# sunshine-skills

个人收集的 Claude Code Skills 集合，覆盖文档处理、设计、办公、网页抓取等常见场景。

## 包含的 Skills

| Skill | 说明 |
|---|---|
| [claude-skill-find-skill](./claude-skill-find-skill/) | Claude Code Skills 的发现与安装工具 |
| [find-skill](./find-skill/) | 从 14 个源（按 GitHub stars 排序）查找并安装 Skills |
| [frontend-design](./frontend-design/) | 前端设计指导：避免模板化、做出有辨识度的视觉 |
| [md-pdf](./md-pdf/) | Markdown → PDF 渲染（4 套主题、CJK/Latin/数学符号字体路由） |
| [officecli](./officecli/) | `.docx` / `.xlsx` / `.pptx` 的 AI 友好 CLI（无需 Office） |
| [opencli-usage](./opencli-usage/) | OpenCLI 工具总览：把任意网站/CLI 统一为 `opencli <site> <cmd>` |
| [pdf](./pdf/) | PDF 读写、合并、拆分、表单填写、加密、OCR |
| [skill-creator](./skill-creator/) | 创建并迭代改进 Skills 的工作流（含评测） |
| [web-design-guidelines](./web-design-guidelines/) | 按 Web Interface Guidelines 审查 UI 代码 |
| [xiaohongshu-cli](./xiaohongshu-cli/) | 小红书 CLI：搜索、阅读、点赞、评论、关注、发布 |

## 添加方式

```bash
# 把整个目录复制到 Claude Code 的 skills 路径下
cp -r <skill-name> ~/.claude/skills/

# 或在 Claude Code 中通过 find-skill 直接搜索安装
```

## License

各 skill 遵循其自带的 LICENSE / license 字段（见各子目录）。

---

> ⚠️ 注意：`claude-skill-find-skill/` 与 `find-skill/` 是历史原因留下的同名重复副本，尚未合并。
