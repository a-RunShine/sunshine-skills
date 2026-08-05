# 墨墨开放 API 参考

> 2026-08-03 验证可用。Base URL: `https://open.maimemo.com/open/api/v1`
>
> 按 `✅ 常用 / 🔶 备用 / ❌ 未开放` 三档标注：
> - **✅ 常用** — memo-context 主流程用，每次跑都调
> - **🔶 备用** — memo-context 偶尔用或扩展时用
> - **❌ 未开放** — 文档里有 schema 定义但端点 404，公测未上线；别当可用接口调

## 索引速查

| 端点 | 方法 | 用途 | 标签 |
|---|---|---|---|
| `/study/query_study_records` | POST | 拉全量学习记录（today / due / VAGUE / STICKING 都靠它 + 客户端筛） | ✅ 常用 |
| `/vocabulary` | GET | 按拼写查单词基本信息（id, spelling） | 🔶 备用 |
| `/notepads` | GET | 列云词本 | 🔶 备用 |
| `/notepads` | POST | 创建云词本（Step 6 回灌） | ✅ 常用 |
| `/notepads/{id}` | GET | 取单个云词本 | 🔶 备用 |
| `/notepads/{id}` | POST | 更新云词本 | 🔶 备用 |
| `/notepads/{id}` | DELETE | 删除云词本 | 🔶 备用 |
| `/study/today` | GET / POST | 文档定义，**接口 404** | ❌ 未开放 |
| `/study/...` | 其它 | 同上 | ❌ 未开放 |
| `/studies/today` 等 | 其它 | 同上 | ❌ 未开放 |

---

## 鉴权 + 限流

所有请求：
```
Authorization: Bearer <MAIMEMO_TOKEN>
Content-Type: application/json
```

**Token 位置：** `./.claude/skills/memo-context/.env` 的 `MAIMEMO_TOKEN` 字段（项目本地，不外传）。

**401 =** token 失效 / scope 不全 → 提示用户去墨墨 App 重新生成。

**限流：**
- 墨墨背单词：10s/20req，60s/40req，5h/2000req
- 墨墨记忆卡（Markji）：5h/8000req
- memo-context 每天 1-3 篇内容不会撞限流；批量补词场景每篇之间 sleep 几秒

---

## ✅ 常用端点

### `POST /study/query_study_records`

**用途：** 拉全量学习记录（已学/未学/今天该学/VAGUE/STICKING 全部从这一接口算出来）。

memo-context Step 1 的核心接口。**唯一一次调用就拿全库**（用户库 ≤ 200 条够用），客户端按字段筛。

#### Request

```json
{
  "limit": 200
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `limit` | int | 否 | 默认 50，**最大 200** |

**注意：**
- **没有日期过滤参数**（试过 `start_date / end_date / from / to / date / study_date / type=today` 全部被忽略）→ 客户端筛
- 不传 body 或 `{}` 也行，返回前 50 条

#### Response (200)

```json
{
  "errors": [],
  "data": {
    "records": [
      {
        "voc_id": "voc-iFfha6XNiy...",
        "voc_spelling": "apple",
        "add_date": "2026-07-09T20:55:29.000Z",
        "first_study_date": "2026-07-09T16:00:00.000Z",
        "last_study_date": "2026-08-01T16:00:00.000Z",
        "next_study_date": "2026-08-08T16:00:00.000Z",
        "last_response": "FAMILIAR",
        "study_count": 2,
        "tags": []
      }
    ],
    "count": 0
  },
  "success": true
}
```

**⚠️ `data.count` 永远是 0，** 不可信。用 `len(data.records)` 拿真实数量。

#### 字段语义（memo-context 怎么用）

| 字段 | 类型 | 含义 | 怎么用 |
|---|---|---|---|
| `voc_id` | string | 墨墨内部 ID | 通常不用，存档/回灌用 `voc_spelling` 就够 |
| `voc_spelling` | string | 单词拼写 | **核心字段**，全文关键词 |
| `add_date` | string (UTC) | 加入词库时间 | 判"新词"：`add_date.startswith(今天的北京日期)` |
| `first_study_date` | string (UTC) | 首次学习时间 | 辅助判新词：`study_count == 1` |
| `last_study_date` | string (UTC) | 最近学习时间 | 辅助判"今天学过哪些" |
| `next_study_date` | string (UTC) | 下次该复习时间 | **核心字段** — 判"今天 due 词" |
| `last_response` | string (enum) | 上次学习结果 | 枚举见下表 |
| `study_count` | int | 已学次数 | 辅助判新词：`study_count <= 1` |
| `tags` | string[] | 单词标签 | 已知值：`STICKING`（难记） |

#### `last_response` 枚举

| 值 | 含义 | 筛选语义 |
|---|---|---|
| `FAMILIAR` | 认识 | 默认不特殊处理 |
| `VAGUE` | 犹豫 | "讲没记住的"模式命中 |
| `FORGOT` | 忘了 | "讲没记住的"模式命中（用户库暂未出现，schema 存在） |

#### `tags` 已知值

| 值 | 含义 | 筛选语义 |
|---|---|---|
| `STICKING` | 难记（墨墨自定标签） | "讲没记住的"模式命中 |
| `[]` | 无标签 | 默认 |

#### 时区处理（重要）

所有 `*_date` 字段是 **UTC 时间，但 anchor 在每天 `16:00:00.000Z`** —— 这对应 **北京时间当天 0 点**。

**简化做法：** 用字符串前缀匹配判断日期，不用 Python DateTime 换算。

```python
TODAY = "2026-08-03"  # 北京时间今天
due_today  = [r for r in records if r["next_study_date"].startswith(TODAY)]
new_today  = [r for r in records if r["add_date"].startswith(TODAY)]
learned_today = [r for r in records if r["last_study_date"].startswith(TODAY)]

# "讲没记住的" = 难记 ∪ 犹豫/忘了 ∪ 今天 due
unstable = [r for r in records
            if "STICKING" in r.get("tags", [])
            or r["last_response"] in ("VAGUE", "FORGOT")
            or r["next_study_date"].startswith(TODAY)]
```

#### 真实样例（2026-08-03 验证）

```python
import requests
r = requests.post(
    "https://open.maimemo.com/open/api/v1/study/query_study_records",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={"limit": 200},
)
records = r.json()["data"]["records"]  # 200 条

TODAY = "2026-08-03"
due = [r for r in records if r["next_study_date"].startswith(TODAY)]
# → 7 个：assert, chop, permit, prioritize, faith, anticipation, approval
#   permit/prioritize 带 STICKING，anticipation 上次是 VAGUE
```

---

### `POST /notepads`

**用途：** 创建云词本。memo-context Step 6 回灌用。

#### Request

```json
{
  "notepad": {
    "status": 0,
    "content": "word1\nword2\n# 章节2\nword3",
    "title": "今日精读-2026-08-03",
    "brief": "今日语境摘要",
    "tags": ["memo-context"]
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `title` | string | ✅ | 建议格式 `今日精读-YYYY-MM-DD` |
| `content` | string | ✅ | 每行一个词。支持 `# 章节名` 分组（自动解析为 `NotepadParsedItem` 数组） |
| `status` | int | 否 | 0=私有，1=公开，2=... |
| `brief` | string | 否 | 一句话描述语境（仅这一个额外文字字段） |
| `tags` | string[] | 否 | 建议加 `"memo-context"` 方便以后筛选 |

#### Response (200)

```json
{
  "errors": [],
  "data": {
    "notepad": {
      "id": "np-...",
      "title": "今日精读-2026-08-03",
      ...
    }
  },
  "success": true
}
```

返回 `data.notepad.id` 就是新云词本 ID，建议存到 `./contexts/YYYY-MM-DD.md` 方便回看。

**content 章节语法：**
```
apple
banana
# 食物
chicken
duck
# 动物
```
→ 墨墨自动解析为 `list: [{type: "chapter", name: "食物", items: [chicken, duck]}, {type: "word", spelling: apple}, {type: "word", spelling: banana}]`

---

## 🔶 备用端点

### `GET /vocabulary?spelling=...`

**用途：** 按拼写查单词基本信息（仅返回 `id, spelling`，**无学习状态**）。

memo-context 一般不用（`/study/query_study_records` 已包含拼写信息）。仅当需要在外部工具展示"加入云词本"按钮时使用。

#### Request

```
GET /vocabulary?spelling=apple
```

#### Response (200)

```json
{
  "errors": [],
  "data": {
    "voc": {
      "id": "voc-iFfha6XNiy...",
      "spelling": "apple"
    }
  },
  "success": true
}
```

---

### `GET /notepads`

**用途：** 列用户所有云词本（分页机制未公开测过）。

memo-context 用不到（一次回灌只创建一个）。仅在用户要"看看我之前灌过哪些"时用。

#### Response (200)

```json
{
  "errors": [],
  "data": {
    "notepads": [
      {"id": "np-...", "title": "今日精读-2026-08-03", "created_time": "...", ...}
    ]
  },
  "success": true
}
```

---

### `GET /notepads/{id}`

**用途：** 取单个云词本详情。

#### Response (200)

```json
{
  "errors": [],
  "data": {
    "notepad": {
      "id": "np-...",
      "type": "...",
      "creator": "...",
      "status": 0,
      "content": "...",
      "title": "...",
      "brief": "...",
      "tags": [...],
      "list": [...],
      "created_time": "...",
      "updated_time": "..."
    }
  },
  "success": true
}
```

**`list` 字段：** 墨墨自动解析 `content` 后的结构化数组，每个元素是 `NotepadParsedItem`（含 `type: "word"|"chapter"`, `spelling`, `name`, `items` 等）。

---

### `POST /notepads/{id}`

**用途：** 更新云词本（**注意是 POST 不是 PUT**）。

Request body 跟 `POST /notepads` 一样，只传要改的字段。**content 全量替换，不是 diff。**

---

### `DELETE /notepads/{id}`

**用途：** 删除云词本。

#### Response (200)

```json
{"errors": [], "data": {}, "success": true}
```

---

## ❌ 未开放（文档定义但端点 404）

**2026-08-03 实测**，以下端点全部 `404 Resource or Api not found`：

```
GET  /study/today
POST /study/today
GET  /studies
GET  /studies/today
GET  /study_records
POST /study_records
GET  /studies/today
GET  /vocabularies/today
GET  /users/me
GET  /users/me/today
GET  /users/me/studies
GET  /users/me/vocabularies
GET  /me/today
GET  /me/studies
```

**为什么写在这里：** memodocs 的 ENDPOINTS 区定义了 `StudyResponse, StudyProgress, StudyTodayItem, StudyRecord` 等 schema，让人以为有"今日学习清单"接口。**实际公测只放了 `/study/query_study_records`**（返回全量，客户端自己筛）。

**别尝试调这些端点。** 调了也只是 404，浪费限流额度。等墨墨公测再补。

---

## 踩坑清单

- **必须 POST `query_study_records`，GET 返回 404** — 文档没明确说 method
- **`data.count` 永远是 0** — 别信它
- **日期过滤参数不生效** — 必须在客户端筛
- **`limit` 硬上限 200** — 用户库 > 200 时需分页（`offset` / `last_id` cursor 没测过，公测可能不支持）
- **时区 anchor 是 16:00Z** — 字符串前缀匹配比 DateTime 换算稳
- **token 是用户级 scope** — 公测 token 通常有 vocabulary + notepads + query_study_records 三个 scope；如果某个接口 401 但其他 OK，说明 scope 不全
- **GET `/vocabulary` 只返 `id+spelling`** — 没有学习状态，要那个走 `query_study_records`
- **`/notepads/{id}` 更新是 POST 不是 PUT** — REST 风格不一致
- **`content` 全量替换** — 更新不是 diff
- **Markji 限流独立** — `5h/8000req`，跟墨墨背单词的 `5h/2000req` 不共享额度池
