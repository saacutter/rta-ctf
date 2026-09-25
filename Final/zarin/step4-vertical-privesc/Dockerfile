# Step 4, vertical privilege escalation (sudo misconfiguration + GTFOBins).
# The last box in my column: you arrive as a low-priv user and escalate to root
# to read the final flag. (Distinct from Isaac's PATH-hijack VPE and Senaya's
# tar-wildcard VPE: this one is a NOPASSWD sudo rule on a binary that can be
# turned into a root shell via GTFOBins.)
FROM debian:12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends sudo openssh-server findutils \
 && rm -rf /var/lib/apt/lists/*

# The low-privilege user. IN THE FULL CHAIN, Isaac's RE reveals THIS credential;
# the player SSHes in as this user, then escalates. The password must ONLY come
# from Isaac's stage (not guessable) so players can't skip him.
# Creds (given to Isaac):  fieldtech / FieldT3ch_2874
ARG LOWUSER=fieldtech
ARG LOWPASS=FieldT3ch_2874
RUN useradd -m -s /bin/bash ${LOWUSER} && echo "${LOWUSER}:${LOWPASS}" | chpasswd

# THE MISCONFIG: the field-maintenance account was granted passwordless sudo to
# run `find` as root (meant for filesystem integrity scans). find can spawn a
# shell via -exec, so this NOPASSWD rule is a full root escalation (GTFOBins).
RUN echo "${LOWUSER} ALL=(root) NOPASSWD: /usr/bin/find" > /etc/sudoers.d/acc-maint \
 && chmod 440 /etc/sudoers.d/acc-maint \
 && visudo -cf /etc/sudoers.d/acc-maint

# final flag (root only), the column's disarm flag. rotate via FLAG build arg.
ARG FLAG="CITS3006{xyOTpUwAhd}"
ENV FLAG=${FLAG}
RUN echo "$FLAG" > /root/flag && chmod 600 /root/flag && chown root:root /root/flag

COPY motd /etc/motd

RUN mkdir -p /run/sshd && ssh-keygen -A \
 && sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config \
 && printf '\nPrintMotd yes\n' >> /etc/ssh/sshd_config

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 22
CMD ["/entrypoint.sh"]
