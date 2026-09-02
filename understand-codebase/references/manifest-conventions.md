# Manifest → language/framework 识别表

Stage 1 扫项目时用——看到某个 manifest 就知道是哪种语言/框架。

| Manifest 命中 | 推断语言/框架 | 进一步查框架的方法 |
|---|---|---|
| `package.json` | Node / TS / JS | 读 `dependencies` + `scripts` 字段 |
| `pyproject.toml` / `setup.py` / `requirements.txt` | Python | 读 `[project]` + `dependencies` |
| `go.mod` | Go | 读 module path + 顶层 package |
| `Cargo.toml` | Rust | 读 `[dependencies]` |
| `pom.xml` / `build.gradle` | Java / Kotlin | 读 `<artifactId>` + dependencies |
| `*.csproj` / `*.sln` | C# / .NET | |
| `pubspec.yaml` | Dart / Flutter | |
| `composer.json` | PHP | |
| `Gemfile` | Ruby | |
| `Mix.exs` | Elixir | |
| 多个 manifest 都有 | monorepo / polyglot | 按目录分组处理 |
| 都没有 | 不是代码项目 | 走 SKILL.md 的 Failure handling 表格 |
