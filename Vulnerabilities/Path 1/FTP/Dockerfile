# Use the latest LTS Ubuntu image as the base
FROM ubuntu:26.04
ENV DEBIAN_FRONTEND=noninteractive

# Install any necessary packages
RUN apt update && apt install sudo -y
RUN apt install openssh-server -y

# Create a non-privileged user
RUN groupadd -g 10000 nonprivileged && useradd -m -r -u 10000 -g nonprivileged user

# Copy the SSH public key to the unprivileged user's SSH directory
RUN mkdir -p /home/user/.ssh && chown user:nonprivileged /home/user/.ssh && chmod 700 /home/user/.ssh
COPY --chown=user:nonprivileged public_key.pub /home/user/.ssh/authorized_keys

# Expose the SSH port
EXPOSE 22

# Start the SSH server
CMD ["/usr/sbin/sshd", "-D"]