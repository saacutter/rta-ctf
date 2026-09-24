#!/usr/bin/env python3
"""
STEP 1 (optional live variant) -- the internal telemetry endpoint that the
operator polls. You only need this if the team wants players to CAPTURE the
traffic live (tcpdump) instead of handing them the ready-made capture.pcap.

It authenticates with a custom X-Aero-Session token (base64 of a small JSON
object) and returns only a boring JSON status. There is no flag here -- the point
of step 1 is the credential, not a flag. Run it over plain HTTP so the token is
visible on the wire.

Run:  sudo python3 telemetry_service.py   (port 80)   or   PORT=8088 python3 ...
Capture:  sudo tcpdump -i <iface> tcp port 80 -w capture.pcap
"""
import base64
import json
import os

from flask import Flask, Response, request

app = Flask(__name__)

VALID = {"k.reyes": "R3yes!ops2027"}  # same credential recoverable from the pcap


def check(tok):
    if not tok:
        return False
    try:
        d = json.loads(base64.b64decode(tok))
    except Exception:
        return False
    return VALID.get(d.get("u")) == d.get("p")


@app.route("/telemetry/status")
def status():
    if not check(request.headers.get("X-Aero-Session")):
        return Response('{"error":"invalid_session"}', status=401,
                        mimetype="application/json")
    return Response('{"segment":"warhead-bus/3","link":"up",'
                    '"coolant_loop_a":"nominal"}',
                    mimetype="application/json")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "80")))
