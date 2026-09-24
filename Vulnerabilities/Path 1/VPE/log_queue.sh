#!/bin/sh

# This script logs the jobs added to the `/var/queue` folder once every minute
# by sending the names of the jobs to `/var/log/jobs.log`.
# This operation is run by `cron` once every minute.

ls /var/job_queue >> /var/log/jobs.log