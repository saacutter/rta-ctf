# Tiered hints, network route

Reveal one at a time, and give the earlier ones a real try before opening the next.
These are meant to point your thinking in the right direction, not to hand you the
step. Some stages only need one hint; if a stage isn't listed with a third hint, it
didn't need one.

---

## Stage 1, the packet capture

1. The login isn't where you'd look for a normal one. It's not Basic auth, so your
   analyser won't break it out for you; the operator's client is carrying its
   identity in a header it added itself. (The recon notes name it.)
2. The value looks like one meaningless blob because it was encoded, not encrypted.
   What's the most common, fully reversible way to pack readable text into a blob
   like that? Try it on the session the server accepted, not the one it refused.

## Stage 2, the records portal

1. Your record references aren't random, and the portal told you they encode the
   record number. If you could turn one of yours back into its number, what would
   that let you reach that was never listed for you?
2. Decode one of your own references and set it next to your record number; the
   relationship is a single, common encoding. Once you see it, you can address
   records that were never meant to be on your list. Read what your neighbours are
   holding.
3. The encoding is plain hex: a reference is just the record number's digits,
   hex-encoded. In CyberChef, run a reference through From Hex to turn it back into
   a number, and To Hex to build the reference for any number you want. Decode one of
   yours to confirm, then use it to open records that aren't yours. One of those
   neighbouring records points you at the exact record where the router's settings
   are filed; open that one.

## Stage 3, the router console

1. Only one command takes free input. See what happens if you try to make it do more
   than ping, and read the message it gives back.
2. It really does reach a shell, but a handful of characters are filtered. You don't
   actually need any of the blocked characters to put a space between words or to run
   a second command; the shell has other ways to express both.
3. `${IFS}` stands in for whitespace and `$(...)` runs a command. Look through
   `/opt/maint` and read what's there; ping echoes back anything it can't resolve, so
   that's how the output comes home.

## Stage 4, the firmware (the reverse-engineering challenge)

1. It's a compiled binary that doesn't want to run under a debugger. Work out what
   it's checking for and why it bails.
2. That check is one call you can neutralise from outside the program; past it, the
   thing it's guarding is decided by a comparison you can influence rather than guess.
   (This is the shared RE box; its own notes go deeper.) What it finally prints is a
   login you'll need next.

## Stage 5, the controller

1. You're not root, but this account was set up for maintenance. What is it actually
   allowed to do with elevated rights? There's a standard first thing to check.
2. `sudo -l` lists what you may run as root. You're cleared to run one specific tool
   as root, no password. The catch is what that tool can be made to do beyond its
   obvious job.
3. The tool can run another program of your choosing (think about GTFOBins). If it
   launches a command while running as root, that command is root too.

---

If a stage still won't budge after its hints, the exact commands are in `SOLUTION.md`
(keep that for markers or a last resort).
