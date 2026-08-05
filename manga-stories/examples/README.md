# Examples · 音乐节 manga v2

这是 `manga-stories` skill 自己的"成功样例库"——本次（2026-08-05）为视频频道
"SunSHINE" / 桑尼 制作的 8 页 manga v2（v1 失败 → v2 重做），用《5.5 音乐节·
我见到了 TB》日记为素材。

## 文件清单

| 文件                          | 角色           | 用途                                       |
| ----------------------------- | -------------- | ------------------------------------------ |
| `anchor-P6样本.png`           | Step 2 样本    | 风格 anchor 阶段输出，确认风格用          |
| `P1-封面.png`                 | 第 1 页        | 封面（"5.5 音乐节·我见到了 TB"）          |
| `P2-早起赶路.png`             | 第 2 页        | 行动页（5/5 早 8 点接驳车）                |
| `P3-第一次听youll-see.png`    | 第 3 页        | 回忆切入（大二暗恋 ayl）                   |
| `P4-暗恋低谷与治愈.png`       | 第 4 页        | 转折（彩色页·apricot 暖色）                |
| `P5-现场到达.png`             | 第 5 页        | 蓄势（铺野餐垫、充气沙发）                 |
| `P6-TB出现.png`               | 第 6 页        | 高潮（彩色页·舞台+剪影）                   |
| `P7-烈日与搭讪.png`           | 第 7 页        | 尴尬+成长                                  |
| `P8-摇滚与圆梦.png`           | 第 8 页        | 圆梦（彩色页·破墙旁白）                    |
| `case-study-brief.md`         | 决策记录       | 完整 6 问 grill + v2 修复记录              |

## 这套样本的价值

### 1. Anchor 验证（Step 2 用）

`anchor-P6样本.png` 是 Step 2 唯一出的图。
- 选择 P6 而不是 P1 是因为 P6 同时考验：人物、格子节奏、彩色、特殊符号（剪影乐队）、caption box
- 通过 P6 anchor 才确定风格 OK 进入批量

### 2. 彩色页选在哪（3 页）

| 彩色页 | 原因                            |
| ------ | ------------------------------- |
| P4     | 转折·低谷→治愈（情绪暖点）      |
| P6     | 高潮·见到 TB（最圆梦的瞬间）    |
| P8     | 圆梦·结尾（破墙旁白）           |

5 张 B&W + 3 张彩色，符合 1-3 页彩色的克制原则。

### 3. Caption Box 修复史

- v1 全部 8 张**没画** caption box（prompt 写得太轻）
- v2 全部 prompt 加 "MANDATORY narrator caption box... DO NOT OMIT"
- v2 batch 出图后**7 张画上了，P3 漏了**
- P3 单张重跑 + prompt 头部加 "CRITICAL" 才解决

→ 这是 anti-patterns.md 里"坑 2"的真实案例。

### 4. 简化人物演化

参考用户原始火柴人 (`production/assets/人物形象/06-火柴人-对话.png`)，
AI 把它演化成"简化漫画人物"（圆头 + dot eyes + 简单身材 + 简单发型）。
- 不是纯火柴人
- 不是完整漫画人物
- 是中间态，**符合 v2 的实际决策**

### 5. TB 怎么处理

真名乐队 Tizzy Bac 不能画真人。
- v2 全部用：舞台 + 灯光 + 3 个剪影 + 简化吉他/鼓符号
- P6 三个剪影背光站立，不画脸、不画名字
- 通过这个处理避免侵权和画走样

### 6. Layout 变化

8 页用了 3+ 种 layout：
- P1 封面：1 大 + 3 小（高潮感）
- P2 行动：横长 + 竖长
- P3 回忆：垂直 4 格（时间流）
- P4 转折：1 大 + 多小
- P5 蓄势：电影宽屏
- P6 高潮：1 大 + 3 小
- P7 尴尬：双格
- P8 圆梦：电影宽屏

→ 不是千篇一律 2×2，符合 anti-patterns.md"坑 1"。

## 怎么用这套样本

### 当作"风格参考图"

下次接到新故事想做 manga 版：

1. 把 `anchor-P6样本.png` 或 `P6-TB出现.png` 作为 reference image 喂给 AI
2. 配合 `references/prompt-template.md` 的 STYLE BLOCK
3. 锁定风格后批量

### 当作"caption 范例"

如果用户不会写 caption，把 `case-study-brief.md` 里的 8 段 caption 给他看，
让他理解"30-60 字、第一人称、内心独白"的节奏。

### 当作"layout 范例"

8 张图对应 8 种不同 layout，下次画之前先想：

- 封面/高潮 → 1 大 + 3 小
- 行动/赶路 → 横长 + 竖长
- 回忆/时间流 → 垂直 4 格
- 蓄势/氛围 → 电影宽屏
- 尴尬/对比 → 双格

## 这次踩过的坑（详见 anti-patterns.md）

1. ❌ v1 没做 anchor 就批量 → 风格重做
2. ❌ v1 prompt 没强调 caption box → 全部漏画
3. ❌ v2 批量 8 张 P3 又漏 → 单张重跑 + CRITICAL 强调
4. ❌ 8 页差点全 2×2 → 显式指定 4 种 layout
5. ❌ TB 差点画真人 → 改成剪影 + 舞台

## 制作人

- 用户：桑尼-SHNIE（@SunSHINE 抖音账号）
- 日期：2026-08-05
- skill 路径：`/Users/sunshine/.claude/skills/manga-stories/`
- 项目路径：`xiaohongshu/5.5_音乐节_我见到了TB/manga/`
