# 云词本

> 云词本 CRUD。**memo-context Step 6 回灌用到**。

| 端点 | 方法 | 用途 | 标签 |
|---|---|---|---|
| [/notepads?limit=&offset=](#get-notepads) | GET | 列云词本 | 🔶 备用 |
| [/notepads](#post-notepads) | POST | 创建云词本 | ✅ 常用（Step 6）|
| [/notepads/{id}](#get-notepadid) | GET | 取单个云词本 | 🔶 备用 |
| [/notepads/{id}](#post-notepadid) | POST | 更新云词本（**注意是 POST 不是 PUT**）| 🔶 备用 |
| [/notepads/{id}](#delete-notepadid) | DELETE | 删除云词本 | 🔶 备用 |

---

## 通用字段

### `Notepad` 对象

| 字段 | 类型 | 必填（创建）| 说明 |
|---|---|---|---|
| `id` | string | 仅返回 | 云词本 ID |
| `type` | enum | 仅返回 | `FAVORITE`（我的收藏）/ `NOTEPAD`（云词本）|
| `creator` | int | 仅返回 | 创建者用户 ID |
| `status` | enum | ✅ | `PUBLISHED` / `UNPUBLISHED` / `DELETED` |
| `content` | string | ✅ | 词条内容（每行一个词，可用 `# 章节` 分组）|
| `title` | string | ✅ | 标题 |
| `brief` | string | ✅ | 简介（**唯一额外文字字段**）|
| `tags` | string[] | ✅ | 标签 |
| `list` | object[] | 仅返回 | 自动解析后的 `NotepadParsedItem` 数组 |
| `created_time` | ISO 8601 | 仅返回 | |
| `updated_time` | ISO 8601 | 仅返回 | |

### `content` 章节语法

```
apple
banana
# 食物
chicken
duck
# 动物
```

→ 墨墨自动解析为 `list: [{type: "WORD", data: {word: "apple"}}, {type: "CHAPTER", data: {chapter: "食物"}}, ...]`

### `NotepadParsedItem`

```json
{
  "type": "CHAPTER" | "WORD",
  "data": {
    "chapter": "食物",
    "word": "apple"  // 当 type=WORD 时
  }
}
```

---

## GET /notepads

### Request

```
GET /notepads?limit=20&offset=0&ids=np-...
```

| Query | 类型 | 必填 | 说明 |
|---|---|---|---|
| `limit` | int | ✅ | 查询数量 |
| `offset` | int | ✅ | 跳过数量 |
| `ids` | string[] | ❌ | 指定 ID 列表过滤 |

### Response (200)

```json
{
  "errors": [],
  "data": {
    "notepads": [
      {
        "id": "np-...",
        "type": "NOTEPAD",
        "creator": 192,
        "status": "PUBLISHED",
        "title": "今日精读-2026-08-03",
        "brief": "今日语境摘要",
        "tags": ["memo-context"],
        "created_time": "...",
        "updated_time": "..."
      }
    ]
  },
  "success": true
}
```

---

## POST /notepads

**memo-context Step 6 回灌用这个。**

### Request

```json
{
  "notepad": {
    "status": "PUBLISHED",
    "content": "vivid\ntangible\neloquent",
    "title": "今日精读-2026-08-03",
    "brief": "今日语境摘要",
    "tags": ["memo-context"]
  }
}
```

### Response (200)

返回完整 `notepad` 对象（含 id 和自动解析的 `list`）。

---

## GET /notepads/{id}

### Request

```
GET /notepads/np-...
```

### Response (200)

返回完整 `notepad` 对象（含 `content` 原文 + `list` 解析结果）。

---

## POST /notepads/{id}

### Request

```json
{
  "notepad": {
    "status": "PUBLISHED",
    "content": "新内容...",
    "title": "新标题",
    "brief": "新简介",
    "tags": ["新tag"]
  },
  "id": "np-..."
}
```

**注意：**
- **是 POST 不是 PUT**
- **content 全量替换**，不是 diff
- `id` 必须在顶层和 path 一致
- `voc_id` 不需要（云词本不绑单词）

---

## DELETE /notepads/{id}

### Request

```
DELETE /notepads/np-...
```

### Response (200)

```json
{
  "errors": [],
  "data": {
    "notepad": { /* 软删后的对象，status: "DELETED" */ }
  },
  "success": true
}
```

**软删：** 不会从 GET 列表中消失，状态变成 `DELETED`。
