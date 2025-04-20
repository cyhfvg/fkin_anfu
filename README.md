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
