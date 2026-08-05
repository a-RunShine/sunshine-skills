# 助记

> 自定义助记 CRUD。每个单词可以有多条助记（谐音/联想/词根等）。

| 端点 | 方法 | 用途 | 标签 |
|---|---|---|---|
| [/notes?voc_id=...](#get-notes) | GET | 查某词的所有助记 | 🔶 备用 |
| [/notes](#post-notes) | POST | 创建助记 | 🔶 备用 |
| [/notes/{id}](#post-notesid) | POST | 更新助记 | 🔶 备用 |
| [/notes/{id}](#delete-notesid) | DELETE | 删除助记 | 🔶 备用 |

---

## 通用字段

### `Note` 对象

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 仅返回 | 助记 ID |
| `voc_id` | string | ✅（创建）| 单词 ID |
| `note_type` | string | ✅ | 助记类型，如 `"谐音."`、`"联想."`、`"词根."` |
| `note` | string | ✅ | 助记内容 |
| `status` | enum | 仅返回 | `PUBLISHED` / `DELETED` |
| `created_time` | ISO 8601 | 仅返回 | |
| `updated_time` | ISO 8601 | 仅返回 | |

### 常见 `note_type` 值（不限制，字符串自由）

- `谐音.`
- `联想.`
- `词根.`
- `串记.`
- `其它.`

### `status` 枚举

| 值 | 含义 |
|---|---|
| `PUBLISHED` | 发布 |
| `DELETED` | 删除（软删）|

---

## GET /notes

### Request

```
GET /notes?voc_id=voc-...
```

### Response (200)

```json
{
  "errors": [],
  "data": {
    "notes": [
      {
        "id": "nt-...",
        "note_type": "谐音.",
        "note": "阿婆 (ā pó) → apple",
        "status": "PUBLISHED",
        "created_time": "...",
        "updated_time": "..."
      }
    ]
  },
  "success": true
}
```

---

## POST /notes

### Request

```json
{
  "note": {
    "voc_id": "voc-...",
    "note_type": "谐音.",
    "note": "阿婆 (ā pó) → apple"
  }
}
```

### Response (200)

返回完整 note 对象（含 id）。

---

## POST /notes/{id}

### Request

```json
{
  "id": "nt-...",
  "note": {
    "note_type": "谐音.",
    "note": "阿婆 (ā pó) → apple（修订）"
  }
}
```

---

## DELETE /notes/{id}

### Request

```
DELETE /notes/nt-...
```

### Response

软删（`status: DELETED`），不会从 GET 列表消失。
