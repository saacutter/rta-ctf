#!/bin/sh
# Refresh the flag from the env (so it can be rotated at run time) and start sshd.
set -e
: "${FLAG:=CITS3006{xyOTpUwAhd}}"
echo "$FLAG" > /root/flag
chmod 600 /root/flag
chown root:root /root/flag
exec /usr/sbin/sshd -D -e
