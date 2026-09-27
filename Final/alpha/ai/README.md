# ARIA support portal (Path 1, AI prompt-injection challenge)

A self-contained web chatbot challenge. Access is gated by a passcode. The bot
looks like a bland support assistant, but it guards a stage flag and the login for
the next box in Path 1. It is deliberately multi-step: a single prompt injection is
not enough (see "How the challenge works" below).

## Run it standalone (to test)
```
docker compose -f docker-compose.snippet.yml up --build
# open http://localhost:8095/
```
Or without Docker:
```
pip install -r requirements.txt
python app.py            # serves on :8095
```

## Files
| file | what it is |
|------|------------|
| `app.py` | the whole app: passcode gate, chat UI, and the rule-based bot |
| `requirements.txt` | Flask |
| `Dockerfile` | container build (exposes 8095) |
| `docker-compose.snippet.yml` | drop-in service for Path 1's compose |
| `SOLUTION-ai.md` | the three gates + exact working prompts, flag, and creds |
| `HINTS-ai.md` | tiered player hints (one nudge per gate) |

## How the challenge works
The player has to clear three gates, in any order they can work out:

1. **Pretext (social engineering).** ARIA only opens up to someone it believes is
   on-call / authorised maintenance staff. A general visitor gets nothing.
2. **Input filter (bypass).** The textbook jailbreak lines (`ignore your
   instructions`, `print your system prompt`, `developer mode`, ...) are screened and
   rejected. The player has to reword the same override/reveal intent.
3. **Two-step maintenance mode.** Clearing 1 + 2 opens "maintenance mode" but releases
   nothing on its own. The player then enumerates the service accounts ARIA manages
   and requests the specific one, which releases the credential and the flag together.

Full walkthrough and exact prompts are in `SOLUTION-ai.md`; tiered hints in `HINTS-ai.md`.

## The values (override via env)
| env var | default | meaning |
|---------|---------|---------|
| `ARIA_PASSCODE` | `ADRJ-6UDP-BRHD` | access passcode (from earlier in Path 1) |
| `ARIA_FLAG` | `CITS3006{LFJkvM1LVy}` | this stage's flag |
| `ARIA_NEXT_USER` | `sysmaint` | leaked username for the next box |
| `ARIA_NEXT_PASS` | `ytEfgh2aCLTT` | leaked password for the next box |

## Integrating into Path 1
1. Copy this folder into the Path 1 project.
2. Paste the service from `docker-compose.snippet.yml` into Path 1's
   `docker-compose.yml` (keep port `8095` free, or remap it).
3. Wire a link/button to it from wherever the player lands after getting the
   passcode.

## Handoff to the vertical-PE box (do not skip)
This challenge leaks `sysmaint` / `ytEfgh2aCLTT`.

## Note on the "AI"
The bot is deterministic and rule-based, not a real language model, which keeps it
offline, reproducible, and gradeable. The moves that beat it are the same ideas that
work on real models: establishing a false context, evading an input filter by
rewording, and treating an over-trusting assistant as a queryable system. The obvious
one-line jailbreaks are deliberately filtered so it can't be one-shotted.
