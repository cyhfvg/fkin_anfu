#!/usr/bin/env bash
# vim: set ts=2 sw=2 et:

set -euo pipefail

: <<'DOC'
统一执行提交前的检查步骤，包括：

1. pre-commit --all-files   # 检查代码格式、导入顺序、空行等
2. pytest tests/            # 运行所有单元测试，确保功能未回归

适用于：
- 本地提交前人工执行；
- Git hook 调用；
- 集成至 CI/CD 流程前置验证。

注：该脚本要求 pre-commit、pytest 已安装并配置好。
DOC

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "[STEP] running pre-commit checks..."
if pre-commit run --all-files; then
  echo "[OK] pre-commit checks passed"
else
  echo "[FAIL] pre-commit checks failed"
  exit 1
fi

echo "[STEP] running pytest..."
if pytest tests/ --disable-warnings; then
  echo "[OK] pytest passed"
else
  echo "[FAIL] pytest failed"
  exit 1
fi
