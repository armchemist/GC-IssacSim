#!/usr/bin/env bash
# Keyboard teleoperation of TWO OMX_F arms on one rail in Isaac Sim 5.1 (WebRTC).
# Requires model/omx_f_dual_rail.usd — run run_load_omx_f_dual_rail.sh first if absent.
set -e
source /data1/workspaces/jgshin22/miniconda3/etc/profile.d/conda.sh
conda activate isaac_sim

export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-1}
export PUBLIC_ENDPOINT_ADDRESS=166.104.223.32

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_DIR/.isaacsim_logs"
mkdir -p "$LOG_DIR"
cd "$LOG_DIR"

exec python "$PROJECT_DIR/teleop_omx_dual_rail.py" \
    --/app/livestream/publicEndpointAddress=166.104.223.32 \
    --/app/livestream/port=49100 \
    "$@"
