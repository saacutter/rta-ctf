#!/bin/bash

service cron start
/usr/sbin/sshd
cd /app && python3 app.py