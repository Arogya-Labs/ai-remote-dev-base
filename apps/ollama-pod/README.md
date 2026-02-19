# ollama-pod

Deploy and manage [Ollama](https://ollama.com) on [RunPod](https://www.runpod.io) GPU cloud with a single command.

## What it does

- Provisions a RunPod pod with a GPU sized for your model
- Automatically picks the cheapest available GPU that fits
- Pulls the model and exposes the Ollama HTTP API
- Tracks active pod state locally for easy teardown

## Install

```bash
uv sync
```

## Configuration

Copy `.env.example` to `.env` and fill in your RunPod API key:

```
RUNPOD_API_KEY=<your-key>
```

## Usage

### Spin up a pod

```bash
uv run ollama-pod up <model>
```

Example:

```bash
uv run ollama-pod up qwen2.5:7b
```

Options:

| Flag | Description |
|------|-------------|
| `--vram` | Override the auto-estimated VRAM (GB) |
| `--gpu-type` | Use a specific GPU type ID instead of auto-selecting |
| `--volume-id` | Attach a network volume (caches models across runs) |

### Check status

```bash
uv run ollama-pod status
```

Shows pod ID, model, endpoint URL, GPU type, cost/hr, and runtime status.

### Tear down

```bash
uv run ollama-pod down
```

Terminates the pod. If a network volume was used, it's preserved for next time.

## How it works

1. **VRAM estimation** — queries the Ollama OCI registry to determine model size, applies a 1.2x overhead factor
2. **GPU selection** — queries RunPod for available GPUs, filters by VRAM, picks the cheapest
3. **Pod creation** — launches an `ollama/ollama` container with port 11434 exposed
4. **Model pull** — waits for the pod to be ready, then pulls the requested model
5. **State tracking** — saves pod metadata to `~/.ollama-pod/active.json`

The Ollama API is available at `https://<pod-id>-11434.proxy.runpod.net`.

## Testing

```bash
uv run pytest
```
