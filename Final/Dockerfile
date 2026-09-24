# Use the Python 3.12 slim image
FROM python:3.12-slim

# Install the necessary packages
RUN apt update && \
    apt install -y --no-install-recommends \
        cron \
        util-linux \
        openssh-server \
        zip && \
    rm -rf /var/lib/apt/lists/*

# Start the web application
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
EXPOSE 5005

# Start the SSH service
RUN groupadd -g 10000 test && useradd -m -r -u 10000 -g test testuser
RUN mkdir -p /home/testuser/.ssh && chown testuser:test /home/testuser/.ssh && chmod 700 /home/testuser/.ssh
COPY --chown=testuser:test files/public_key.pub /home/testuser/.ssh/authorized_keys
EXPOSE 22

# Copy the entrypoint script to the machine
COPY entrypoint.sh /usr/local/bin/entrypoint
RUN chmod 700 /usr/local/bin/entrypoint
RUN chown root:root /usr/local/bin/entrypoint

CMD ["/usr/local/bin/entrypoint"]