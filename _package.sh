#!/usr/bin/env bash
# vim: set ts=2 sw=2 et:

set -euo pipefail

: <<'DOC'
统一构建脚本：支持清理、构建、上传 PyPI 包，支持组合参数执行。

用法示例：
  ./_clean.sh --clean
  ./_clean.sh --build
  ./_clean.sh --build --upload
  ./_clean.sh --clean --build
  ./_clean.sh --clean --build --upload

参数说明：
  --clean   删除 dist/ build/ *.egg-info
  --build   构建 sdist 与 wheel(默认前置执行 clean)
  --upload  上传至 PyPI(必须配合 --build)
DOC

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

DO_CLEAN=false
DO_BUILD=false
DO_UPLOAD=false

for arg in "$@"; do
  case "$arg" in
    --clean) DO_CLEAN=true ;;
    --build) DO_BUILD=true ;;
    --upload) DO_UPLOAD=true ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: $0 [--clean] [--build] [--upload]"
      exit 1
      ;;
  esac
done

# --upload 必须依赖 --build
if [[ "$DO_UPLOAD" == true && "$DO_BUILD" == false ]]; then
  echo "Error: --upload requires --build"
  exit 2
fi

# 如果 build 为 true，而 clean 为 false，则自动 clean
if [[ "$DO_BUILD" == true && "$DO_CLEAN" == false ]]; then
  echo "[STEP] Auto-clean before build ..."
  rm -rf dist/ build/ *.egg-info
fi

# 显式 clean
if [[ "$DO_CLEAN" == true ]]; then
  echo "[STEP] Cleaning dist/, build/, *.egg-info ..."
  rm -rf dist/ build/ *.egg-info
fi

# 构建
if [[ "$DO_BUILD" == true ]]; then
  echo "[STEP] Building package ..."
  python3 -m build
fi

# 上传
if [[ "$DO_UPLOAD" == true ]]; then
  echo "[STEP] Uploading package via twine ..."
  twine upload dist/*
fi
