# Team Charlie (branch 3) 


## What changed in the shared app
- `templates/dashboard.html`: the TEAM CHARLIE "ENTER TEAM" button now points at
  this route's entry. It sends the player to `http://<same-host>:8090/` (built
  from the current hostname in JS, so it works whatever the VM's IP is).
  Nothing else in the shared app was touched.

## How to run everything on the shared VM
1. Shared entry app (SQLi -> dashboard), as before:
     cd aerospace-ctf            # the shared Flask app
     source venv/bin/activate
     python app.py               # serves the portal + dashboard
2. This network route (Team Charlie), in a second terminal:
     cd zarin-route
     docker compose up --build
   That brings up:
     - operator console + briefing : http://<vm-ip>:8090/   (Charlie tile lands here)
     - router telnet               : telnet <vm-ip> 23
     - firmware endpoint           : http://<vm-ip>:8081/   (secret path, from the injection)
     - vertical-PE box             : ssh fieldtech@<vm-ip> -p 2022
3. Players who reach Team Charlie get the pcap + intercept-notes.txt from the
   briefing page at :8090.

## The chain (Team Charlie)
pcap (Wireshark) -> operator portal IDOR (horizontal PE) -> router telnet
(command injection) -> reverse the firmware (Isaac's RE) -> SSH + sudo-misconfig
privesc -> root. Four flags on my side (network, horizontal, router, root); see
docs/SOLUTION.md and docs/PLAYER-BRIEF.md.

## For Isaac (RE handoff on this branch)
Isaac's reverse-engineering binary is already wired in as the router "firmware":
`zarin-route/step3-warhead-router/fw/acc-rtr01-fw.elf` is Isaac's compiled `rand`.
Solving the router injection reveals a secret URL to download it; reversing it
yields the SSH login `fieldtech / FieldT3ch_2874`, which is how you reach my final
box. If Isaac rebuilds his binary, drop the new ELF at that path (and if he changes
the login, update LOWUSER/LOWPASS in step4-vertical-privesc/Dockerfile to match).
His RE stage flag is his own; my four flags are listed in docs/SOLUTION.md.

## Note on ports
Shared app = 5005 (compose) / 5000 (older notes). This route = 8090 (web), 23
(telnet), 8081 (firmware), 2022 (ssh). No port clashes with the shared app.
