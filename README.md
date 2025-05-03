# ai-remote-dev-base
This repository sets up a barebones Docker container with Ollama and Open-WebUI for AI development on an nvidia GPU machine via remote-SSH.

Installs following packages:
uv
ollama
open-webui

Then runs OpenWebUi + Ollama in the background at their default ports.

## Setup via quickpod.io
To run this on a pod provisioned via quickpod.io, create a template with the following settings:

**Launch Mode**: ```Docker Entrypoint```

**Docker Image Path**: ```surajarogyalabs/ai-remote-dev-base:latest```

**Docker Options**
```bash
-gpus all -p 22:22 -p 8080:8080 -p 11434:11434 -v "$(pwd)":/home/dev/app --add-host=host.docker.internal:host-gateway -e SSH_PUB_KEY="<PUB_SSH_KEY>"
```