# 墨墨开放 API 索引

> 2026-08-03 验证。Base URL: `https://open.maimemo.com/open/api/v1`
>
> 鉴权 token: `Bearer <MAIMEMO_TOKEN>`，存于 `./.claude/skills/memo-context/.env`

## 资源索引

| 资源组 | 详情文件 | 端点数 | 用途 | memo-context 用到？ |
|---|---|---|---|---|
| 学习数据（公测） | [study.md](./study.md) | 5 | 学习记录/今日清单/进度/加词/提前复习 | ✅ Step 1 主入口 |
| 单词 | [vocabulary.md](./vocabulary.md) | 2 | 按拼写/批量查单词 | 🔶 备用（确认 voc_id） |
| 释义 | [interpretations.md](./interpretations.md) | 4 | 自定义释义 CRUD | 🔶 备用（写词时附加） |
| 例句 | [phrases.md](./phrases.md) | 4 | 例句 CRUD | 🔶 备用 |
| 助记 | [notes.md](./notes.md) | 4 | 助记 CRUD | 🔶 备用 |
| 云词本 | [notepads.md](./notepads.md) | 5 | 云词本 CRUD | ✅ Step 6 回灌 |
| 记忆卡 | [markji.md](./markji.md) | 10 | 牌组/章节/卡片/文件 | ❌ 暂不用 |

## 鉴权 + 限流

```
Authorization: Bearer <MAIMEMO_TOKEN>
Content-Type: application/json
```

**Token 位置：** `./.claude/skills/memo-context/.env` 的 `MAIMEMO_TOKEN` 字段（项目本地，不外传）。

**401 =** token 失效或 scope 不全 → 提示用户去墨墨 App 重新生成。

**限流：**
- 墨墨背单词：10s/20req，60s/40req，5h/2000req
- 墨墨记忆卡：5h/8000req（独立额度池）
- memo-context 每天 1-3 篇内容不会撞限流；批量场景每篇之间 sleep 几秒

**公测 vs 正式：** 学习数据组 5 个端点都是 `beta: true`（公测），其它 6 组是正式。公测端点可能调整，正式端点稳定。

## 字段枚举速查

### `last_response`（study_records / today_items）
| 值 | 含义 |
|---|---|
| `FAMILIAR` | 认识 |
| `VAGUE` | 模糊（犹豫）|
| `FORGET` | 忘记 |
| `WELL_FAMILIAR` | 熟知 |
| `CANCEL_WELL_FAMILIAR` | 取消熟知 |

### `tags`（study_records）
| 值 | 含义 |
|---|---|
| `STICKING` | 难记 |
| `WELL_FAMILIAR` | 熟知 |

### `status`（释义 / 例句 / 助记 / 云词本）
| 值 | 含义 |
|---|---|
| `PUBLISHED` | 发布 |
| `UNPUBLISHED` | 未发布（仅云词本/释义）|
| `DELETED` | 删除 |

### `type`（云词本）
| 值 | 含义 |
|---|---|
| `FAVORITE` | 我的收藏 |
| `NOTEPAD` | 云词本 |

## 时区处理（重要）

所有 `*_date` 字段是 **UTC 时间，但 anchor 在每天 `16:00:00.000Z`** —— 这对应 **北京时间当天 0 点**。

`next_study_date` 等筛选参数要求 **ISO 8601 北京时区**（如 `"2026-08-03T00:00:00+08:00"`）。

**简化做法：** 字符串前缀匹配筛选"今天 due"词：
```python
TODAY = "2026-08-03"  # 北京时间今天
due = [r for r in records if r["next_study_date"].startswith(TODAY)]
```

## 通用错误码

| 错误码 | 含义 | 怎么办 |
|---|---|---|
| `common_unauthorized` | token 失效/无权限 | 重新生成 token |
| `common_not_found` | 端点不存在或资源被删 | 检查路径 |
| `common_invalid_param` | body/query 参数错 | 看错误信息 `info` 字段（它会告诉你缺哪个字段）|
| `common_rate_limited` | 限流 | sleep 重试 |
| `interpretation_invalid_tag` | 释义 tag 不在允许列表 | 查用户已有 tag 或留空 |
| `interpretation_create_limitation` | 释义 tag 达上限 | 换 tag |

错误信息 `info` 字段通常**会**告诉你缺哪个字段（这是这次探索最大的发现）：
```
"{base}.interpretation must have required property 'tags'"
"{base} must have required property 'voc_id'"
```

## 踩坑清单（按踩的次数排）

- **`/study/today` 永远是 404** — 真正的"今日单词"是 `POST /study/get_today_items`
- **`query_study_records` 日期过滤**：`{next_study_date: {start, end}}`，不是 `start_date` / `from` / `date`
- **`FORGOT` 拼错** — 正确是 `FORGET`（墨墨的拼法）
- **`tags` 完整枚举** 是 `STICKING / WELL_FAMILIAR`，不要凭印象只写 `STICKING`
- **`/vocabulary` 只能查单个** — 批量查用 `POST /vocabulary/query`
- **`POST /vocabulary/query` spellings 和 ids 不能同时用**（schema 提示"忽略其他条件"，实际是二选一）
- **markji 跟 memo 限流分开** — 一个 5h/2000 一个 5h/8000
- **释义/例句/助记的 `tags`** 必须是用户已用过的或墨墨预置的，每个 tag 有最大创建数
- **`status: 0/1/2` 是 notepads 的旧版字段** — 新版用 `PUBLISHED/UNPUBLISHED/DELETED`
- **`POST /{resource}/{id}` 是更新**（不是 PUT），且 content 全量替换
- **`data.count` 在 study_records 里有意义（=总数），其它接口可能不靠谱**
