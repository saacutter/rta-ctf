#!/bin/bash

service cron start
/usr/sbin/sshd
su -s /bin/bash www-data -c "python3 /srv/flc/app/app.py" 2>&1 |
    sed -u 's|.*Running on http://127\.0\.0\.1:5000.*|FLC internal service started (container access only).|' &
cd /app || exit 1
# Print the browser URL after both web apps have finished starting.
python3 - <<'PY' &
import socket
import time

deadline = time.monotonic() + 60
while time.monotonic() < deadline:
    try:
        for port in (5000, 5005):
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                pass
    except OSError:
        time.sleep(0.5)
    else:
        print("\nMain website - copy this URL into your browser:", flush=True)
        print("http://127.0.0.1:5005/\n", flush=True)
        break
else:
    print("Web app startup timed out. Check the logs above for errors.", flush=True)
PY
exec python3 app.py
