# Containerized OpenCode Environment with ARD Discovery Plugin & gcloud CLI
FROM ghcr.io/anomalyco/opencode:latest

# Install python3, git, tar, curl, bash and extract google-cloud-sdk
USER root
RUN apk add --no-cache python3 git curl bash tar && \
    curl -sSL https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz | tar -xz -C /usr/local && \
    ln -sf /usr/local/google-cloud-sdk/bin/gcloud /usr/bin/gcloud && \
    ln -sf /usr/local/google-cloud-sdk/bin/bq /usr/bin/bq

ENV CLOUDSDK_PYTHON=/usr/bin/python3
ENV PATH="/usr/local/google-cloud-sdk/bin:${PATH}"

# Set up working workspace directory
WORKDIR /workspace

# Copy the ARD plugin exploration repo into the container
COPY . /workspace/ard-plugin-exploration

# Configure OpenCode global config directory and plugin location
ENV ARD_CONFIG_DIR=/workspace/.config/ard
ENV XDG_CONFIG_HOME=/workspace/.config

# Default entrypoint is opencode
ENTRYPOINT ["opencode"]
CMD ["--help"]
