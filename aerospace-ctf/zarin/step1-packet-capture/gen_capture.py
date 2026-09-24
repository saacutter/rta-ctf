#!/usr/bin/env python3
"""
STEP 1 of my route  --  builds capture.pcap  (network / Wireshark forensics)

An operator workstation (10.44.7.31) polls an internal telemetry endpoint over
plain HTTP. Instead of standard HTTP Basic auth (which Wireshark auto-decodes for
you -- too easy), the client authenticates with a CUSTOM header:

    X-Aero-Session: <base64( {"u":"<user>","p":"<pass>"} )>

So Wireshark shows the token but doesn't decode it -- the player has to notice
it's a base64 blob, decode it, and read the JSON to get the credential.

Made harder than v1: the two logins are buried in benign background traffic
(other HTTP + DNS), and there are still TWO of them:
  - a DECOY that fails  -> 401
  - the REAL one        -> 200
so you must check which request the server ACCEPTED, not grab the first token.

There is NO flag anywhere in this pcap -- the prize is the credential.

Run:  python3 gen_capture.py   ->   writes capture.pcap
"""
import base64
import json

from scapy.all import (DNS, DNSQR, DNSRR, IP, TCP, UDP, Ether, Raw, wrpcap)

CLIENT_IP = "10.44.7.31"
SERVER_IP = "10.44.0.10"       # telemetry service (the one that wants the token)
DNS_IP = "10.44.0.2"
CLIENT_MAC = "02:42:0a:2c:07:1f"
SERVER_MAC = "02:42:0a:2c:00:0a"
GW_MAC = "02:42:0a:2c:00:02"
HTTP_PORT = 80

REAL_USER, REAL_CODE = "k.reyes", "R3yes!ops2027"
DECOY_USER, DECOY_CODE = "k.reyes", "Summer2026!"

_t = [1_726_900_000.0]     # shared advancing clock so the file is reproducible


def aero_token(user, code):
    """The custom session token: base64 of a small JSON object."""
    return base64.b64encode(
        json.dumps({"u": user, "p": code}, separators=(",", ":")).encode()
    ).decode()


def http_get(path, host, session=None, ua="AeroTelemetryAgent/2.1"):
    lines = [f"GET {path} HTTP/1.1", f"Host: {host}", f"User-Agent: {ua}",
             "Accept: */*"]
    if session:
        lines.insert(3, f"X-Aero-Session: {session}")
    lines += ["Connection: close", "", ""]
    return ("\r\n".join(lines)).encode()


def http_resp(code, reason, body, ctype="application/json"):
    b = body.encode()
    hdr = (f"HTTP/1.1 {code} {reason}\r\nServer: acc-telemetry/1.4\r\n"
           f"Content-Type: {ctype}\r\nContent-Length: {len(b)}\r\n"
           f"Connection: close\r\n\r\n").encode()
    return hdr + b


def conn(dst_ip, dst_mac, sport, cseq0, sseq0, request_bytes, response_bytes):
    """One HTTP request/response TCP connection (handshake + teardown)."""
    ec = Ether(src=CLIENT_MAC, dst=dst_mac); es = Ether(src=dst_mac, dst=CLIENT_MAC)
    ic = IP(src=CLIENT_IP, dst=dst_ip); is_ = IP(src=dst_ip, dst=CLIENT_IP)
    cseq, sseq, pk = cseq0, sseq0, []

    def stamp(p):
        p.time = _t[0]; _t[0] += 0.013; pk.append(p)

    stamp(ec / ic / TCP(sport=sport, dport=HTTP_PORT, flags="S", seq=cseq))
    stamp(es / is_ / TCP(sport=HTTP_PORT, dport=sport, flags="SA", seq=sseq, ack=cseq + 1))
    cseq += 1
    stamp(ec / ic / TCP(sport=sport, dport=HTTP_PORT, flags="A", seq=cseq, ack=sseq + 1))
    sseq += 1
    stamp(ec / ic / TCP(sport=sport, dport=HTTP_PORT, flags="PA", seq=cseq, ack=sseq) / Raw(request_bytes))
    cseq += len(request_bytes)
    stamp(es / is_ / TCP(sport=HTTP_PORT, dport=sport, flags="A", seq=sseq, ack=cseq))
    stamp(es / is_ / TCP(sport=HTTP_PORT, dport=sport, flags="PA", seq=sseq, ack=cseq) / Raw(response_bytes))
    sseq += len(response_bytes)
    stamp(ec / ic / TCP(sport=sport, dport=HTTP_PORT, flags="A", seq=cseq, ack=sseq))
    stamp(es / is_ / TCP(sport=HTTP_PORT, dport=sport, flags="FA", seq=sseq, ack=cseq))
    stamp(ec / ic / TCP(sport=sport, dport=HTTP_PORT, flags="FA", seq=cseq, ack=sseq + 1))
    stamp(es / is_ / TCP(sport=HTTP_PORT, dport=sport, flags="A", seq=sseq + 1, ack=cseq + 1))
    return pk


def dns(qname, sport):
    """A benign DNS query + answer pair (background noise)."""
    ec = Ether(src=CLIENT_MAC, dst=GW_MAC); eg = Ether(src=GW_MAC, dst=CLIENT_MAC)
    q = ec / IP(src=CLIENT_IP, dst=DNS_IP) / UDP(sport=sport, dport=53) / \
        DNS(id=sport & 0xffff, rd=1, qd=DNSQR(qname=qname))
    a = eg / IP(src=DNS_IP, dst=CLIENT_IP) / UDP(sport=53, dport=sport) / \
        DNS(id=sport & 0xffff, qr=1, aa=1, qd=DNSQR(qname=qname),
            an=DNSRR(rrname=qname, ttl=300, rdata="10.44.0.10"))
    q.time = _t[0]; _t[0] += 0.01
    a.time = _t[0]; _t[0] += 0.05
    return [q, a]


def main():
    pkts = []

    # --- background noise: DNS + unauthenticated HTTP to a few hosts ---
    pkts += dns("telemetry.ops.internal.", 51001)
    pkts += conn("10.44.0.20", GW_MAC, 49770, 300000, 700000,
                 http_get("/assets/logo.svg", "portal.ops.internal", ua="Mozilla/5.0"),
                 http_resp(200, "OK", "<svg/>", ctype="image/svg+xml"))
    pkts += conn("10.44.0.20", GW_MAC, 49772, 320000, 720000,
                 http_get("/api/time", "portal.ops.internal", ua="Mozilla/5.0"),
                 http_resp(200, "OK", '{"utc":"2026-09-21T03:40:55Z"}'))

    # --- DECOY poll (bad token) -> 401 ---
    pkts += conn(SERVER_IP, SERVER_MAC, 49788, 100000, 500000,
                 http_get("/telemetry/status", SERVER_IP, aero_token(DECOY_USER, DECOY_CODE)),
                 http_resp(401, "Unauthorized", '{"error":"invalid_session"}'))

    # --- more noise between the two logins ---
    pkts += dns("ntp.ops.internal.", 51002)
    pkts += conn("10.44.0.20", GW_MAC, 49790, 340000, 740000,
                 http_get("/health", "portal.ops.internal", ua="kube-probe/1.29"),
                 http_resp(200, "OK", '{"status":"ok"}'))

    # --- REAL poll (good token) -> 200 (benign telemetry, NO flag) ---
    pkts += conn(SERVER_IP, SERVER_MAC, 49802, 220000, 610000,
                 http_get("/telemetry/status", SERVER_IP, aero_token(REAL_USER, REAL_CODE)),
                 http_resp(200, "OK", '{"segment":"warhead-bus/3","link":"up",'
                          '"coolant_loop_a":"nominal","ts":"2026-09-21T03:41:07Z"}'))

    # --- trailing noise ---
    pkts += conn("10.44.0.20", GW_MAC, 49804, 360000, 760000,
                 http_get("/assets/app.css", "portal.ops.internal", ua="Mozilla/5.0"),
                 http_resp(304, "Not Modified", ""))

    wrpcap("capture.pcap", pkts)
    print(f"[+] wrote capture.pcap  ({len(pkts)} packets, incl. background noise)")
    print(f"[+] real token  : X-Aero-Session for {REAL_USER}:{REAL_CODE}  (-> 200)")
    print(f"[+] decoy token : {DECOY_USER}:{DECOY_CODE}  (-> 401)")

    raw = open("capture.pcap", "rb").read()
    assert b"CITS3006" not in raw, "FLAG LEAKED INTO PCAP -- fix the generator"
    # the creds must NOT appear in cleartext -- only inside the base64 token
    assert REAL_CODE.encode() not in raw, "password in cleartext -- should be base64 in the token"
    print("[+] self-check OK: no flag in pcap, password only inside the base64 token")


if __name__ == "__main__":
    main()
