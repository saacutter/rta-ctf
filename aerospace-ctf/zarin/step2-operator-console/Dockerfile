# Step 2 build/test image (operator console / horizontal-PE IDOR).
# NOTE: build this from the zarin-route ROOT so ../shared is in the context:
#   docker build -f step2-operator-console/Dockerfile -t acc-console .
FROM python:3.11-slim
WORKDIR /app
COPY step2-operator-console/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY step2-operator-console/app.py /app/app.py
COPY shared /shared
# the briefing page hands out the capture + recon notes -> bundle them in
COPY step1-packet-capture/capture.pcap /app/capture.pcap
COPY step1-packet-capture/intercept-notes.txt /app/intercept-notes.txt
# app.py imports "../shared"; from /app that resolves to /shared
ENV PORT=8090
EXPOSE 8090
CMD ["python3", "/app/app.py"]
