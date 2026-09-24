# Use the latest LTS Ubuntu image as the base
FROM ubuntu:26.04
ENV DEBIAN_FRONTEND=noninteractive

# Install any necessary packages
RUN apt update && apt install sudo -y
RUN apt install openssh-server -y
RUN apt install cron -y
RUN apt install zip -y

# Create a non-privileged user
RUN groupadd -g 10000 nonprivileged && useradd -m -r -u 10000 -g nonprivileged user
RUN chmod 777 /home/user

# Copy the scripts for the cronjob
RUN mkdir -p /usr/local/sbin && mkdir -p /var/log/jobs && mkdir -p /var/job_queue/
COPY --chown=root:root archive_queue.sh /usr/local/sbin/archive_queue
COPY --chown=root:root log_queue.sh /usr/local/sbin/log_queue
RUN chmod 755 /usr/local/sbin/archive_queue /usr/local/sbin/log_queue

# Copy the cron script and start the cronjob
COPY --chown=root:root crontab /etc/cron.d/archive_jobs
RUN chmod 0644 /etc/cron.d/archive_jobs

# Copy the create_job binary to the system
COPY --chown=root:root create_job /home/user/create_job
RUN chmod 6711 /home/user/create_job

CMD service cron start && su - user