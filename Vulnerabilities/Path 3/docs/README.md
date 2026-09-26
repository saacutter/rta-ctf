# route, network → horizontal PE → network → RE → vertical PE

My part of the "disarm the warhead" challenge. Three routes to root; all needed to
defuse. This is the **network** route, themed as the AEROSPACE COMMAND grid to match
our shared login look. Runs as **Docker** services.

The design idea: **each step only gives you what the next step needs.** You sniff a
login → it opens a console → the console leaks a config → the config opens the
router → the router gives up a flag **and the firmware** → you reverse the firmware
(Isaac's RE) for an SSH login → you SSH in and escalate to root. Nothing is
skippable, and no step just hands over the final flag.

```
 STEP 1 packet capture   STEP 2 Records Portal      STEP 3 router (network)          STEP 4 RE (Isaac)     STEP 5 controller
 sniff operator login →  log in, IDOR to another  →  telnet in, ${IFS}/$() command →  reverse the       →  SSH as fieldtech,
 from capture.pcap       operator's maintenance      injection: read the flag AND     firmware binary       sudo misconfig (GTFOBins)
 (2 logins, 1 decoy)     snapshot → telnet backdoor  a secret firmware download URL   → SSH credentials     → root → disarm flag
   k.reyes:R3yes!ops2027   support:Falc0n#rtr!22       CITS3006{24n4CBiT2K} + fw        fieldtech:FieldT3ch_2874  CITS3006{xyOTpUwAhd}
```

**Flags (one per challenge, four total):**
- Network (packet capture): `CITS3006{l4A5p3MGYr}` , shown on the portal dashboard
  once you log in with the sniffed credential.
- Horizontal PE (IDOR): `CITS3006{2cXVYDsVXj}` , inside the config record you reach
  via the IDOR (record #48879).
- Web injection (router): `CITS3006{24n4CBiT2K}` , read out of the router via the
  command injection.
- Vertical PE (root): `CITS3006{xyOTpUwAhd}` , the final disarm flag at `/home/fieldtech/disarm-authorization.txt`.

All four are independent random values; none reveals the next stage, and stage
progression is driven by the loot (credentials, firmware), not the flags. Isaac's RE
box in the middle carries its own flag (his stage).

They're different so the router stage can't leak the final flag, you must go through
Isaac's RE and my privesc box to finish. (Rotate via the `FLAG` build args.)

**How Isaac's RE is wired in:** solving my router injection reveals a secret URL to
download the router's "firmware", which is actually Isaac's RE binary. Reversing it
yields the SSH login for my final box. So the order is locked: my telnet → Isaac's RE
→ my privesc. The firmware is served only at that secret path (no listing, everything
else 404s), so you can't grab it without solving the injection.

**Route entry:** the player lands on a **briefing page** (`/`) that frames the mission
and hands over the packet capture **and recon notes** as downloads, then a button into
the portal login. That's what the shared hub's "Network" team tile should link to.

## What makes each step non-trivial

- **Step 1**, creds ride in a **custom `X-Aero-Session` header** (base64 of a JSON
  object), not Basic auth, so Wireshark doesn't decode it. Two tokens buried in
  benign traffic (DNS + HTTP); one is a decoy (401). A recon notes file
  (`intercept-notes.txt`) ships with the pcap to point players at the header without
  spoiling the decode. No flag in the pcap.
- **Step 2**, horizontal PE via IDOR. The URL ref is the record number's text
  **hex-encoded** (obfuscation, not authz), and a portal note only says the ref
  "encodes the record number" (it does not name hex). The player decodes one of
  their own, then has to enumerate to a record that isn't theirs to find the
  breadcrumb, which names the far-off config record #48879. So the IDOR itself is
  the discovery step, not something handed to them in their own record.
- **Step 3**, the `ping` command injection is filtered (space/`;`/`|`/`&`/`` ` ``
  /quotes), so you need the `${IFS}` + `$(...)` bypass. The MOTD points at
  `/opt/maint/rtr-01.snapshot`, which holds the flag AND the firmware URL joined in
  one token, so a single read via the injection hands the player both (they can't
  grab the flag and miss the firmware).
- **Step 4 (Isaac's)**, anti-debug (`ptrace`) bypassed with `LD_PRELOAD`, then a
  hash gate patched in memory; reveals the SSH login.
- **Step 5**, a **NOPASSWD sudo rule** lets `fieldtech` run `find` as root;
  `find -exec` spawns a root shell (GTFOBins) → `/home/fieldtech/disarm-authorization.txt`. Distinct from Isaac's
  PATH hijack and Senaya's tar-wildcard.

## Hints, not spoilers

- `docs/PLAYER-BRIEF.md`, scenario + objective per stage, nudges only.
- `docs/HINTS.md`, tiered hints (nudge → more → technique), reveal one at a time.
- `docs/SOLUTION.md`, full step-by-step (markers / last resort).
- In-world hints are baked into the challenge itself (recon notes, breadcrumb record,
  console note, router MOTD), so a player gets guidance from the boxes alone, the
  docs above are the extra layer we also hand out.

## Files

```
step1-packet-capture/
  capture.pcap          <- GIVE TO PLAYERS. sniffed traffic (with noise).
  intercept-notes.txt   <- GIVE TO PLAYERS with the pcap. recon nudge (stage-1 clue).
  gen_capture.py        regenerates capture.pcap (scapy). self-checks no flag leaks in.
  telemetry_service.py  OPTIONAL live endpoint (only if we want live tcpdump capture).

step2-operator-console/
  app.py                the console (IDOR). Also serves the briefing page + pcap +
                        intercept-notes downloads.
  requirements.txt      Flask 3.1.3 / Werkzeug 3.1.8
  Dockerfile            (build from the zarin-route root so ../shared is in context)

step3-warhead-router/
  telnet_server.py      router console. injectable ping. flag + fw URL in /opt/maint.
  fw_server.py          OTA firmware endpoint, serves Isaac's binary at a secret path.
  fw/acc-rtr01-fw.elf   Isaac's RE binary (the "firmware"). rotate if he rebuilds.
  entrypoint.sh         stages /opt/maint artefacts, starts telnet + firmware servers
  Dockerfile

step4-vertical-privesc/
  motd, Dockerfile      creates fieldtech, NOPASSWD sudo on find, sshd, /home/fieldtech/disarm-authorization.txt root-only
  entrypoint.sh         writes /home/fieldtech/disarm-authorization.txt from FLAG, runs sshd
  SOLUTION-vertical.md  the privesc walkthrough (sudo misconfig + GTFOBins)

shared/aerospace.py     the AEROSPACE COMMAND theme (login card + jet backdrop)
docker-compose.yml      run all live services (primary way to run it)
deploy/                 systemd units + vm-install.sh (telnet stage only; Docker for full chain)
verify_chain.py         runs the chain locally and asserts it solves + no flag in pcap
solve.py                reference exploit vs the live services (demo backup)
docs/                   PLAYER-BRIEF, HINTS, SOLUTION, DEMO-SCRIPT, WALKTHROUGH, this README
```

## Run it (Docker, the agreed way)

```bash
docker compose up --build
# Operations Records Portal : http://localhost:8090/
# router telnet             : telnet localhost 23
# firmware endpoint         : http://localhost:8081/ (secret path from the injection)
# vertical-PE box           : ssh fieldtech@localhost -p 2022  (creds from Isaac's RE)
# hand players              : step1-packet-capture/capture.pcap + intercept-notes.txt
```

Prove the network half works with no Docker at all:
```bash
pip install scapy flask --break-system-packages
python3 verify_chain.py            # walks steps 1-3, prints the flag
```

## Rotating things

- **Flags:** router flag and root flag are `FLAG` build args in `docker-compose.yml`
  (step-3 / step-4). The network and horizontal flags live in the step-2 console
  (`NETWORK_FLAG` / `HORIZONTAL_FLAG` env vars, defaults in `app.py`). Rebuild after
  changing any.
- **Firmware / SSH creds:** if Isaac rebuilds his binary, drop the new ELF at
  `step3-warhead-router/fw/acc-rtr01-fw.elf`, and if he changed the login, update
  `LOWUSER`/`LOWPASS` in the step-4 Dockerfile to match. Rotate the download token
  via `FW_TOKEN` in the step-3 Dockerfile.
- **Telnet password:** if you change it, re-scramble and update
  `mgmt.telnet.pass_enc` in step 2's export (`app.py`):
  ```bash
  python3 -c "import base64;print(base64.b64encode(bytes(b^0x5A for b in b'NEWPASS')).decode())"
  ```

## Hook onto the shared SQLi
Everyone branches from the shared SQL injection. My route just needs the
`capture.pcap` (+ `intercept-notes.txt`) handed to the player when they reach my
branch, then it's self-contained through to root.
