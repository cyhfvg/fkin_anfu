# -*- coding: utf-8 -*-
"""
NucleiParser 单元测试
- 覆盖 TXT 行解析
- 覆盖 JSON 数组解析
- 覆盖 目录级解析（同时存在 TXT/JSON）并验证去重
- 断言关键字段与 FindingResult.deduplicate 的合并结果
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from fkin_anfu.parsers.models.finding_result import FindingResult
from fkin_anfu.parsers.nuclei_parser import NucleiParser


def _write(p: Path, content: str) -> None:
    """
    工具：写入文本文件（UTF-8）
    """
    p.write_text(content, encoding="utf-8")


def test_parse_txt_basic_http_record(tmp_path: Path) -> None:
    """
    验证：解析 nuclei 的 TXT 一行 HTTP 资产信息，字段映射正确。
    """
    # TXT 示例（每行五段：name, type, severity, address, info(可选)）
    # 示例中 info 为 JSON 字符串数组
    txt_line = '[gunicorn-detect] [http] [info] http://192.168.32.204:7099 ["gunicorn/19.9.0"]\n'
    txt_path = tmp_path / "nuclei.txt"
    _write(txt_path, txt_line)

    parser = NucleiParser()
    results: List[FindingResult] = parser.parse(txt_path, recursive=False)

    # 关键断言（输出样例见注释）
    assert len(results) == 1
    r = results[0]
    assert r.name == "gunicorn-detect"  # 输出样例: 'gunicorn-detect'
    assert r.protocol == "http"  # 'http'
    assert r.service == "http"  # 'http'
    assert r.ip == "192.168.32.204"  # '192.168.32.204'
    assert r.port == 7099  # 7099
    assert r.url.startswith("http://192.168.32.204:7099")  # True
    assert r.severity == "info"  # 'info'
    assert r.finding_type in ("asset", "vuln")  # 具体取决于你的实现策略；常见做法：info=asset
    assert r.raw_path == "nuclei.txt"  # 'nuclei.txt'
    # info 提取：若实现将 info 放在 title 或 extra["extracted"]，做柔性断言
    assert ("gunicorn" in (r.title or "")) or ("extracted" in r.extra)


def test_parse_txt_tcp_record_with_info(tmp_path: Path) -> None:
    """
    验证：解析 nuclei 的 TXT 一行 TCP 资产信息（无 URL，仅 host:port）。
    """
    txt_line = (
        '[vmware-authentication-daemon] [tcp] [info] 192.168.7.37:902 '
        '["VMware Authentication Daemon Version 1.10"]\n'
    )
    txt_path = tmp_path / "n_tcp.txt"
    _write(txt_path, txt_line)

    parser = NucleiParser()
    results = parser.parse(txt_path)
    assert len(results) == 1
    r = results[0]
    assert r.ip == "192.168.7.37"
    assert r.port == 902
    assert r.protocol in ("tcp", "")  # 常见做法：无 URL 则 protocol=tcp
    assert r.service in ("tcp", "vmware", "")  # 取决于你的映射策略
    assert r.severity == "info"
    # 信息应被保存到 title 或 extra
    assert ("VMware Authentication" in (r.title or "")) or ("extracted" in r.extra)


def test_parse_txt_cve_medium(tmp_path: Path) -> None:
    """
    验证：TXT 行为 CVE 中危漏洞，host:port 地址映射正确。
    """
    txt_line = '[CVE-2023-48795] [javascript] [medium] 192.168.0.172:22 ["Vulnerable to Terrapin"]\n'
    txt_path = tmp_path / "cve.txt"
    _write(txt_path, txt_line)

    parser = NucleiParser()
    results = parser.parse(txt_path)
    assert len(results) == 1
    r = results[0]
    assert r.name == "CVE-2023-48795"
    assert r.severity == "medium"
    assert r.ip == "192.168.0.172"
    assert r.port == 22
    # 非 http 场景，protocol 一般为 tcp，service 可保留为 'javascript'（nuclei type）或 'tcp'
    assert r.finding_type == "vuln"
    assert ("Terrapin" in (r.title or "")) or ("extracted" in r.extra)


def test_parse_json_array(tmp_path: Path) -> None:
    """
    验证：解析 nuclei JSON 数组（简化示例），匹配关键字段。
    """
    data = [
        {
            "template-id": "gunicorn-detect",
            "info": {"name": "gunicorn-detect", "severity": "info"},
            "type": "http",
            "host": "192.168.32.204:7099",
            "port": "7099",
            "scheme": "http",
            "matched-at": "http://192.168.32.204:7099",
            "extracted-results": ["gunicorn/19.9.0"],
            "matcher-status": True,
        }
    ]
    json_path = tmp_path / "nuclei.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    parser = NucleiParser()
    results = parser.parse(json_path)
    assert len(results) == 1
    r = results[0]
    assert r.name == "gunicorn-detect"
    assert r.ip == "192.168.32.204"
    assert r.port == 7099
    assert r.protocol == "http"
    assert r.service == "http"
    assert r.severity == "info"
    assert r.url.startswith("http://192.168.32.204:7099")
    assert ("gunicorn" in (r.title or "")) or ("extracted" in r.extra)


def test_parse_dir_and_dedupe_between_txt_and_json(tmp_path: Path) -> None:
    """
    验证：目录下同时存在 TXT 与 JSON，代表同一发现时进行去重，只保留 1 条。
    注意：为了保证匹配到同一去重 key，这里让 TXT 与 JSON 的 name 与 URL 一致。
    """
    # 1) 写入 TXT（与 JSON 目标一致）
    txt = '[gunicorn-detect] [http] [info] http://192.168.32.204:7099 ["gunicorn/19.9.0"]\n'
    _write(tmp_path / "a.txt", txt)

    # 2) 写入 JSON（同一目标）
    data = [
        {
            "template-id": "gunicorn-detect",
            "info": {"name": "gunicorn-detect", "severity": "info"},
            "type": "http",
            "host": "192.168.32.204:7099",
            "port": "7099",
            "scheme": "http",
            "matched-at": "http://192.168.32.204:7099",
            "extracted-results": ["gunicorn/19.9.0"],
            "matcher-status": True,
        }
    ]
    (tmp_path / "b.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    parser = NucleiParser()
    results = parser.parse(tmp_path, recursive=False)

    # 断言：去重后 1 条，且 raw_path 合并（顺序可能 a.txt,b.json）
    assert len(results) == 1
    r = results[0]
    assert r.name == "gunicorn-detect"
    assert r.ip == "192.168.32.204" and r.port == 7099
    # 输出样例：'a.txt,b.json' 或 'b.json,a.txt'（取决于你的合并实现）
    assert "a.txt" in r.raw_path and "b.json" in r.raw_path
