# ==============================================================
# Solar Wind Prediction Competition — submission template
#
# The platform runs:  <ENTRYPOINT> <INFERENCE_TIMESTAMP>
# e.g.                /app/run.sh 20261111T060000Z
#
# Replace everything between the EDIT markers, including the
# language and runtime. Keep the ENTRYPOINT contract.
# ==============================================================
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# ---- PLATFORM LAYER — needed for the upload helper -----------
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl jq \
    && rm -rf /var/lib/apt/lists/*
COPY upload.sh /app/upload.sh
# -------------------------------------------------------------

# ================= EDIT BELOW =================================
# Install any runtime you like. Python is only an example —
# R, Julia, Go, a compiled binary are all fine.

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY model.py .
# COPY weights/ ./weights/

# ================= EDIT ABOVE =================================

COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh /app/upload.sh \
    && useradd --create-home --uid 1000 runner \
    && chown -R runner /app
USER runner

ENTRYPOINT ["/app/run.sh"]
