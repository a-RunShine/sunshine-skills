# 模块识别规则（按语言习惯）

> "模块"在不同语言/项目里有不同定义。这里给 language-specific 的指引，**主 skill Stage 1.3 用**。

## Node / TypeScript

- 顶层 `packages/<name>/`、`apps/<name>/`、`src/modules/<name>/` → 每个=模块
- 单 `src/` 目录：按 `src/<subdir>` 切，**切 ≥ 3 个文件的子目录**（小于 3 个的并入父目录）

## Python

- `src/<package>/`、`<package>/`（顶级包）、`app/`（Django/Flask）、`services/`、`workers/` → 每个=模块
- 单文件脚本（`scripts/*.py`）→ 不单独算模块，归到 `scripts/`

## Go

- `cmd/<binary>/`（入口二进制）→ 每个=模块
- `internal/<package>/`、`pkg/<package>/` → 按包切
- `internal/` 整体可算一个"业务核心"模块，看大小定

## Java / Kotlin

- Maven multi-module → 每个 `<module>` 算
- 单 module 按 `src/main/java/<basepackage>/<sub>` 切

## Rust

- `crates/<name>/`、`src/bin/<name>.rs` → 每个=模块
- 单 crate 按 `src/<mod>.rs` 切

## 通用兜底

- 第一级有意义的目录（**跳过列表见 `references/depth-boundaries.md` 的 §跳过 段**）→ 候选模块
- 单文件项目 → 整个项目= 1 个模块，名字用项目名
