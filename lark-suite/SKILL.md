---
name: lark-suite
version: 1.0.72
description: "通过 lark-cli 操作飞书（消息、文档、云空间、多维表格、电子表格、幻灯片、日历、邮箱、任务、会议、Markdown、考勤、审批、OKR、知识库、通讯录、白板、视频会议、妙记等 26 个业务域）。覆盖飞书全场景，含 200+ 命令与快捷方式。当用户提到飞书/Lark/Feishu 操作，或需要查日程、发消息、写文档、读/写多维表格、建任务、查通讯录、操作云空间、处理妙记会议纪要、提交审批、查询 OKR 等时使用。"
metadata:
  category: "productivity"
  requires:
    bins: ["lark-cli"]
  cliHelp: "lark-cli --help"
---

# 飞书全功能 Skill（lark-suite）

你是 AI Agent，通过 `lark-cli` 命令操作飞书资源。**所有业务域操作前，必须先用 Read 工具读取 [`skills/lark-shared/SKILL.md`](skills/lark-shared/SKILL.md)**，里面包含：
- 应用凭证配置（`config init` / `config init --new`）
- 用户身份 vs Bot 身份选择
- OAuth 授权（`auth login --recommend` / `--no-wait --json`）
- 业务域权限范围（`--domain all/docs/drive/im/...`）
- 权限缺失处理（看 `console_url` 引导用户去开发者后台）
- 登录态查询（`auth status --json --verify` / `whoami`）
- 退出与撤销授权（`auth logout`）
- `_notice` JSON 提示处理（更新提示、技能同步提示）

## 26 个业务域索引

按用户需求，先读对应业务域的 `SKILL.md` 学习具体能力和命令格式：

| # | 业务域 | SKILL.md 路径 | 主要能力 |
|---|---|---|---|
| 1 | 消息 IM | `skills/lark-im/SKILL.md` | 发/收消息、群聊管理、消息搜索、表情反应、上传下载媒体 |
| 2 | 文档 Doc | `skills/lark-doc/SKILL.md` | 创建/读取/更新/搜索文档 |
| 3 | 云空间 Drive | `skills/lark-drive/SKILL.md` | 上传/下载文件、权限与评论管理 |
| 4 | Markdown | `skills/lark-markdown/SKILL.md` | 创建/读取/patch/覆盖 Drive 原生 `.md` 文件 |
| 5 | 多维表格 Base | `skills/lark-base/SKILL.md` | 数据表/字段/记录/视图/仪表盘/自动化/表单/权限 |
| 6 | 电子表格 Sheets | `skills/lark-sheets/SKILL.md` | 创建/读/写/追加/查找/导出表格 |
| 7 | 幻灯片 Slides | `skills/lark-slides/SKILL.md` | 创建/管理演示文稿、增删页面 |
| 8 | 日历 Calendar | `skills/lark-calendar/SKILL.md` | 日程 CRUD、议程、忙闲、会议室、邀请回复 |
| 9 | 邮件 Mail | `skills/lark-mail/SKILL.md` | 浏览/搜索/阅读/发送/回复/转发/草稿/监听新邮件 |
| 10 | 任务 Task | `skills/lark-task/SKILL.md` | 任务/清单/子任务/提醒/成员/附件 |
| 11 | 知识库 Wiki | `skills/lark-wiki/SKILL.md` | 知识空间/节点/文档层级 |
| 12 | 通讯录 Contact | `skills/lark-contact/SKILL.md` | 按姓名/邮箱/手机号搜索用户、获取用户信息 |
| 13 | 视频会议 VC | `skills/lark-vc/SKILL.md` | 搜索会议、查询纪要和录制 |
| 14 | 妙记 Minutes | `skills/lark-minutes/SKILL.md` | 妙记搜索、音视频下载、总结与待办提取 |
| 15 | 审批 Approval | `skills/lark-approval/SKILL.md` | 查询/同意/拒绝/转交审批、撤回/抄送 |
| 16 | 考勤 Attendance | `skills/lark-attendance/SKILL.md` | 查询个人考勤打卡记录 |
| 17 | OKR | `skills/lark-okr/SKILL.md` | 查询/创建/更新 OKR 与关键结果 |
| 18 | 白板 Whiteboard | `skills/lark-whiteboard/SKILL.md` | 读取/导出/用 DSL/PlantUML/Mermaid 更新白板 |
| 19 | 笔记 Note | `skills/lark-note/SKILL.md` | 飞书便签 |
| 20 | 妙搭 Apps | `skills/lark-apps/SKILL.md` | 创建妙搭应用、发布 HTML/静态站点 |
| 21 | Event | `skills/lark-event/SKILL.md` | 事件订阅管理 |
| 22 | OpenAPI Explorer | `skills/lark-openapi-explorer/SKILL.md` | 浏览开放平台 API |
| 23 | Skill Maker | `skills/lark-skill-maker/SKILL.md` | 创建自定义 Skill |
| 24 | VC Agent | `skills/lark-vc-agent/SKILL.md` | 视频会议智能体 |
| 25 | 工作流-会议纪要 | `skills/lark-workflow-meeting-summary/SKILL.md` | 会议纪要工作流 |
| 26 | 工作流-站会报告 | `skills/lark-workflow-standup-report/SKILL.md` | 站会报告工作流 |

## 命令三层架构

```bash
# 第一层：快捷命令（人类与 Agent 友好，带智能默认值，+ 前缀）
lark-cli <service> +<shortcut> [flags]
# 例：lark-cli im +messages-send --chat-id oc_xxx --text "hello"

# 第二层：API 命令（飞书开放平台 API 1:1 映射）
lark-cli <service> <resource> <method> [flags]

# 第三层：原始 API 调用（覆盖全 API）
lark-cli schema <service>.<resource>.<method>   # 调用前先看参数结构
lark-cli <service> <resource> <method> --params '<json>' --data '<json>'
```

## 命令探索

```bash
lark-cli --help                                  # 所有顶层命令
lark-cli <service> --help                       # 某个 service 的资源和命令
lark-cli schema <service>.<resource>.<method>   # 调原生 API 前必看参数结构
```

## 本环境特殊说明

- CLI 已装在：`/Users/sunshine/Desktop/OH-WorkSpace/.lark-cli-prefix/bin/lark-cli`
- 调用方式二选一：
  - 绝对路径：`/Users/sunshine/Desktop/OH-WorkSpace/.lark-cli-prefix/bin/lark-cli --version`
  - 或在 shell 里 `export PATH="$PWD/.lark-cli-prefix/bin:$PATH"` 后直接 `lark-cli ...`
- 首次使用前必须先做：
  1. `lark-cli config init --new` —— 创建应用（需用户在浏览器完成授权）
  2. `lark-cli auth login --recommend` —— 登录授权
  3. `lark-cli auth status` —— 验证登录态

详细流程见 `skills/lark-shared/SKILL.md`。