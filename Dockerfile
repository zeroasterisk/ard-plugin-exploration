# Containerized OpenCode Environment with ARD Discovery Plugin
FROM ghcr.io/anomalyco/opencode:latest

# Install python3 and git for ARD resolver scripts and local repositories
USER root
RUN apk add --no-cache python3 git curl bash

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
