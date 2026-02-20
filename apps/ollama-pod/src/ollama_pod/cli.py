import json
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ollama_pod.gpu import CloudType, find_cheapest_gpu
from ollama_pod.model_info import estimate_vram_gb
from ollama_pod.pod import (
    CLOUD_TYPE_MAP,
    OLLAMA_IMAGE,
    create_ollama_pod,
    find_ollama_pods,
    get_endpoint,
    pull_model,
    resolve_volume_datacenter,
    terminate_pod,
    wait_for_ready,
)

app = typer.Typer(help="Spin up/down Ollama on RunPod GPUs.")
console = Console()

STATE_DIR = Path.home() / ".ollama-pod"
PODS_DIR = STATE_DIR / "pods"


def _pod_file(name: str) -> Path:
    return PODS_DIR / f"{name}.json"


def _save_state(name: str, state: dict) -> None:
    PODS_DIR.mkdir(parents=True, exist_ok=True)
    state["name"] = name
    _pod_file(name).write_text(json.dumps(state, indent=2))


def _load_state(name: str) -> dict | None:
    path = _pod_file(name)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _load_all_states() -> list[dict]:
    if not PODS_DIR.exists():
        return []
    return [json.loads(f.read_text()) for f in sorted(PODS_DIR.glob("*.json"))]


def _clear_state(name: str) -> None:
    path = _pod_file(name)
    if path.exists():
        path.unlink()


def _sync_from_runpod() -> list[dict]:
    """Query RunPod for all running Ollama pods and save them locally. Returns synced states."""
    pods = find_ollama_pods()
    running = [p for p in pods if p.get("desiredStatus") == "RUNNING"]

    if not running:
        return []

    synced: list[dict] = []
    for pod in running:
        pod_id = pod["id"]
        pod_name = pod.get("name") or pod_id
        machine = pod.get("machine") or {}
        gpu_type = machine.get("gpuDisplayName", "unknown")
        volume_id = pod.get("networkVolumeId")
        cost_per_hr = pod.get("costPerHr", 0.0)

        endpoint = get_endpoint(pod)

        state = {
            "pod_id": pod_id,
            "model": "unknown",
            "endpoint": endpoint,
            "gpu_type": gpu_type,
            "cost_per_hr": cost_per_hr,
            "network_volume_id": volume_id,
            "created_at": pod.get("lastStatusChange", "unknown"),
        }
        _save_state(pod_name, state)
        synced.append(state)

    return synced


@app.command()
def up(
    model: str = typer.Argument(help="Ollama model to pull (e.g. qwen2.5:7b)"),
    name: str = typer.Option("default", help="Name for this pod (used for multi-pod tracking)"),
    vram: float | None = typer.Option(None, help="Override VRAM estimate in GB"),
    gpu_type: str | None = typer.Option(None, help="Specific RunPod GPU type ID"),
    volume_id: str | None = typer.Option(None, help="RunPod network volume ID"),
    cloud_type: CloudType = typer.Option("any", help="Cloud type: any, community, or secure"),
    image: str | None = typer.Option(None, help=f"Docker image (default: {OLLAMA_IMAGE})"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show GPU and cost without creating a pod"),
) -> None:
    """Spin up an Ollama pod on RunPod and pull a model."""
    # Check for existing active pod with this name
    existing = _load_state(name)
    if existing:
        console.print(
            f"[yellow]Pod '{name}' already active:[/yellow] {existing['pod_id']} "
            f"({existing['endpoint']})\n"
            f"Run [bold]ollama-pod down --name {name}[/bold] first."
        )
        raise typer.Exit(1)

    # Resolve VRAM requirement
    if vram is None:
        with console.status(f"Querying model size for [bold]{model}[/bold]..."):
            min_vram = estimate_vram_gb(model)
        console.print(f"Estimated VRAM needed: {min_vram:.1f} GB")
    else:
        min_vram = vram

    # Resolve datacenter when volume is specified
    datacenter_id: str | None = None
    if volume_id:
        with console.status("Looking up volume datacenter..."):
            datacenter_id = resolve_volume_datacenter(volume_id)
        if datacenter_id:
            console.print(f"Volume [bold]{volume_id}[/bold] pinned to datacenter [bold]{datacenter_id}[/bold]")
        else:
            console.print(f"[yellow]Warning: could not resolve datacenter for volume {volume_id}[/yellow]")

    # Find GPU
    if gpu_type is None:
        with console.status("Finding cheapest available GPU..."):
            gpu_type, cost_per_hr, resolved_cloud = find_cheapest_gpu(min_vram, cloud_type)
        console.print(
            f"Selected GPU: [bold]{gpu_type}[/bold] (${cost_per_hr:.2f}/hr, {resolved_cloud} cloud)"
        )
        if datacenter_id and cloud_type != "any":
            console.print(
                f"[yellow]Note: GPU availability is based on global data. "
                f"{gpu_type} may not be available as {resolved_cloud} cloud "
                f"in datacenter {datacenter_id}. Deployment will fail fast if so.[/yellow]"
            )
    else:
        cost_per_hr = 0.0  # unknown when manually specified
        resolved_cloud = cloud_type

    if dry_run:
        console.print("\n[bold]Dry run summary:[/bold]")
        console.print(f"  Model: {model}")
        console.print(f"  Image: {image or OLLAMA_IMAGE}")
        console.print(f"  Name:  {name}")
        console.print(f"  VRAM:  {min_vram:.1f} GB")
        console.print(f"  GPU:   {gpu_type}")
        if cost_per_hr > 0:
            console.print(f"  Cost:  ${cost_per_hr:.2f}/hr")
        raise typer.Exit(0)

    # Create pod
    with console.status("Creating pod..."):
        pod_id = create_ollama_pod(
            gpu_type,
            name=name,
            network_volume_id=volume_id,
            cloud_type=CLOUD_TYPE_MAP[cloud_type],
            image=image,
        )
    console.print(f"Pod created: [bold]{pod_id}[/bold]")

    # Wait for ready
    try:
        with console.status("Waiting for pod to be ready..."):
            pod_info = wait_for_ready(pod_id)
    except SystemExit:
        console.print("[red]Pod failed to start. Terminating...[/red]")
        terminate_pod(pod_id)
        raise

    endpoint = get_endpoint(pod_info)

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
    _save_state(name, state)

    console.print()
    console.print("[green bold]Pod is ready![/green bold]")
    console.print(f"  Name:     {name}")
    console.print(f"  Endpoint: [bold]{endpoint}[/bold]")
    console.print(f"  Model:    {model}")
    console.print(f"  GPU:      {gpu_type}")
    if cost_per_hr > 0:
        console.print(f"  Cost:     ${cost_per_hr:.2f}/hr")


@app.command()
def down(
    name: str = typer.Option("default", help="Name of the pod to terminate"),
) -> None:
    """Terminate a tracked Ollama pod."""
    state = _load_state(name)
    if state is None:
        existing = _load_all_states()
        if existing:
            names = [s.get("name", "?") for s in existing]
            console.print(f"No pod named '{name}'. Tracked pods: {', '.join(names)}")
        else:
            console.print("No tracked pods found.")
        raise typer.Exit(1)

    pod_id = state["pod_id"]
    with console.status(f"Terminating pod [bold]{pod_id}[/bold]..."):
        terminate_pod(pod_id)

    _clear_state(name)
    console.print(f"[green]Pod '{name}' ({pod_id}) terminated.[/green]")
    if state.get("network_volume_id"):
        console.print("Network volume preserved — models cached for next run.")


@app.command()
def status(
    name: str | None = typer.Option(None, help="Name of a specific pod to show"),
) -> None:
    """Show the status of tracked Ollama pods."""
    import runpod

    from ollama_pod.config import runpod_api_key

    runpod.api_key = runpod_api_key()

    if name is not None:
        # Show a single named pod
        state = _load_state(name)
        if state is None:
            console.print(f"No pod named '{name}'.")
            raise typer.Exit(1)
        _print_pod_table(runpod, state)
        return

    # Show all tracked pods
    states = _load_all_states()
    if not states:
        with console.status("No local state — checking RunPod..."):
            synced = _sync_from_runpod()
        if not synced:
            console.print("No active pods.")
            raise typer.Exit(0)
        for s in synced:
            console.print(f"[dim]Synced pod {s['pod_id']} as '{s['name']}'.[/dim]")
        console.print()
        states = synced

    for state in states:
        _print_pod_table(runpod, state)
        console.print()


def _print_pod_table(runpod_mod, state: dict) -> None:  # noqa: ANN001
    """Print a Rich table for a single pod state."""
    pod_name = state.get("name", "?")
    try:
        pod = runpod_mod.get_pod(state["pod_id"])
    except Exception:
        console.print(f"[yellow]Pod '{pod_name}' ({state['pod_id']}) not found on RunPod. Cleaning up.[/yellow]")
        _clear_state(pod_name)
        return

    table = Table(title=f"Pod: {pod_name}")
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


