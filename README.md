# sunshine-skills

<p align="left">
  <a href="https://github.com/a-RunShine/sunshine-skills/stargazers"><img src="https://img.shields.io/github/stars/a-RunShine/sunshine-skills?style=for-the-badge&logo=github&logoColor=white&color=4c1" alt="Stars"></a>
  <a href="https://github.com/a-RunShine/sunshine-skills/network/members"><img src="https://img.shields.io/github/forks/a-RunShine/sunshine-skills?style=for-the-badge&logo=github&logoColor=white&color=4c1" alt="Forks"></a>
  <a href="https://github.com/a-RunShine/sunshine-skills/issues"><img src="https://img.shields.io/github/issues/a-RunShine/sunshine-skills?style=for-the-badge&logo=github&logoColor=white&color=4c1" alt="Issues"></a>
  <a href="https://github.com/a-RunShine/sunshine-skills/commits/master"><img src="https://img.shields.io/github/last-commit/a-RunShine/sunshine-skills?style=for-the-badge&logo=git&logoColor=white&color=4c1" alt="Last Commit"></a>
  <a href="https://github.com/a-RunShine/sunshine-skills"><img src="https://img.shields.io/github/repo-size/a-RunShine/sunshine-skills?style=for-the-badge&logo=github&logoColor=white&color=4c1" alt="Repo Size"></a>
  <a href="https://github.com/a-RunShine/sunshine-skills"><img src="https://img.shields.io/github/languages/top/a-RunShine/sunshine-skills?style=for-the-badge&logo=python&logoColor=white&color=3776AB" alt="Top Language"></a>
  <a href="https://github.com/a-RunShine/sunshine-skills"><img src="https://img.shields.io/github/languages/count/a-RunShine/sunshine-skills?style=for-the-badge&logo=github&logoColor=white&color=4c1" alt="Languages"></a>
</p>

个人收集的 Claude Code Skills 集合，覆盖文档处理、设计、办公、网页抓取等常见场景。

## 包含的 Skills

| Skill | 说明 |
|---|---|
| [code-review](./practical/code-review/) | "Review the changes since a fixed point (commit, branch, tag… |
| [domain-modeling](./practical/domain-modeling/) | Build and sharpen a project's domain model. Use when discuss… |
| [eli5](./practical/eli5/) | "Explain a topic like I'm 5 year old. Use when the user typ… |
| [find-skill](./practical/find-skill/) | "Finds and installs agent skills when they ask questions li… |
| [frontend-design](./practical/frontend-design/) | "Guidance for distinctive, intentional visual design when bu… |
| [gc-minimal-zine-poster-v0-1](./for-fun/gc-minimal-zine-poster-v0-1/) | "Generate Minimal Zine Poster v0.1 poetic paper-poster prompt… |
| [grill-me](./practical/grill-me/) | "A relentless interview to sharpen a plan or design." |
| [grill-with-docs](./practical/grill-with-docs/) | "A relentless interview to sharpen a plan or design, which al… |
| [grilling](./practical/grilling/) | "Grill the user relentlessly about a plan, decision, or idea.… |
| [handoff](./practical/handoff/) | "Compact the current conversation into a handoff document for… |
| [humanizer-zh](./practical/humanizer-zh/) | 去除文本中的 AI 生成痕迹。适用于编辑或审阅文本，使其听起来更自然、更像人类书写。 |
| [implement](./practical/implement/) | "Implement a piece of work based on a spec or set of tickets… |
| [improve-codebase-architecture](./practical/improve-codebase-architecture/) | "Scan a codebase for deepening opportunities, present them as… |
| [lark-suite](./lark-suite/) | "通过 lark-cli 操作飞书（消息、文档、云空间、多维表格… |
| [manga-stories](./for-fun/manga-stories/) | Generate a vertical (3:4) Japanese-manga style image set… |
| [officecli](./practical/officecli/) | "Create, analyze, proofread, and modify Office documents… |
| [oil-icon](./practical/oil-icon/) | "Generate a cohesive set of transparent-background icons… |
| [pdf](./practical/pdf/) | "Use this skill whenever the user wants to do anything with P… |
| [research](./practical/research/) | "Investigate a question against high-trust primary sources an… |
| [scenes-gathered-zine-v1-3](./for-fun/scenes-gathered-zine-v1-3/) | "Transform a user-supplied photo into a vertical 3:5 Gathere… |
| [skill-creator](./practical/skill-creator/) | "Create new skills, modify and improve existing skills, and m… |
| [sunshine-spec](./practical/sunshine-spec/) | "Spec 驱动开发：通过协作式需求澄清，依次生成 spec.md → plan.md… |
| [tdd](./practical/tdd/) | "Test-driven development. Use when the user wants to build fe… |
| [teach](./practical/teach/) | "Teach the user a new skill or concept, within this workspace… |
| [theme-factory](./practical/theme-factory/) | "Toolkit for styling artifacts with a theme. These artifacts c… |
| [understand-codebase](./practical/understand-codebase/) | "Blueprint an unfamiliar codebase. Triggers: "分析这个项目"… |
| [web-artifacts-builder](./practical/web-artifacts-builder/) | "Suite of tools for creating elaborate, multi-component claud… |
| [web-design-guidelines](./practical/web-design-guidelines/) | "Review UI code for Web Interface Guidelines compliance. Use w… |
| [writing-great-skills](./practical/writing-great-skills/) | "Reference for writing and editing skills well — the vocabula… |
| [xiaohongshu-cli](./for-fun/xiaohongshu-cli/) | "Use xiaohongshu-cli for ALL Xiaohongshu (Little Red Book, 小红… |
| [xiaohongshu-image-batch](./for-fun/xiaohongshu-image-batch/) | 从原始素材或主题，批量制作小红书图文内容（3:4 竖版，6-8 张为一组）… |



## 添加方式

```bash
# 把整个目录复制到 Claude Code 的 skills 路径下
cp -r <skill-name> ~/.claude/skills/

# 或在 Claude Code 中通过 find-skill 直接搜索安装
```

## License

各 skill 遵循其自带的 LICENSE / license 字段（见各子目录）。

---

> ⚠️ 注意：`find-skill/` 内的 `agents/openai.yaml` 来自原 `claude-skill-find-skill/`，合并前先保留以备回退。
