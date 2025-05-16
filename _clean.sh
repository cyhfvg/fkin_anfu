#!/usr/bin/env bash
# vim: set ts=2 sw=2 et:

set -euo pipefail

: <<'DOC'
统一执行打包前清理动作

1. 清理dist/ build/ *.egg-info   # 删除之前的打包痕迹

适用于：
- 打包之前的准备

DOC

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "[STEP] clean dist, build, egg-info etc..."
rm -rf dist/ build/ *.egg-info
