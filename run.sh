#!/bin/bash
set -e

# Parse command line arguments
START_OLLAMA=false
START_OPENWEBUI=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --ollama)
            START_OLLAMA=true
            shift
            ;;
        --openwebui)
            START_OPENWEBUI=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --ollama      Start Ollama service"
            echo "  --openwebui   Start Open WebUI service"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --ollama                # Start only Ollama"
            echo "  $0 --openwebui             # Start only Open WebUI"
            echo "  $0 --ollama --openwebui    # Start both services"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# If no arguments provided, show usage
if [[ "$START_OLLAMA" == false && "$START_OPENWEBUI" == false ]]; then
    echo "No services specified. Use --help for usage information."
    exit 1
fi

mkdir -p /home/dev/logs

# Start Ollama if requested
if [[ "$START_OLLAMA" == true ]]; then
    touch /home/dev/logs/ollama.log
    echo "Starting Ollama..."
    ollama serve > /home/dev/logs/ollama.log 2>&1 &
fi

# Start Open WebUI if requested
if [[ "$START_OPENWEBUI" == true ]]; then
    touch /home/dev/logs/openwebui.log
    echo "Starting Open WebUI..."
    uv run open-webui serve > /home/dev/logs/openwebui.log 2>&1 &
fi

