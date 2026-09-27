# Separate FTP challenge

Run commands below from `Final` on the Windows Docker host unless marked Kali.
The web service publishes TCP 5005 and the FTP service publishes TCP 2121 plus
TCP 30000-30009 for passive data transfers. Both use the Windows host's IP;
players do not need either container's internal IP. Other challenge services,
including web port 5006 and SSH, keep their existing configuration.

## Build and start (PowerShell)

Find the Windows address reachable from Kali with `ipconfig`. Use that address
below, not a Docker bridge address, localhost, or the Kali address.

```powershell
Set-Location 'C:\Users\dulwa\OneDrive - UWA\Desktop\CITS3006 Project\cits3006-project\Final'
$env:FTP_PUBLIC_HOST = '192.168.1.100' # Replace with the Windows host IP.
docker compose config --quiet
docker compose build aerospace-web aerospace-ftp
# Recreate web first so the old combined container releases the FTP ports.
docker compose up -d --no-deps --force-recreate aerospace-web
docker compose up -d --no-deps --force-recreate aerospace-ftp
# Start any other project services that are not already running.
docker compose up -d --build
docker compose ps
```

For subsequent sessions, set `FTP_PUBLIC_HOST=<Windows-host-IP>` in the existing
`Final/.env` file. Do not overwrite its other settings. Recreate FTP when this
address changes. EPSV uses the control connection's host address; traditional
PASV uses `FTP_PUBLIC_HOST`. The passive ports must also be reachable from Kali
through Windows Firewall and the VM network. They listen only during transfers,
so an idle port scan need not show them open.

## Verify from Kali

Replace the example address with the same Windows host IP:

```bash
HOST_IP=192.168.1.100
nmap -sT -sV -p 5005,2121 "$HOST_IP"
curl --fail --max-time 10 -I "http://$HOST_IP:5005/"
# Verbose output includes the anonymous login response (230).
curl --fail --max-time 15 -v --user 'anonymous:lab@example.com' \
  --list-only "ftp://$HOST_IP:2121/"
curl --fail --max-time 15 --user 'anonymous:lab@example.com' \
  "ftp://$HOST_IP:2121/research_notes.txt"
# Force traditional PASV and honor its advertised address to test configuration.
curl --fail --max-time 15 --disable-epsv --no-ftp-skip-pasv-ip \
  --user 'anonymous:lab@example.com' \
  "ftp://$HOST_IP:2121/research_notes.txt"
```

The notes and their existing flag should be returned. Anonymous access remains
read-only, with the same banner and filenames.

## Verify filesystem isolation on the Docker host

A remote port scan cannot prove filesystem absence. Use Docker administration
on Windows for this check; ordinary Kali access does not include Docker access.

```powershell
docker compose exec -T aerospace-web python -c "from pathlib import Path; paths = ['/app/ftp_share', '/app/ftp_server.py', '/app/ftp', '/ftp']; assert not any(Path(p).exists() for p in paths), 'FTP files leaked into web'; print('PASS: FTP paths absent from web')"
docker compose exec -T aerospace-web find / -xdev -name research_notes.txt
docker inspect aerospace-web --format '{{json .Mounts}}'
docker compose exec -T aerospace-ftp ls -l /app/ftp_share
```

The `find` command should print nothing. The web mount list should contain only
the existing database mount, with no FTP share, parent repository directory, or
Docker socket. The FTP listing should show `research_notes.txt`.

If Kali already has authorized SSH access to the **Windows host** and Docker
permission there, the equivalent remote filesystem checks are:

```bash
ssh WINDOWS_USER@"$HOST_IP" 'docker exec aerospace-web test ! -e /app/ftp_share'
ssh WINDOWS_USER@"$HOST_IP" 'docker exec aerospace-web find / -xdev -name research_notes.txt'
ssh WINDOWS_USER@"$HOST_IP" 'docker inspect aerospace-web --format "{{json .Mounts}}"'
```

These require host administration. The lab's published SSH port 22 belongs to
the web container, not automatically to Windows; use the actual host SSH port
with `ssh -p` if configured. No host SSH setup is required to play the lab.

## Isolation details

`ftp/` is a dedicated build context. Only its image copies `ftp_share/`, and no
FTP volume is mounted into web. `Final/.dockerignore` excludes `ftp/` and the old
`app/ftp_share/` and `app/ftp_server.py` paths from the main build context, so the
web Dockerfile's `COPY app/ .` cannot include them, even in an image layer.
Flask no longer starts an FTP thread, and its requirements no longer install
pyftpdlib. The existing web entrypoint still starts its original web, cron, and
SSH services. FTP starts independently through its own Dockerfile command.
The web Dockerfile normalizes entrypoint line endings so Windows checkouts
produce a runnable Linux startup script.

Source files remain in the host checkout for building the FTP image. Among the
running lab containers, only FTP contains them. Changes to those files require
rebuilding and recreating FTP. A player in web may still connect over the network
to anonymous FTP, which is the intended challenge interface.
