#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
nuclei 扫描结果解析

支持:
- 单个文件解析
- 目录递归解析(.txt 与 .json)
- 转换为统一的 FindingResult 列表结构

TXT 行格式(每行一条):
    [name] [service] [severity] address [info?]
字段含义:
    - name:漏洞/指纹名称
    - service:服务类型(http/tcp/javascript/...)
    - severity:漏洞级别(info/low/medium/high/critical)
    - address:URL 或 ip:port 或 ip
    - info(可选):可能为 JSON 数组/字符串/原始文本

JSON 关键字段(每个对象):
    - info.name           → 漏洞/指纹名称
    - info.severity       → 漏洞级别
    - type                → 服务类型
    - matched-at          → 漏洞地址(优先)
    - extracted-results   → 漏洞信息(可选)
    - host                → 可能为 ip 或 ip:port
    - port                → 端口(权威来源,优先于 host 携带的端口)
    - scheme              → http/https(若存在可用于组装 URL)

实现说明:
- 解析出标准 FindingResult:
  ip, port, protocol, url, service, finding_type, name, title, product, version, severity, source_tool, raw_path
- 地址解析优先级(JSON):matched-at > url > scheme+host+port > host
- 端口以 JSON 的 port 字段为准；若 URL 上未显式端口,会进行补齐
- 资产/漏洞分类:severity ∈ {low/medium/high/critical} 视为 vuln,否则 asset
- 轻量产品/版本提取:支持 “prod/ver” 与 “<prod> Version <ver>” 两类常见模式

@author: cyhfvg
@date: 2025/10/24
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

from fkin_anfu.parsers.base_parser import BaseParser
from fkin_anfu.parsers.models.finding_result import FindingResult
from fkin_anfu.utils.color_utils import YELLOW
from fkin_anfu.utils.file_utils import safe_read_lines
from fkin_anfu.utils.log_utils import debug_print

__all__ = ["NucleiParser"]


class NucleiParser(BaseParser):
    """
    nuclei 扫描结果解析器:将 nuclei 输出的 .txt/.json 结果解析为 FindingResult 结构。
    """

    # 可识别扩展名
    _TXT_SUFFIXES = {".txt"}
    _JSON_SUFFIXES = {".json"}  # 如需支持 .jsonl 可后续扩展

    # TXT 行解析主正则:
    # 形如:[name] [service] [severity] address [info?]
    _TXT_LINE_PATTERN = re.compile(r'^\[([^\]]+)\]\s+\[([^\]]+)\]\s+\[([^\]]+)\]\s+(\S+)(?:\s+\[(.+)\])?\s*$')

    # IPv4 或 IPv4:port
    _IP_PORT_PATTERN = re.compile(r'^(?P<ip>(?:\d{1,3}\.){3}\d{1,3})(?::(?P<port>\d{1,5}))?$')

    # product/version 轻量提取:如 "gunicorn/19.9.0"
    _PROD_VER_SLASH = re.compile(r'(?P<prod>[A-Za-z][A-Za-z0-9._\- ]{0,63})\s*/\s*(?P<ver>[0-9][A-Za-z0-9._\-]*)')

    # "<prod> Version <ver>" 形式
    _VER_WORD_PATTERN = re.compile(
        r'(?P<prod>[A-Za-z][A-Za-z0-9._\- ]{0,63})\s+Version\s+(?P<ver>[0-9][A-Za-z0-9._\-]*)',
        re.IGNORECASE,
    )

    # ==============================
    # public entry
    # ==============================
    def parse(self, path: Path, recursive: bool = False) -> List[FindingResult]:
        """
        扫描结果解析方法,支持文件或目录输入。

        Args:
            path (Path): 输入路径(文件或目录)
            recursive (bool): 是否递归目录

        Returns:
            List[FindingResult]: 标准结构的解析结果
        """
        findings: list[FindingResult] = []

        if path.is_file():
            findings.extend(self._parse_file(path))
        elif path.is_dir():
            files: list[Path] = self._collect_files(path, recursive)
            debug_print("INFO", f"[NucleiParser] 发现 {len(files)} 个待解析文件")
            for file in files:
                findings.extend(self._parse_file(file))
        else:
            raise FileNotFoundError(f"Input path not found: {path}")

        before = len(findings)
        findings = FindingResult.deduplicate(findings)
        after = len(findings)
        debug_print("INFO", f"[NucleiParser] 成功解析 {YELLOW(before)} 条记录, 去重后剩余 {YELLOW(after)} 条记录")
        return findings

    # ==============================
    # internal helpers
    # ==============================
    def _collect_files(self, root: Path, recursive: bool) -> list[Path]:
        """
        收集指定目录下的 .txt 与 .json 文件。

        Args:
            root (Path): 根目录
            recursive (bool): 是否递归

        Returns:
            list[Path]: 目标文件列表
        """
        if recursive:
            candidates = (p for p in root.rglob("*") if p.is_file())
        else:
            candidates = (p for p in root.iterdir() if p.is_file())

        files: list[Path] = []
        for p in candidates:
            suf = p.suffix.lower()
            if suf in self._TXT_SUFFIXES or suf in self._JSON_SUFFIXES:
                files.append(p)
        return files

    def _parse_file(self, path: Path) -> list[FindingResult]:
        """
        解析单个 nuclei 扫描结果文件。按扩展名分发到具体处理逻辑。

        Args:
            path (Path): 文件路径

        Returns:
            list[FindingResult]: 提取的结果
        """
        try:
            suf = path.suffix.lower()
            if suf in self._TXT_SUFFIXES:
                return self._parse_txt_file(path)
            elif suf in self._JSON_SUFFIXES:
                return self._parse_json_file(path)
            else:
                debug_print("WARN", f"[NucleiParser] 跳过不支持的文件类型: {path.name}")
                return []
        except Exception as why:
            raise RuntimeError(f"Failed to parse file: {path}") from why

    def _parse_txt_file(self, path: Path) -> list[FindingResult]:
        """
        解析 nuclei 的 .txt 输出文件。

        Args:
            path (Path): 文件路径

        Returns:
            list[FindingResult]: 提取的结果
        """
        findings: list[FindingResult] = []
        try:
            lines = safe_read_lines(path)
        except Exception as why:
            raise RuntimeError(f"Failed to read file: {path}") from why

        for line in lines:
            text = line.strip()
            if not text:
                continue
            item = self._parse_txt_line(text, raw_path=path.name)
            if item is not None:
                findings.append(item)

        debug_print("INFO", f"[NucleiParser] 解析文件 {path.name} 行/记录 {len(lines)}, 产出 {len(findings)}")
        return findings

    def _parse_txt_line(self, line: str, raw_path: str) -> Optional[FindingResult]:
        """
        解析 nuclei .txt 单行输出。

        Args:
            line (str): 单行文本
            raw_path (str): 来源文件名

        Returns:
            Optional[FindingResult]: 匹配成功返回 FindingResult,否则 None

        兼容示例:
            [favicon-detect:prometheus-time] [http] [info] http://192.168.43.119:30006/favicon.ico ["-1399433489"]
            [fingerprinthub-web-fingerprints:prometheus] [http] [info] http://192.168.43.119:30006/graph
            [vmware-authentication-daemon] [tcp] [info] 192.168.7.37:902 ["VMware Authentication Daemon Version 1.10"]
            [gunicorn-detect] [http] [info] http://192.168.32.204:7099 ["gunicorn/19.9.0"]
            [basic-auth-detect] [http] [info] http://192.168.0.172:8761 ["Basic realm="Realm""]
            [CVE-2023-48795] [javascript] [medium] 192.168.0.172:22 ["Vulnerable to Terrapin"]
        """
        m = self._TXT_LINE_PATTERN.match(line)
        if not m:
            # 行式不符,忽略
            return None

        name_raw, service_raw, severity_raw, address, info_raw = m.groups()

        # 统一化
        name = (name_raw or "").strip()
        service = (service_raw or "").strip().lower()
        severity = self._normalize_severity(severity_raw)

        # 解析地址
        ip, port, protocol, url = self._parse_address(address, service_hint=service)

        # info 清洗与可选 product/version 提取
        info_clean = self._clean_info(info_raw)
        product, version = self._extract_product_version(info_clean, name_hint=name)

        # 资产或漏洞类型判断
        finding_type = self._classify_finding_type_from_severity(severity)

        # service 兜底:当地址为 http(s) 时固定 http,否则沿用 service 或回退 tcp
        final_service = "http" if url and url.startswith(("http://", "https://")) else (service or "tcp")

        return FindingResult(
            ip=ip,
            port=port,
            protocol=protocol,
            url=url,
            service=final_service,
            finding_type=finding_type,
            name=name,
            title=info_clean or name,
            product=product,
            version=version,
            severity=severity,
            source_tool="nuclei",
            raw_path=raw_path,
        )

    # ==============================
    # JSON pipeline
    # ==============================
    def _parse_json_file(self, path: Path) -> list[FindingResult]:
        """
        解析 nuclei 的 .json 输出文件。

        Args:
            path (Path): 文件路径

        Returns:
            list[FindingResult]: 提取的结果
        """
        findings: list[FindingResult] = []
        try:
            content = path.read_text(encoding='utf-8')
        except Exception as why:
            raise RuntimeError(f"Failed to read file: {path}") from why

        try:
            data = json.loads(content)
        except Exception as why:
            raise RuntimeError(f"Invalid JSON format: {path}") from why

        for obj in self._iter_json_objects(data):
            item = self._parse_json_obj(obj, raw_path=path.name)
            if item is not None:
                findings.append(item)

        debug_print(
            "INFO",
            f"[NucleiParser] 解析文件 {path.name} 行/记录 {self._count_json_records(data)}, 产出 {len(findings)}",
        )
        return findings

    def _iter_json_objects(self, data: Any) -> Iterable[dict]:
        """
        将 nuclei JSON 顶层结构展开为对象序列,兼容常见两种形态:
        - 顶层列表:[{}, {}, ...]
        """
        if isinstance(data, list):
            for obj in data:
                if isinstance(obj, dict):
                    yield obj

    def _count_json_records(self, data: Any) -> int:
        """
        统计 JSON 中记录条数,仅用于日志展示。
        """
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict) and "results" in data and isinstance(data["results"], list):
            return len(data["results"])
        return 1

    def _parse_json_obj(self, obj: dict, raw_path: str) -> Optional[FindingResult]:
        """
        解析 nuclei JSON 单对象。

        关键字段(关注):
          - name ← obj.info.name
          - severity ← obj.info.severity
          - type ← obj.type
          - matched-at ← 漏洞地址(优先)
          - extracted-results ← 漏洞信息(可选)
          - host 可能为 ip 或 ip:port
          - port 为端口(权威来源,优先于 host 携带的端口)
        """
        info = obj.get("info") or {}
        name = info.get('name', '').strip()
        severity = self._normalize_severity(info.get("severity", "info"))
        type_str = (obj.get("type") or "").strip().lower()
        scheme = (obj.get("scheme") or "").strip().lower()
        cve_id = ''
        classification = info.get('classification')
        if classification:
            cve_id = classification.get('cve-id', '')
            if not cve_id:
                cve_id = ''
            else:
                cve_id = ','.join(cve_id)

        # host 可能是 ip 或 ip:port
        host_raw: str = obj.get("host") or ""
        host_ip, host_port = self._split_host(host_raw)

        port_authority: Optional[int] = int(obj.get("port", 0))

        # 漏洞地址候选:matched-at > url > scheme+host+port > host
        addr = obj.get("matched-at") or obj.get("url") or ""
        if not addr:
            if scheme in {"http", "https"} and host_ip:
                if port_authority is not None:
                    addr = f"{scheme}://{host_ip}:{port_authority}"
                elif host_port is not None:
                    addr = f"{scheme}://{host_ip}:{host_port}"
                else:
                    default_port = 443 if scheme == "https" else 80
                    addr = f"{scheme}://{host_ip}:{default_port}"
            elif host_raw:
                addr = host_raw

        # 解析地址获取 ip/port/protocol/url
        ip, port, protocol, url = self._parse_address(addr, service_hint=type_str)

        if port_authority is not None:
            port = port_authority
            # 若 url 为 http(s) 且无显式端口,则补齐
            if url.startswith(("http://", "https://")):
                parsed = urlparse(url)
                if parsed.hostname and parsed.port is None:
                    rebuilt = parsed._replace(netloc=f"{parsed.hostname}:{port_authority}")
                    url = rebuilt.geturl()

        # 若 ip 仍为空,尝试从 host 获取
        if not ip and host_ip:
            ip = host_ip

        # protocol / service 归一化
        final_protocol = scheme or protocol or type_str or "tcp"
        final_service = (
            "http" if (url.startswith(("http://", "https://")) or scheme in {"http", "https"}) else (type_str or "tcp")
        )

        # title 与产品版本
        extracted = obj.get("extracted-results")
        title = ""
        if isinstance(extracted, list) and extracted:
            title = ", ".join(str(x) for x in extracted)
        elif isinstance(extracted, (str, int, float, bool)):
            title = str(extracted)

        product, version = self._extract_product_version(title, name_hint=name)

        # 资产或漏洞类型
        finding_type = self._classify_finding_type_from_severity(severity)

        return FindingResult(
            ip=ip,
            port=port,
            protocol=final_protocol,
            url=url,
            service=final_service,
            finding_type=finding_type,
            name=name,
            title=title or name,
            cve_id=cve_id,
            product=product,
            version=version,
            severity=severity,
            source_tool="nuclei",
            raw_path=raw_path,
        )

    # ==============================
    # utilities
    # ==============================
    def _normalize_severity(self, s: str) -> str:
        """
        归一化 severity 至常见集合；未命中集合时回退为 "info"。

        Args:
            s (str): 原始严重性字符串

        Returns:
            str: 标准严重性(info/low/medium/high/critical)
        """
        val = (s or "").strip().lower()
        if val in {"info", "low", "medium", "high", "critical"}:
            return val
        return "info"

    def _classify_finding_type_from_severity(self, severity: str) -> str:
        """
        基于 severity 映射 finding_type。

        Args:
            severity (str): 标准严重性

        Returns:
            str: "vuln" 或 "asset"
        """
        return "vuln" if severity in {"low", "medium", "high", "critical"} else "asset"

    def _parse_address(self, address: str, service_hint: str) -> Tuple[str, int, str, str]:
        """
        解析 address,返回 (ip, port, protocol, url)。

        规则:
        - 若为 URL:protocol=scheme,ip/port 从 URL 解析,url=原样；
        - 若为 IPv4(:port):protocol="tcp",url=f"{ip}:{port}" 或 ip；
        - 其他:兜底 protocol=service_hint 或 "tcp",url=原样。

        Args:
            address (str): 地址字符串(URL 或 ip(:port) 或其他)
            service_hint (str): 服务类型提示(如 http/tcp),用于兜底

        Returns:
            Tuple[str, Optional[int], str, str]: (ip, port, protocol, url)
        """
        addr = (address or "").strip()

        # URL 情形
        if addr.startswith(("http://", "https://")):
            parsed = urlparse(addr)
            ip = parsed.hostname or ""
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            protocol = parsed.scheme
            url = addr
            return ip, port, protocol, url

        # IPv4(:port) 情形
        m = self._IP_PORT_PATTERN.match(addr)
        if m:
            ip = m.group("ip")
            port_str = m.group("port")
            port = int(port_str) if port_str else 0
            protocol = "tcp"
            url = f"{ip}:{port}" if port is not None else ip
            return ip, port, protocol, url

        # 兜底(未知形态)
        protocol = service_hint or "tcp"
        return "", 0, protocol, addr

    def _clean_info(self, info_raw: Optional[str]) -> str:
        """
        清洗 TXT info 字段；尝试解析为 JSON,或去除外层引号。

        Args:
            info_raw (Optional[str]): 原始 info 文本(可能为 JSON 片段)

        Returns:
            str: 清洗后的文本
        """
        if info_raw is None:
            return ""
        s = info_raw.strip()
        # pylint: disable=broad-exception-caught
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return ", ".join(str(x) for x in parsed)
            if isinstance(parsed, (str, int, float, bool)):
                return str(parsed)
            if isinstance(parsed, dict):
                return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
        except Exception:
            if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
                return s[1:-1]
        # pylint: enable=broad-exception-caught
        return s

    def _extract_product_version(self, info: str, name_hint: str) -> Tuple[str, str]:
        """
        从 info 或 name_hint 中做轻量产品/版本提取；无法识别时返回空串。

        支持:
        1) "prod/ver" 形式(如 gunicorn/19.9.0)
        2) "<prod> Version <ver>" 形式

        Args:
            info (str): 信息文本(通常来自 extracted-results 或 TXT 的 info)
            name_hint (str): 名称文本(如模板/规则名)

        Returns:
            Tuple[str, str]: (product, version)
        """
        text = (info or "").strip()

        m = self._PROD_VER_SLASH.search(text)
        if m:
            prod = m.group("prod").strip().lower()
            ver = m.group("ver").strip()
            return prod, ver

        m = self._VER_WORD_PATTERN.search(text)
        if m:
            prod = m.group("prod").strip().lower()
            ver = m.group("ver").strip()
            return prod, ver

        # 从 name_hint 再尝试一次
        m = self._PROD_VER_SLASH.search(name_hint or "")
        if m:
            prod = m.group("prod").strip().lower()
            ver = m.group("ver").strip()
            return prod, ver

        return "", ""

    def _split_host(self, host: str) -> tuple[str, Optional[int]]:
        """
        拆分 JSON 的 host 字段,兼容 "ip" 或 "ip:port"。

        Args:
            host (str): 例如 "192.168.1.1" 或 "192.168.1.1:8080"

        Returns:
            tuple[str, Optional[int]]: (ip, port)
        """
        if not host:
            return "", None
        s = host.strip()
        m = self._IP_PORT_PATTERN.match(s)
        if m:
            ip = m.group("ip")
            port_str = m.group("port")
            return ip, int(port_str) if port_str else None
        return "", None
