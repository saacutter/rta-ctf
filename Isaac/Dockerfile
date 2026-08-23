# Use the latest LTS Ubuntu image as the base
FROM ubuntu:26.04

# Install any necessary packages
RUN apt update && apt install sudo -y

# Create a non-privileged user
RUN groupadd -g 10000 nonprivileged && useradd -r -u 10000 -g nonprivileged user

# Copy reverse engineering binary to container
COPY Draft/RE/re /home/user/re
RUN chmod +x /home/user/re

# Launch the container as the non-privileged user
USER user
WORKDIR /home/user