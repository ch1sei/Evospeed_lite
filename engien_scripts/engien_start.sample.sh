#!/usr/bin/env bash

CUDA_VISIBLE_DEVICES=6,7 \
exec ~/sglang-runtime/.venv/bin/sglang serve \
    --model-path /data/models/Qwen/Qwen3.6-35B-A3B \
    --host 127.0.0.1 \
    --port 30000 \
    --tp-size 2