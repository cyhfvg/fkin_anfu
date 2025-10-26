# Changelog

fkin_anfu: "Network Security Automation Toolkit"

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [0.6.2] - 2025-10-26

### Fixed

- 修改`help`文档，更人性化

## [0.6.1] - 2025-10-26

### Fixed

- 修改若干 docs 格式问题

## [0.6.0] - 2025-10-26

### Added

- 添加`Nuclei_parser`;支持对 nuclei 的`txt`、`json`类型结果进行解析
- 为`FindingResult`提供 sort_fn 与 merge_fn 等

## [0.5.2] - 2025-10-23

### Fixed

- 为`color_utils`提供的方法将 msg 更改为`Any`类型，避免 IDE 类型检查报警告

## [0.5.1] - 2025-10-22

### Added

- 为`log_utils`的`debug_print(level: str, msg: str)`将 msg 更改为`Any`类型，避免 IDE 类型检查报警告

## [0.5.0] - 2025-10-22

### Added

- 为`ip_utils`的`omni_extend_ip_list`方法添加入参为`Union[str, list[str]]`混合类型的
  版本实现`batch_omni_extend_ip_list`，允许批量 extend_ip

## [0.4.7] - 2025-10-22

### Fixed

- 在`fkin-anfu/cli/main.py`中补充`if __name__ == "__main__"`入口调用，允许直接运行
  `main.py`脚本启动程序
- 修复`fscan_parser`对目录的读取错误

## [0.4.6] - 2025-09-16

### Added

- 在`log_utils`中添加`print_ascii`方法用于输出艺术字
- 移除`ip_utils`中`is_valid_ipv4`方法中的日志输出

## [0.4.5] - 2025-09-16

### Added

- 添加 ip_utils 中`omni_extend_ip_list`,`parse_ip_range`函数对 ip 范围'127.0.0.1-5'格式支持

## [0.4.4] - 2025-08-21

### Fixed

- 修复 fscan_parser 中 doc 字符串显示错误
- 修复 afrog_parser 中 str.lower()方法调用
- 修复 parse_manager 中 颜色序列对字符串处理方法调用位置

## [0.4.3] - 2025-08-20

### Added

- 添加`color_utils`工具类，提供颜色化字符串方法
- 重构`log_utils`

## [0.4.2] - 2025-07-17

### Added

- 添加`fscan_parser`工具，解析 fscan 扫描结果，支持输出 xlsx, json 格式

## [0.4.1] - 2025-07-17

### Added

- 添加`output_utils`工具，为输出提供统一工具，当前提供 FindingResult 类型的 JSON 与 XLSX 输出
- 修改 parse_cmd 中 FindingResult 的输出为统一 output_utils 工具

## [0.4.0] - 2025-07-13

### Added

- 添加`parse`子命令；解析汇总漏洞扫描工具结果
- 添加`afrog_parser`；劝解解析 afrog 扫描输出的`json`结果，并能尝试修复 afrog 输出时可能存在的文件末尾缺少`]`问题
- `afrog_parser`: 能够输出汇总结果,支持`xlsx`与`json`输出格式

## [0.3.1] - 2025-07-09

### Fixed

- 修改版本号错误

## [0.3.0] - 2025-07-09

### Added

- 初始发布 `ip_utils` 模块
- 实现 IPv4 校验、范围解析、C 段分组、连续段识别等功能
- 提供统一日志接口 `debug_print`，便于调试和记录异常输入
