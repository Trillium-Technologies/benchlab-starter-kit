# Solar Wind Prediction Competition — conformance test.
# Do not modify. Any change is rejected before the build runs.
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl jq \
    && rm -rf /var/lib/apt/lists/*
COPY upload.sh run.sh /app/
RUN chmod +x /app/run.sh /app/upload.sh \
    && useradd --create-home --uid 1000 runner \
    && chown -R runner /app
USER runner
ENTRYPOINT ["/app/run.sh"]
