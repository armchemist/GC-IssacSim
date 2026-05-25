#!/usr/bin/env bash
# Load omx_f.urdf into Isaac Sim 5.1 with WebRTC livestream.
# Connect from local PC using "Isaac Sim WebRTC Streaming Client".
#   Server IP: 166.104.223.32
set -e
source /data1/workspaces/jgshin22/miniconda3/etc/profile.d/conda.sh
conda activate isaac_sim

export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-1}
export PUBLIC_ENDPOINT_ADDRESS=166.104.223.32

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_DIR/.isaacsim_logs"
mkdir -p "$LOG_DIR"
cd "$LOG_DIR"

exec python "$PROJECT_DIR/load_omx_f.py" \
    --/app/livestream/publicEndpointAddress=166.104.223.32 \
    --/app/livestream/port=49100 \
    "$@"
