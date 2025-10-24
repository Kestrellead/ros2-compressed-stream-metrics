#!/usr/bin/env bash
set -euo pipefail
python -m stream_metrics.cli --kind rgb --codec jpeg --hz 30 --seconds 5
python -m stream_metrics.cli --kind rgb --codec png  --hz 15 --seconds 5
python -m stream_metrics.cli --kind tof --codec png16 --hz 20 --seconds 5
