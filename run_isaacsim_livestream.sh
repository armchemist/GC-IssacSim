#!/usr/bin/env bash
# Launch Isaac Sim 5.1 in WebRTC livestream (headless) mode.
# Connect from local PC using the "Isaac Sim WebRTC Streaming Client".
#   Server IP: 166.104.223.32
#   Required open ports: TCP/UDP 47995-48012, 49000-49007, TCP 8211, 8011

set -e
source /data1/workspaces/jgshin22/miniconda3/etc/profile.d/conda.sh
conda activate isaac_sim

# Pick a GPU (RTX 3080 #0 has some memory used; #1 is free)
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-1}

# Use the prebuilt streaming app config
APP=isaacsim.exp.full.streaming.kit

# Keep NvStreamer .etli trace logs out of the project root
LOG_DIR="$(dirname "$0")/.isaacsim_logs"
mkdir -p "$LOG_DIR"
cd "$LOG_DIR"

exec isaacsim "$APP" \
    --no-window \
    --/app/livestream/publicEndpointAddress=166.104.223.32 \
    --/app/livestream/port=49100 \
    "$@"
