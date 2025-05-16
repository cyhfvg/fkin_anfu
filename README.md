# fkin_anfu

安全服务效率工具

## usage

```python
cd fkin_anfu
python -m venv .venv
source .venv/bin/activate
```

### 依赖安装

```bash
pip install pip-tools
# 生成生产依赖
pip-compile requirements.in --output-file=requirements.txt

# 生成开发依赖（含测试工具）
pip-compile requirements-dev.in --output-file=requirements-dev.txt

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 提交代码

使用`pre-commit`做代码风格检查， 已封装为`_shortcut_action.sh`简便执行；

```bash
# 安装1次
pip install pre-commit
pre-commit install
```

```bash
# 手动触发check
pre-commit run --all-files
git diff   # 确认无自动修改残留
# 手动添加文件修改
git add .
git commit -m "fix(XXXX): code quality passed by pre-commit"
```

```bash
# 手动执行test
pytest

pytest tests/utils/test_log_utils.py
```
