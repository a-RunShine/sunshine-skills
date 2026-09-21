# 深度阅读边界

> 决定 Stage 2 哪些文件**必读**、**按需**、**跳过**。

## 必读（每个模块）

- 模块入口文件：`__init__.py` / `index.ts` / `main.go` / `<Module>Application.java` 等
- 模块目录下"看起来核心"的文件（按文件大小 + import 数量排前 3-5 个）
- 跟 manifest 强相关的：`package.json` 的 `main` / `bin`、`pyproject` 的 `[project.scripts]` 等

## 按需读

- 配置文件（yaml / toml / json）— 理解部署和环境
- CI/CD 配置 — 理解测试/部署流程
- Dockerfile / docker-compose — 理解运行时
- 测试文件 — 每个模块读 1-2 个代表性测试

## 跳过（默认不读）

- `node_modules/`、`vendor/`、`dist/`、`build/`、`.venv/`、`__pycache__/`、`target/`、`.git/`
- `*.lock`、`package-lock.json`、`yarn.lock`、`Cargo.lock`
- 生成的代码：`*_pb.go`、`*.gen.ts`、`openapi.json`、`schema.prisma`、`*.graphql`
- 大二进制、`.min.js`、`.map` 文件
- 测试 fixtures（faked data），在看测试结构时才读

## 单模块过大（> 50K 行）

在 dossier 里只描述顶层结构，标 `详见源码`，避免把整个模块的代码强行塞进一份文档。
