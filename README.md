# ai-remote-dev-base
This repository sets up a barebones Docker container with Ollama and Open-WebUI for AI development on an nvidia GPU machine via remote-SSH.

* Installs following packages at docker setup:
  * [uv](https://github.com/astral-sh/uv)
  * [ollama](https://ollama.com/)
* Start services selectively with `/home/dev/app/run.sh`
  * Use command line arguments to start only the services you need
  * Installs [open-webui](https://github.com/open-webui/open-webui) via uv when requested

## Usage

Start services using command line arguments:

```bash
# Start only Ollama
./run.sh --ollama

# Start only Open WebUI
./run.sh --openwebui

# Start both services
./run.sh --ollama --openwebui

# Show help and usage information
./run.sh --help
```

**Default Ports:**
- Ollama: `11434`
- Open WebUI: `8080`



## Setup via quickpod.io
To run this on a pod provisioned via quickpod.io, create a template with the following settings:

**Launch Mode**: ```Docker Entrypoint```

**Docker Image Path**: ```surajarogyalabs/ai-remote-dev-base:latest```

**Docker Options**
```bash
-gpus all -p 22:22 -p 8080:8080 -p 11434:11434 -v "$(pwd)":/home/dev/app --add-host=host.docker.internal:host-gateway -e SSH_PUB_KEY="<PUB_SSH_KEY>"
```