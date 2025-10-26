#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
定义 FindingResult 数据结构，用于统一表示漏洞信息或资产识别结果。
字段涵盖五大类：网络定位、服务信息、识别内容、责任归属、元信息。
此模型适用于解析阶段标准化结构，并可用于后续输出或合并处理。

@author: cyhfvg
@date: 2025/07/10
"""
from __future__ import annotations

from typing import Any, Callable, ClassVar, Dict, Iterable, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import BaseModel, Field


class FindingResult(BaseModel):
    """
    标准化的扫描发现结构; Parser 产出该结构，后续可直接用于导出/展示/合并。
    同时在模型内提供“稳定去重”能力
    """

    # ========= 类常量 =========
    _DEFAULT_PORTS: ClassVar[Dict[str, int]] = {"http": 80, "https": 443}
    _SEVERITY_RANK: ClassVar[Dict[str, int]] = {"info": 0, "low": 100, "medium": 200, "high": 300, "critical": 400}

    # ========= 网络定位 =========
    ip: str = Field(default="", description="IP地址或域名")
    port: int = Field(default=0, description="端口号")
    protocol: str = Field(default="", description="协议类型, 如 http、https、tcp")
    url: str = Field(default="", description="完整访问 URL, 如 http://1.1.1.1:8080/path")

    # ========= 服务识别 =========
    service: str = Field(default="", description="服务类型, 如 http、ssh")
    product: str = Field(default="", description="服务软件名, 如 nginx、tomcat")
    version: str = Field(default="", description="软件版本信息")
    banner: str = Field(default="", description="指纹特征或响应头信息")

    # ========= 识别内容 =========
    finding_type: str = Field(default="", description="识别类型:vuln(漏洞)或 asset(资产)")
    name: str = Field(default="", description="漏洞名或资产特征名")
    title: str = Field(default="", description="页面标题或结果摘要")
    severity: str = Field(default="", description="严重等级, 如 high、medium、low、info")
    cve_id: str = Field(default="", description="CVE 编号（如有）")

    # ========= 责任归属 =========
    org_unit: str = Field(default="", description="所属单位")
    department: str = Field(default="", description="所属部门")
    business_system: str = Field(default="", description="所属业务系统名称")
    owner: str = Field(default="", description="资产负责人")
    source_origin: str = Field(default="", description="归属来源, 如 资产管理平台、资产表、手动确认等")

    # ========= 元信息 =========
    source_tool: str = Field(default="", description="来源工具名，如 afrog、nuclei")
    raw_path: str = Field(default="", description="原始扫描结果文件名")
    extra: Dict[str, Any] = Field(default_factory=dict, description="附加字段信息,预留扩展用")

    @staticmethod
    def severity_rank(severity: str) -> int:
        """
        将严重性字符串映射为数字等级，返回值越大表示严重性越高。
        Args:
            severity (str): 严重性，如 info/low/medium/high/critical
        Returns:
            int: 数值等级
        """
        return FindingResult._SEVERITY_RANK.get((severity or "").lower(), 0)

    @staticmethod
    def canonicalize_url(url: str) -> str:
        """
        规范化 URL(作为去重与比较的基础):
        - 小写 scheme/host
        - 明确端口(默认 http=80, https=443)
        - 去除 fragment
        - path 为空时设为 '/'
        - query 排序与去重（同 key 仅保留首次）
        兼容性：仅用 urllib.parse 基本能力，适配 Python 3.8。
        """
        if not url:
            return ""
        # pylint: disable=broad-exception-caught
        try:
            parsed = urlparse(url)

            scheme = (parsed.scheme or "").lower()
            host = (parsed.hostname or "").lower()
            port = parsed.port
            if port is None and scheme in FindingResult._DEFAULT_PORTS and host:
                port = FindingResult._DEFAULT_PORTS[scheme]

            # 规整 netloc：若无法解析 hostname，则维持原 netloc（尽量不丢信息）
            if host:
                netloc = host if port is None else f"{host}:{port}"
            else:
                netloc = parsed.netloc

            path = parsed.path or "/"

            # query 去重并按 key 排序
            if parsed.query:
                kvs = parse_qsl(parsed.query, keep_blank_values=True)
                dedup = {}  # type: Dict[str, str]
                for k, v in kvs:
                    if k not in dedup:
                        dedup[k] = v
                query = urlencode(sorted(dedup.items(), key=lambda x: x[0]))
            else:
                query = ""

            # 移除 fragment
            return urlunparse((scheme, netloc, path, "", query, ""))
        except Exception:
            return url
        # pylint: enable=broad-exception-caught

    @staticmethod
    def build_canonical_key(
        url: str = "",
        name: str = "",
        ip: str = "",
        port: Optional[int] = None,
        protocol: str = "",
        service: str = "",
    ) -> str:
        """
        构建稳定去重 Key。
        优先: 规范化URL + name(小写)
        退化: protocol/service + ip + port + name(小写, port 缺失用 -1)
        """
        name_norm = (name or "").strip().lower()
        if url:
            cu = FindingResult.canonicalize_url(url)
            return f"url|{name_norm}|{cu}"

        proto = (protocol or service or "tcp").strip().lower()
        ip_norm = (ip or "").strip().lower()
        port_norm = port if (isinstance(port, int) and port > 0) else -1
        return f"host|{name_norm}|{proto}|{ip_norm}|{port_norm}"

    def canonical_key(self) -> str:
        """
        基于当前对象生成稳定的去重 Key。
        Returns:
            str: 稳定 key
        """
        return FindingResult.build_canonical_key(
            url=self.url or "",
            name=self.name or "",
            ip=self.ip or "",
            port=self.port,
            protocol=self.protocol or "",
            service=self.service or "",
        )

    @staticmethod
    def _merge_default(old: FindingResult, new: FindingResult) -> FindingResult:
        """
        默认合并策略：将 new 的有效信息融合进 old(原地修改 old 并返回 old)。
        规则：
          1) 严重性取更高(critical > high > medium > low > info)
          2) 字段补齐: old 为空/默认时，用 new 的非空值补（见代码 attr 列表）
          3) 端口补齐: old.port==0 时用 new.port
          4) 标题优选: 长度更长者（视为信息量更大）
          5) raw_path 合并: 逗号拼接并去重（保序）
          6) extra 浅合并: 仅当 old.extra 不含该 key 时，补充 new.extra
          7) source_tool: 默认保留 old
          8) url: 规范化url
        """
        # 1) 严重性更高优先
        if FindingResult.severity_rank(new.severity) > FindingResult.severity_rank(old.severity):
            old.severity = new.severity

        # 2) 基本字段补齐（仅 old 为空或默认时才补）
        def fill(attr):
            ov = getattr(old, attr, None)
            nv = getattr(new, attr, None)
            if (ov is None) or (isinstance(ov, str) and ov.strip() == ""):
                if nv not in (None, ""):
                    setattr(old, attr, nv)

        for attr in (
            "ip",
            "protocol",
            "service",
            "product",
            "version",
            "banner",
            "cve_id",
            "org_unit",
            "department",
            "business_system",
            "owner",
            "source_origin",
        ):
            fill(attr)

        # 3) 端口
        if (not isinstance(old.port, int) or old.port == 0) and isinstance(new.port, int) and new.port > 0:
            old.port = new.port

        # 4) 标题长度优先
        old_title = (old.title or "").strip()
        new_title = (new.title or "").strip()
        if len(new_title) > len(old_title):
            old.title = new_title

        # 5) raw_path 合并去重
        if old.raw_path or new.raw_path:
            seen = set()
            merged = []
            for part in (old.raw_path or "").split(","):
                p = part.strip()
                if p and p not in seen:
                    seen.add(p)
                    merged.append(p)
            for part in (new.raw_path or "").split(","):
                p = part.strip()
                if p and p not in seen:
                    seen.add(p)
                    merged.append(p)
            old.raw_path = ",".join(merged)

        # 6) extra 浅合并(old 优先）
        if isinstance(new.extra, dict):
            if not isinstance(old.extra, dict):
                old.extra = {}
            for k, v in new.extra.items():
                if k not in old.extra:
                    old.extra[k] = v

        # 7) source_tool 合并
        if new.source_tool:
            tools = [t for t in (old.source_tool + "," + new.source_tool).split(",") if t]
            # 去重保序
            dedup = []
            seen_t = set()
            for t in tools:
                ts = t.strip()
                if ts and ts not in seen_t:
                    seen_t.add(ts)
                    dedup.append(ts)
            old.source_tool = ",".join(dedup)

        # 8) url规范化
        old.url = FindingResult.canonicalize_url(old.url)
        return old

    @staticmethod
    def deduplicate(
        results: Iterable[FindingResult],
        key_fn: Optional[Callable[[FindingResult], str]] = None,
        merge_fn: Optional[Callable[[FindingResult, FindingResult], FindingResult]] = None,
    ):
        """
        对 FindingResult 序列进行稳定去重与合并(保持首现顺序)。

        Args:
            results: Iterable[FindingResult] 待去重序列
            key_fn: (可选) 生成去重 Key 的函数；默认使用实例的 canonical_key()
            merge_fn: (可选) 合并策略；默认使用 _merge_default

        Returns:
            List[FindingResult]: 去重合并后的列表
        """
        # 使用默认策略（3.8 兼容写法）
        if key_fn is None:

            def temp_key_fn(r: FindingResult) -> str:
                return r.canonical_key()

            key_fn = temp_key_fn
        if merge_fn is None:
            merge_fn = FindingResult._merge_default

        mapping = {}  # type: Dict[str, FindingResult]
        ordered_keys = []  # type: list[str]

        for item in results:
            # pylint: disable=broad-exception-caught
            try:
                k = key_fn(item)
            except Exception:
                # 兜底 key：避免异常导致流程中断
                k = f"fallback|{item.name}|{item.ip}|{item.port}"
            # pylint: enable=broad-exception-caught

            if k in mapping:
                mapping[k] = merge_fn(mapping[k], item)
            else:
                mapping[k] = item
                ordered_keys.append(k)

        return [mapping[k] for k in ordered_keys]
