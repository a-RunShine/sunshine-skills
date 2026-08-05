# 记忆卡（Markji）

> 牌组 / 章节 / 卡片 / 文件完整 CRUD。
> memo-context **暂不用**（memo-context 只用背单词那侧），但写在这里备查。

| 端点 | 方法 | 用途 | 标签 |
|---|---|---|---|
| [/markji/decks?offset=&limit=&folder_id=](#get-markjidecks) | GET | 列我的牌组 | 🔶 备用 |
| [/markji/decks/folders](#get-markjidecksfolders) | GET | 牌组文件夹 | 🔶 备用 |
| [/markji/decks/{deck}?with_root=](#get-markjidecksdeck) | GET | 牌组详情 | 🔶 备用 |
| [/markji/decks/{deck}/chapters?with_cards=&updated_time=](#get-markjidecksdeckchapters) | GET | 牌组章节列表 | 🔶 备用 |
| [/markji/decks/{deck}/chapters/{chapter}?with_cards=](#get-markjidecksdeckchapterschapter) | GET | 单个章节 | 🔶 备用 |
| [/markji/decks/{deck}/cards/{card}](#get-markjidecksdeckcardscard) | GET | 卡片详情 | 🔶 备用 |
| [/markji/decks/{deck}/chapters/{chapter}/cards](#post-markjidecksdeckchapterschaptercards) | POST | 新建卡片 | 🔶 备用 |
| [/markji/decks/{deck_id}/cards/{card_id}](#post-markjidecksdeck_idcardscard_id) | POST | 更新卡片 | 🔶 备用 |
| [/markji/files](#post-markjifiles) | POST | 上传文件（multipart）| 🔶 备用 |
| [/markji/files/query](#post-markjifilesquery) | POST | 查文件外链 | 🔶 备用 |

---

## 通用枚举

### 资源 `status`

| 值 | 含义 |
|---|---|
| `NORMAL` | 正常 |
| `DELETED` | 删除 |
| `BLOCKED` | 封禁 |

### 资源 `source`

| 值 | 含义 |
|---|---|
| `SELF` | 自建 |
| `FORK` | 派生 |

### 文件夹 `object_class`

| 值 | 含义 |
|---|---|
| `FOLDER` | 文件夹 |
| `DECK` | 牌组 |

### 卡片 `content_type`

| 值 | 含义 |
|---|---|
| `PLAIN` | 纯文本 |

---

## 通用字段

### `MarkjiDeck`（牌组）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 牌组 OpenAPI ID |
| `parent_id` | string\|null | 上游牌组 ID（FORK 时有值）|
| `source` | enum | `SELF` / `FORK` |
| `status` | enum | `NORMAL` / `DELETED` / `BLOCKED` |
| `name` | string | 牌组名称 |
| `description` | string | 牌组简介 |
| `creator` | string | 用户 OpenAPI ID |
| `authors` | string[] | 作者 OpenAPI ID 列表 |
| `revision` | int | 牌组版本 |
| `is_private` | bool | 是否私有 |
| `card_count` | int | 卡片数量 |
| `chapter_count` | int | 章节数量 |
| `created_time` | ISO 8601 | |
| `updated_time` | ISO 8601 | |
| `root_deck` | object | 当 `with_root=true` 时返回 |

### `MarkjiChapter`（章节）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 章节 OpenAPI ID |
| `deck_id` | string | 所属牌组 ID |
| `name` | string | 章节名称 |
| `revision` | int | 版本 |
| `card_ids` | string[] | 卡片 ID 列表 |
| `creator` | string | 用户 ID |
| `created_time` / `updated_time` | ISO 8601 | |

### `MarkjiCard`（卡片）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 卡片 OpenAPI ID |
| `status` | enum | 同资源 status |
| `deck_id` | string | 所属牌组 ID |
| `parent_id` | string\|null | 上游卡片 ID（FORK 时）|
| `root_id` | string | 根卡片 ID |
| `revision` | int | 卡片版本 |
| `content` | string | 卡片内容（Markji 语法）|
| `content_type` | enum | `PLAIN` |
| `files` | `MarkjiFile[]` | 卡片包含的文件 |
| `creator` | string | 用户 ID |
| `source` | enum | `SELF` / `FORK` |
| `grammar_version` | int | 语法版本 |
| `card_rids` | string[] | 引用的根卡片 ID 列表 |
| `created_time` / `updated_time` | ISO 8601 | |

### `MarkjiFile`（文件）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 文件 OpenAPI ID |
| `url` | string | 文件访问地址（**有过期时间**）|
| `mime` | string | MIME 类型 |
| `size` | int | 大小（KB，按 4KB 对齐）|
| `info` | object | 文件信息（任意）|
| `expire_time` | ISO 8601 | URL 过期时间 |

### `MarkjiFolder`（文件夹）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 文件夹 ID |
| `name` | string | 文件夹名 |
| `parent_id` | string\|null | 父文件夹 ID |
| `items` | `MarkjiFolderItem[]` | 文件夹内对象 |

### `MarkjiFolderItem`

| 字段 | 类型 | 说明 |
|---|---|---|
| `object_id` | string | 对象 ID |
| `object_class` | enum | `FOLDER` / `DECK` |
| `order` | int | 排序值 |

---

## GET /markji/decks

**用途：** 列我的牌组（支持分页、按文件夹/来源过滤）。

### Request

```
GET /markji/decks?offset=0&limit=20&folder_id=...&source={...}
```

| Query | 类型 | 必填 | 说明 |
|---|---|---|---|
| `offset` | int | ❌ | 偏移量 |
| `limit` | int | ❌ | 每页数量 |
| `folder_id` | string | ❌ | 文件夹 ID |
| `source` | object | ❌ | 来源过滤（schema 标 object，实际是 enum `{SELF, FORK}`）|

### Response (200)

```json
{
  "errors": [],
  "data": {
    "decks": [ /* MarkjiDeck[] */ ],
    "total": 42
  },
  "success": true
}
```

---

## GET /markji/decks/folders

### Response (200)

```json
{
  "errors": [],
  "data": {
    "folders": [ /* MarkjiFolder[] */ ]
  },
  "success": true
}
```

---

## GET /markji/decks/{deck}

| Query | 类型 | 必填 | 说明 |
|---|---|---|---|
| `with_root` | bool | ❌ | 是否返回根牌组信息 |

### Response (200)

```json
{
  "errors": [],
  "data": {
    "deck": { /* MarkjiDeck */ }
  },
  "success": true
}
```

---

## GET /markji/decks/{deck}/chapters

| Query | 类型 | 必填 | 说明 |
|---|---|---|---|
| `updated_time` | ISO 8601 | ❌ | 只返回更新时间晚于该时间的章节 |
| `with_cards` | bool | ❌ | 是否同时返回章节内卡片 |

### Response (200)

```json
{
  "errors": [],
  "data": {
    "chapterset": {
      "id": "...",
      "deck_id": "...",
      "revision": 5,
      "chapter_ids": ["..."],
      "created_time": "...",
      "updated_time": "..."
    },
    "chapters": [ /* MarkjiChapter[] */ ],
    "cards": [ /* MarkjiCard[]，仅 when with_cards=true */ ]
  },
  "success": true
}
```

---

## GET /markji/decks/{deck}/chapters/{chapter}

| Query | 类型 | 必填 | 说明 |
|---|---|---|---|
| `with_cards` | bool | ❌ | |
| `updated_time` | ISO 8601 | ❌ | |

### Response (200)

同 chapters 列表，但 `chapters` 数组只有 1 个。

---

## GET /markji/decks/{deck}/cards/{card}

### Response (200)

```json
{
  "errors": [],
  "data": {
    "card": { /* MarkjiCard */ }
  },
  "success": true
}
```

---

## POST /markji/decks/{deck}/chapters/{chapter}/cards

**用途：** 新建卡片。

### Request

```json
{
  "deck": "deck-...",
  "chapter": "chapter-...",
  "card": {
    "content": "卡片内容（Markji 语法）",
    "grammar_version": 1
  },
  "order": null
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `deck` | string | ✅ | 牌组 OpenAPI ID（**顶层必须有**）|
| `chapter` | string | ✅ | 章节 OpenAPI ID（**顶层必须有**）|
| `card.content` | string | ✅ | 卡片内容（Markji 语法）|
| `card.grammar_version` | int | ✅ | 语法版本 |
| `order` | int | ❌ | 插入位置（不传则追加到章节末尾）|

### Response (200)

```json
{
  "errors": [],
  "data": {
    "card": { /* MarkjiCard（含 id）*/ },
    "chapter": { /* 更新后的 MarkjiChapter */ }
  },
  "success": true
}
```

---

## POST /markji/decks/{deck_id}/cards/{card_id}

**用途：** 更新卡片。

### Request

```json
{
  "deck_id": "deck-...",
  "card_id": "card-...",
  "card": {
    "content": "新内容（Markji 语法）",
    "grammar_version": 1
  }
}
```

### Response (200)

```json
{
  "errors": [],
  "data": {
    "card": { /* MarkjiCard */ }
  },
  "success": true
}
```

---

## POST /markji/files

**用途：** 上传文件（multipart/form-data）。文件可附加到牌组 / 卡片。

### Request

```
POST /markji/files
Content-Type: multipart/form-data

--boundary
Content-Disposition: form-data; name="file"
Content-Type: <mime>

<binary file content>
--boundary
Content-Disposition: form-data; name="deck_id"

deck-...
--boundary--
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `file` | file | ✅ | multipart 中的 `file` 字段 |
| `deck_id` | string | ❌ | 牌组 OpenAPI ID。指定后文件按"牌组编辑权限"归属 |

### Response (200)

```json
{
  "errors": [],
  "data": {
    "file": {
      "id": "file-...",
      "url": "https://...",
      "mime": "image/png",
      "size": 128,
      "info": {},
      "expire_time": "2026-09-02T..."
    }
  },
  "success": true
}
```

### Python 真实样例

```python
import requests

with open("image.png", "rb") as f:
    r = requests.post(
        f"{BASE}/markji/files",
        headers={"Authorization": f"Bearer {TOKEN}"},
        files={"file": ("image.png", f, "image/png")},
        data={"deck_id": "deck-..."},  # 可选
    )
file_id = r.json()["data"]["file"]["id"]
file_url = r.json()["data"]["file"]["url"]  # 注意有过期时间
```

---

## POST /markji/files/query

### Request

```json
{
  "ids": ["file-...", "file-..."],
  "expires": 2592000
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `ids` | string[] | ✅ | 文件 ID 列表 |
| `expires` | int | ❌ | 外链有效期（秒），默认 30 天 |

### Response (200)

```json
{
  "errors": [],
  "data": {
    "files": [ /* MarkjiFile[]，含 url + expire_time */ ]
  },
  "success": true
}
```

---

## Markji 内容语法（card.content 用）

参考 https://markji.com/syntax（墨墨记忆卡语法）。核心规则：

- 普通文字不需要标签
- `[T#B#加粗]` 加粗
- `[F#1#答案1#答案2#答案3]` 挖空
- `[E##x^2 + y^2 = z^2]` 独立公式
- `[P##居中段落]` 段落
- `[Choice##*A#正确选项#-B#错误选项]` 单选
- `[Audio##音频ID#显示文字]` 音频
- `[Pic##图片ID]` 图片
- `[T#link/"url"#文字]` 链接

详细语法见墨墨记忆卡官方文档。
