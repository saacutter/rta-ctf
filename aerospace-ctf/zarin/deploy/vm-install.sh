#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# One-shot installer for MY route inside the shared team VM (Debian/Ubuntu/Kali).
# Run as root:   sudo ./vm-install.sh
#
# It installs step 2 (operator console, tcp/8090) and step 3 (router telnet,
# tcp/23) as systemd services. Step 1 is just the capture.pcap file that gets
# handed to players -- there's nothing to install for it (the optional live
# telemetry service is only if the team wants live capture).
# ---------------------------------------------------------------------------
set -euo pipefail

SRC="$(cd "$(dirname "$0")/.." && pwd)"     # zarin-route/
DEST="/opt/acc-route"

echo "[*] installing python + flask..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip iputils-ping >/dev/null
pip3 install --quiet --break-system-packages "Flask==3.1.3" "Werkzeug==3.1.8" || \
  pip3 install --quiet "Flask==3.1.3" "Werkzeug==3.1.8"

echo "[*] creating service user 'acc'..."
id acc >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin acc

echo "[*] copying route to $DEST ..."
mkdir -p "$DEST"
cp -r "$SRC/step2-operator-console" "$SRC/step3-warhead-router" "$SRC/shared" "$DEST/"
chown -R acc:acc "$DEST/step2-operator-console" "$DEST/shared"

echo "[*] installing systemd services..."
cp "$SRC/deploy/acc-console.service" /etc/systemd/system/
cp "$SRC/deploy/acc-router.service"  /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now acc-console.service
systemctl enable --now acc-router.service

echo
echo "[+] done. services:"
systemctl --no-pager --lines=0 status acc-console.service acc-router.service || true
echo
echo "    operator console : http://<vm-ip>:8090/   (step 2)"
echo "    router telnet    : telnet <vm-ip> 23       (step 3)"
echo "    give players      : step1-packet-capture/capture.pcap"
echo
echo "[i] to rotate the flag: edit FLAG in /etc/systemd/system/acc-router.service"
echo "    then: systemctl daemon-reload && systemctl restart acc-router"
