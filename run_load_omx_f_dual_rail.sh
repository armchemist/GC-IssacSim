#!/usr/bin/env bash
# Import omx_f_dual_on_rail.urdf → model/omx_f_dual_rail.usd and stream via WebRTC.
# Run this ONCE to generate the USD; then use run_teleop_omx_dual_rail.sh for teleop.
set -e
source /data1/workspaces/jgshin22/miniconda3/etc/profile.d/conda.sh
conda activate isaac_sim

export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-1}
export PUBLIC_ENDPOINT_ADDRESS=166.104.223.32
export PYTHONUNBUFFERED=1   # flush [lab_scene]/[teleop] prints immediately

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_DIR/.isaacsim_logs"
mkdir -p "$LOG_DIR"
cd "$LOG_DIR"

exec python "$PROJECT_DIR/load_omx_f_dual_rail.py" \
    --/app/livestream/publicEndpointAddress=166.104.223.32 \
    --/app/livestream/port=49100 \
    "$@"
