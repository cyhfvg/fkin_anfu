# Changelog

fkin_anfu: "Network Security Automation Toolkit"

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [0.4.2] - 2025-07-17

### Added

- 添加`fscan_parser`工具，解析fscan扫描结果，支持输出xlsx, json格式

## [0.4.1] - 2025-07-17

### Added

- 添加`output_utils`工具，为输出提供统一工具，当前提供FindingResult类型的JSON与XLSX输出
- 修改parse_cmd中FindingResult的输出为统一output_utils工具

## [0.4.0] - 2025-07-13

### Added

- 添加`parse`子命令；解析汇总漏洞扫描工具结果
- 添加`afrog_parser`；劝解解析afrog扫描输出的`json`结果，并能尝试修复afrog输出时可能存在的文件末尾缺少`]`问题
- `afrog_parser`: 能够输出汇总结果,支持`xlsx`与`json`输出格式

## [0.3.1] - 2025-07-09

### Fixed

- 修改版本号错误

## [0.3.0] - 2025-07-09

### Added

- 初始发布 `ip_utils` 模块
- 实现 IPv4 校验、范围解析、C段分组、连续段识别等功能
- 提供统一日志接口 `debug_print`，便于调试和记录异常输入
