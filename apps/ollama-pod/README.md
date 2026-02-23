# ollama-pod

Deploy and manage [Ollama](https://ollama.com) on [RunPod](https://www.runpod.io) GPU cloud with a single command.

## What it does

- Provisions a RunPod pod with a GPU sized for your model
- Automatically picks the cheapest available GPU that fits
- Pulls the model and exposes the Ollama HTTP API
- Tracks active pod state locally for easy teardown

## Install

From the project directory:

```bash
uv tool install .
```

Or with an absolute path:

```bash
uv tool install /path/to/apps/ollama-pod
```

### Update

```bash
uv tool install --reinstall .
```

### Uninstall

```bash
uv tool uninstall ollama-pod
```

## Configuration

Create `~/.ollama-pod/.env` with your RunPod API key:

```bash
mkdir -p ~/.ollama-pod
echo "RUNPOD_API_KEY=<your-key>" > ~/.ollama-pod/.env
```

A `.env` in the current directory is also loaded as a fallback.

## Usage

### Spin up a pod

```bash
ollama-pod up <model>
```

Example:

```bash
ollama-pod up qwen2.5:7b
```

Options:

| Flag | Description |
|------|-------------|
| `--name` | Name for this pod, used for multi-pod tracking (default: `default`) |
| `--vram` | Override the auto-estimated VRAM (GB) |
| `--gpu-type` | Use a specific GPU type ID instead of auto-selecting |
| `--volume-id` | Attach a network volume (caches models across runs) |
| `--cloud-type` | Cloud type: `any`, `community`, or `secure` (default: `any`) |
| `--image` | Docker image override (default: `surajarogyalabs/kenai-ollama:latest`) |
| `--dry-run` | Show GPU and cost without creating a pod |

### Check status

```bash
ollama-pod status
```

Shows pod ID, model, endpoint URL, GPU type, cost/hr, and runtime status.

Use `--name <name>` to check a specific pod.

### Tear down

```bash
ollama-pod down
```

Terminates the pod. If a network volume was used, it's preserved for next time.

Use `--name <name>` to target a specific pod.

## How it works

1. **VRAM estimation** — queries the Ollama OCI registry to determine model size, applies a 1.2x overhead factor
2. **GPU selection** — queries RunPod for available GPUs, filters by VRAM, picks the cheapest
3. **Pod creation** — launches a `surajarogyalabs/kenai-ollama:latest` container with TCP port 11434 exposed
4. **Model pull** — waits for the pod to be ready, then pulls the requested model
5. **State tracking** — saves pod metadata to `~/.ollama-pod/pods/<name>.json`

The Ollama API endpoint is the TCP address (`http://<ip>:<port>`) when available, falling back to `https://<pod-id>-11434.proxy.runpod.net`.

## Development

```bash
uv sync
uv run pytest
```
