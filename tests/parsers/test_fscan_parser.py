#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
测试： fscan_parser

@author: cyhfvg
@date: 2025/07/17
"""
import pytest

from fkin_anfu.parsers.fscan_parser import FscanParser
from fkin_anfu.parsers.models.finding_result import FindingResult


@pytest.fixture
def parser() -> FscanParser:
    return FscanParser()


@pytest.mark.parametrize(
    "line, expected",
    [
        ("192.168.1.10:22 open", {"ip": "192.168.1.10", "port": 22, "finding_type": "asset", "name": "端口开放"}),
        (
            "[*] WebTitle http://192.168.1.20:8080 code:200 len:1234 title:Apache Tomcat/8.5.93",
            {
                "ip": "192.168.1.20",
                "port": 8080,
                "protocol": "http",
                "service": "http",
                "name": "web服务开放",
                "product": "tomcat",
                "version": "8.5.93",
                "title": "Apache Tomcat/8.5.93",
            },
        ),
        (
            "[+] PocScan http://192.168.1.30:7001/_async poc-yaml-weblogic-unauth-rce",
            {
                "ip": "192.168.1.30",
                "port": 7001,
                "protocol": "http",
                "name": "poc-yaml-weblogic-unauth-rce",
                "finding_type": "vuln",
                "severity": "high",
                "title": "weblogic-unauth-rce",
            },
        ),
        (
            "[+] InfoScan http://192.168.1.40:8000/swagger [Swagger UI]",
            {
                "ip": "192.168.1.40",
                "port": 8000,
                "name": "资产识别Swagger UI",
                "title": "Swagger UI",
                "finding_type": "asset",
            },
        ),
        (
            "[+] ftp 192.168.1.50:21 admin 123456",
            {
                "ip": "192.168.1.50",
                "port": 21,
                "protocol": "tcp",
                "service": "ftp",
                "finding_type": "vuln",
                "name": "ftp口令 admin / 123456",
                "severity": "high",
            },
        ),
        (
            "[+] Redis 192.168.1.60:6379 unauthorized file:/data/dump.rdb",
            {
                "ip": "192.168.1.60",
                "port": 6379,
                "protocol": "tcp",
                "service": "redis",
                "finding_type": "vuln",
                "name": "Redis unauthorized",
                "severity": "high",
            },
        ),
    ],
)
def test_parse_line_variants(parser: FscanParser, line: str, expected: dict) -> None:
    """
    覆盖 fscan 五大类型分支行的解析逻辑，验证字段提取正确性
    """
    result = parser._parse_line(line=line, raw_path="mock.txt")
    assert isinstance(result, FindingResult)

    for field, value in expected.items():
        actual = getattr(result, field)
        assert actual == value, f"Mismatch field `{field}`: expected={value}, actual={actual}"
