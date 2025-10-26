# -*- coding: utf-8 -*-
"""
FindingResult 辅助方法测试
- canonicalize_url：规范化、补端口、排序去重 query
- build_canonical_key / canonical_key：稳定 key 构建
- deduplicate：去重与合并策略（严重性、title、raw_path、extra 等）
"""
from __future__ import annotations

from typing import List

from fkin_anfu.parsers.models.finding_result import FindingResult


def test_canonicalize_url_default_ports_and_query_sort() -> None:
    """
    验证 URL 规范化：
    - http/https 默认端口补齐
    - query 排序并去重（同 key 仅保留首次）
    """
    u1 = "http://1.2.3.4/a?c=2&b=1&b=1"
    u2 = "http://1.2.3.4:80/a?b=1&c=2"

    cu1 = FindingResult.canonicalize_url(u1)
    cu2 = FindingResult.canonicalize_url(u2)

    # 输出样例：'http://1.2.3.4:80/a?b=1&c=2'
    assert cu1 == cu2
    assert cu1 == "http://1.2.3.4:80/a?b=1&c=2"


def test_build_canonical_key_without_url() -> None:
    """
    无 URL 时，使用 protocol/service + ip + port + name 构建 key。
    """
    k1 = FindingResult.build_canonical_key(
        url="",
        name="SSH-Banner",
        ip="10.0.0.1",
        port=22,
        protocol="tcp",
        service="ssh",
    )
    k2 = FindingResult.build_canonical_key(
        url="",
        name="ssh-banner",
        ip="10.0.0.1",
        port=22,
        protocol="tcp",
        service="ssh",
    )
    assert k1 == k2  # 名称大小写不敏感
    # 输出样例：'host|ssh-banner|tcp|10.0.0.1|22'
    assert k1.endswith("|10.0.0.1|22")


def test_deduplicate_merge_severity_title_raw_path_extra() -> None:
    """
    验证 deduplicate 的默认合并策略：
    - 严重性取更高
    - 标题信息量更大者优先
    - raw_path 合并去重
    - extra 浅合并（old 优先）
    """
    a = FindingResult(
        url="http://1.2.3.4/a?b=1&c=2",
        name="Jetty-Detect",
        severity="low",
        title="Jetty",
        raw_path="a.txt",
        extra={"k": "v1"},
    )
    b = FindingResult(
        url="http://1.2.3.4:80/a?c=2&b=1",
        name="jetty-detect",
        severity="medium",
        title="Jetty(9.4.26) Detected",
        raw_path="b.json",
        extra={"k": "v1", "k2": "v2"},
    )

    merged: List[FindingResult] = FindingResult.deduplicate([a, b])
    assert len(merged) == 1
    r = merged[0]
    # 严重性取更高：输出样例 'medium'
    assert r.severity == "medium"
    # URL 规范化：输出样例 'http://1.2.3.4:80/a?b=1&c=2'
    assert r.url == "http://1.2.3.4:80/a?b=1&c=2"
    # 标题更长者优先：输出样例 'Jetty(9.4.26) Detected'
    assert r.title == "Jetty(9.4.26) Detected"
    # raw_path 合并：输出样例 'a.txt,b.json' 或 'b.json,a.txt'
    assert "a.txt" in r.raw_path and "b.json" in r.raw_path
    # extra 浅合并：保留 old.k='v1'，补充 k2
    assert r.extra.get("k") == "v1" and r.extra.get("k2") == "v2"


def test_deduplicate_host_key_without_url() -> None:
    """
    无 URL 的主机类发现去重：使用 host key（proto/service + ip + port + name）
    """
    x = FindingResult(
        ip="10.0.0.1",
        port=22,
        protocol="tcp",
        service="ssh",
        name="SSH-Banner",
        severity="info",
        raw_path="r1.txt",
    )
    y = FindingResult(
        ip="10.0.0.1",
        port=22,
        protocol="tcp",
        service="ssh",
        name="ssh-banner",
        severity="high",
        banner="OpenSSH_8.9",
        raw_path="r2.txt",
    )

    merged = FindingResult.deduplicate([x, y])
    assert len(merged) == 1
    r = merged[0]
    # 严重性提升到 'high'
    assert r.severity == "high"
    # banner 被补齐
    assert r.banner == "OpenSSH_8.9"
    # raw_path 合并
    assert "r1.txt" in r.raw_path and "r2.txt" in r.raw_path


def test_deduplicate_with_custom_key_fn_url_only() -> None:
    """
    进阶：若你希望忽略 name，仅按 URL 去重，可自定义 key_fn。
    说明：默认实现包含 name + url，不同 name 不会合并；此示例展示如何覆盖策略。
    """
    a = FindingResult(url="http://1.2.3.4/x", name="A", raw_path="a.txt")
    b = FindingResult(url="http://1.2.3.4:80/x", name="B", raw_path="b.json")

    def key_fn_url_only(r: FindingResult) -> str:
        # 仅用规范化 URL 作为 key（忽略 name）
        return "u|" + FindingResult.canonicalize_url(r.url)

    merged = FindingResult.deduplicate([a, b], key_fn=key_fn_url_only)
    assert len(merged) == 1
    r = merged[0]
    # 输出样例：url 规范化后 'http://1.2.3.4:80/x'
    assert r.url == "http://1.2.3.4:80/x"
    # raw_path 合并
    assert "a.txt" in r.raw_path and "b.json" in r.raw_path
