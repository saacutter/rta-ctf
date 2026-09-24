#!/bin/bash

service cron start
/usr/sbin/sshd
su -s /bin/bash www-data -c "python3 /srv/flc/app/app.py" &
cd /app && python3 app.py
