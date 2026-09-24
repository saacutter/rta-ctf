#!/bin/bash
set -e
service cron start
/usr/sbin/sshd -D
exec su -s /bin/bash www-data -c "python3 /srv/flc/app/app.py"