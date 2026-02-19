import json
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ollama_pod.gpu import find_cheapest_gpu
from ollama_pod.model_info import estimate_vram_gb
from ollama_pod.pod import (
    OLLAMA_PORT,
    create_ollama_pod,
    find_ollama_pods,
    get_endpoint,
    pull_model,
    terminate_pod,
    wait_for_ready,
)

app = typer.Typer(help="Spin up/down Ollama on RunPod GPUs.")
console = Console()

STATE_DIR = Path.home() / ".ollama-pod"
STATE_FILE = STATE_DIR / "active.json"


def _save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _load_state() -> dict | None:
    if not STATE_FILE.exists():
        return None
    return json.loads(STATE_FILE.read_text())


def _clear_state() -> None:
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def _sync_from_runpod() -> dict | None:
    """Query RunPod for a running Ollama pod and save it locally. Returns the state or None."""
    pods = find_ollama_pods()
    running = [p for p in pods if p.get("desiredStatus") == "RUNNING"]

    if not running:
        return None

    if len(running) > 1:
        console.print(f"[yellow]Found {len(running)} running Ollama pods:[/yellow]")
        for p in running:
            console.print(f"  {p['id']}  gpu={p.get('machine', {}).get('gpuDisplayName', '?')}")
        console.print("Cannot auto-sync with multiple pods.")
        return None

    pod = running[0]
    pod_id = pod["id"]
    machine = pod.get("machine") or {}
    gpu_type = machine.get("gpuDisplayName", "unknown")
    volume_id = pod.get("networkVolumeId")
    cost_per_hr = pod.get("costPerHr", 0.0)

    # Build endpoint from runtime port mapping
    endpoint = get_endpoint(pod_id)  # default: proxy URL
    runtime = pod.get("runtime") or {}
    for port_info in runtime.get("ports") or []:
        if port_info.get("privatePort") == OLLAMA_PORT and port_info.get("ip"):
            ip = port_info["ip"]
            public_port = port_info["publicPort"]
            protocol = "https" if port_info.get("type") == "http" else "http"
            endpoint = f"{protocol}://{ip}:{public_port}"
            break

    state = {
        "pod_id": pod_id,
        "model": "unknown",
        "endpoint": endpoint,
        "gpu_type": gpu_type,
        "cost_per_hr": cost_per_hr,
        "network_volume_id": volume_id,
        "created_at": pod.get("lastStatusChange", "unknown"),
    }
    _save_state(state)
    return state


@app.command()
def up(
    model: str = typer.Argument(help="Ollama model to pull (e.g. qwen2.5:7b)"),
    vram: float | None = typer.Option(None, help="Override VRAM estimate in GB"),
    gpu_type: str | None = typer.Option(None, help="Specific RunPod GPU type ID"),
    volume_id: str | None = typer.Option(None, help="RunPod network volume ID"),
) -> None:
    """Spin up an Ollama pod on RunPod and pull a model."""
    # Check for existing active pod
    existing = _load_state()
    if existing:
        console.print(
            f"[yellow]Pod already active:[/yellow] {existing['pod_id']} "
            f"({existing['endpoint']})\n"
            "Run [bold]ollama-pod down[/bold] first."
        )
        raise typer.Exit(1)

    # Resolve VRAM requirement
    if vram is None:
        with console.status(f"Querying model size for [bold]{model}[/bold]..."):
            min_vram = estimate_vram_gb(model)
        console.print(f"Estimated VRAM needed: {min_vram:.1f} GB")
    else:
        min_vram = vram

    # Inherit volume_id from previous state if available
    if volume_id is None:
        prev = _load_state()
        if prev and prev.get("network_volume_id"):
            volume_id = prev["network_volume_id"]

    # Find GPU
    if gpu_type is None:
        with console.status("Finding cheapest available GPU..."):
            gpu_type, cost_per_hr = find_cheapest_gpu(min_vram)
        console.print(f"Selected GPU: [bold]{gpu_type}[/bold] (${cost_per_hr:.2f}/hr)")
    else:
        cost_per_hr = 0.0  # unknown when manually specified

    # Create pod
    with console.status("Creating pod..."):
        pod_id = create_ollama_pod(gpu_type, network_volume_id=volume_id)
    console.print(f"Pod created: [bold]{pod_id}[/bold]")

    # Wait for ready
    try:
        with console.status("Waiting for pod to be ready..."):
            wait_for_ready(pod_id)
    except SystemExit:
        console.print("[red]Pod failed to start. Terminating...[/red]")
        terminate_pod(pod_id)
        raise

    endpoint = get_endpoint(pod_id)

    # Pull model
    try:
        with console.status(f"Pulling [bold]{model}[/bold] (may take a few minutes)..."):
            pull_model(endpoint, model)
    except Exception as e:
        console.print(f"[red]Model pull failed: {e}. Terminating pod...[/red]")
        terminate_pod(pod_id)
        raise typer.Exit(1)

    # Save state
    state = {
        "pod_id": pod_id,
        "model": model,
        "endpoint": endpoint,
        "gpu_type": gpu_type,
        "cost_per_hr": cost_per_hr,
        "network_volume_id": volume_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_state(state)

    console.print()
    console.print("[green bold]Pod is ready![/green bold]")
    console.print(f"  Endpoint: [bold]{endpoint}[/bold]")
    console.print(f"  Model:    {model}")
    console.print(f"  GPU:      {gpu_type}")
    if cost_per_hr > 0:
        console.print(f"  Cost:     ${cost_per_hr:.2f}/hr")


@app.command()
def down() -> None:
    """Terminate the active Ollama pod."""
    state = _load_state()
    if state is None:
        console.print("No active pod found.")
        raise typer.Exit(0)

    pod_id = state["pod_id"]
    with console.status(f"Terminating pod [bold]{pod_id}[/bold]..."):
        terminate_pod(pod_id)

    _clear_state()
    console.print(f"[green]Pod {pod_id} terminated.[/green]")
    if state.get("network_volume_id"):
        console.print("Network volume preserved — models cached for next run.")


@app.command()
def status() -> None:
    """Show the status of the active Ollama pod."""
    import runpod

    from ollama_pod.config import runpod_api_key

    state = _load_state()
    if state is None:
        with console.status("No local state — checking RunPod..."):
            state = _sync_from_runpod()
        if state is None:
            console.print("No active pod.")
            raise typer.Exit(0)
        console.print(f"[dim]Synced pod {state['pod_id']} from RunPod.[/dim]\n")

    runpod.api_key = runpod_api_key()
    try:
        pod = runpod.get_pod(state["pod_id"])
    except Exception:
        console.print("[yellow]Pod not found on RunPod. Cleaning up state.[/yellow]")
        _clear_state()
        raise typer.Exit(1)

    table = Table(title="Ollama Pod Status")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Pod ID", state["pod_id"])
    table.add_row("Model", state["model"])
    table.add_row("Endpoint", state["endpoint"])
    table.add_row("GPU", state["gpu_type"])
    table.add_row("Status", pod.get("desiredStatus", "unknown"))
    table.add_row("Runtime", "ready" if pod.get("runtime") else "starting")
    if state.get("cost_per_hr", 0) > 0:
        table.add_row("Cost", f"${state['cost_per_hr']:.2f}/hr")
    if state.get("network_volume_id"):
        table.add_row("Volume", state["network_volume_id"])
    table.add_row("Created", state.get("created_at", "unknown"))

    console.print(table)


