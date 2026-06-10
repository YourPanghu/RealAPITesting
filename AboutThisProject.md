# AboutThisProject —— RealAPITesting 学习指南

> 这份文档不是说明书，是**学习路线图**。  
> 告诉你：先看什么、重点理解什么、哪些代码必须能盲敲。

---

## 1. 这个项目在做什么？

```
用 pytest 对真实第三方 HTTP API 做自动化测试。
3 个 API 平台，30 个测试用例，覆盖 8 种测试模式。
```

一句话记住：**把 API 请求封装成"类的方法"，测试用例只调用方法 + 写断言。**

---

## 2. 阅读顺序（按这个看，不要跳）

### 第一步：理解"配置怎么管的"

| 顺序 | 文件 | 看什么 | 时间 |
|------|------|--------|------|
| 1 | `.env.example` | API Key 长什么样，为什么用 .env | 1 分钟 |
| 2 | `.gitignore` | `.env` 被忽略，不会提交到 GitHub | 30 秒 |
| 3 | `config.py` | **重点**：Config 单例、`_load_dotenv()`、`has_xxx_key()` 的安全校验、多 Key 逗号分隔解析 | 5 分钟 |

> 🔑 **核心知识点**：`has_qweather_key()` 检查 `"your_"` 不在 key 里 —— 这样即使用了 `.env.example` 的占位符也不会发出无效请求。聚合数据的 `JUHE_API_KEYS` 支持逗号分隔多个 Key，解决不同接口订阅不同 Key 的问题。

### 第二步：理解"API 怎么封装的"

| 顺序 | 文件 | 看什么 | 时间 |
|------|------|--------|------|
| 4 | `apis/__init__.py` | Page Object 思想的文档说明 | 2 分钟 |
| 5 | `apis/hitokoto_api.py` | 最简单的 API 客户端 —— 只有 2 个方法 | 5 分钟 |
| 6 | `apis/qweather_api.py` | **重点**：`_get()` 统一入口模式、天气/地理双 Host 架构、`verify_connection()` 预检 | 5 分钟 |
| 7 | `apis/juhe_api.py` | **重点**：多 Key 自动切换的 `_get()`、`is_success()`、笑话 API 必传 time 时间戳 | 5 分钟 |

> 🔑 **核心知识点**：`_get(self, endpoint, **params)` 是四合一 —— **URL 拼接 + 自动注入 Key + 认证失败自动换 Key + 异常处理**。上层方法只需要传业务参数。聚合数据不同接口可能用不同 Key，`_get` 遇到 10001 等认证错误会自动切换下一个 Key。

### 第三步：理解"测试怎么写的"

| 顺序 | 文件 | 看什么 | 时间 |
|------|------|--------|------|
| 8 | `tests/conftest.py` | fixture 机制、`pytest_configure` 钩子 | 5 分钟 |
| 9 | `tests/test_hitokoto.py` | **最重要**：五步测试法 + 4 种测试模式 | 10 分钟 |
| 10 | `tests/test_qweather.py` | 数据驱动（CSV）+ 业务逻辑断言 | 8 分钟 |
| 11 | `tests/test_juhe.py` | 翻页不重复 + 多分类 parametrize | 5 分钟 |
| 12 | `data/cities.csv` | 数据驱动的数据源 | 1 分钟 |

---

## 3. 重点理解记忆

### 3.1 API 测试五步法 🔴 必须能说出来

```
① 状态码检查     → 200 OK（或 raise_for_status 隐式检查）
② 响应结构检查   → 必需字段都在（for field in required_fields）
③ 字段类型检查   → id 是 int、name 是 str（isinstance）
④ 业务逻辑检查   → 最高温 >= 最低温、翻页数据不重复
⑤ 异常场景测试   → 无效参数、超大页码、空参数
```

> 对应代码在 `test_hitokoto.py:test_get_random_sentence`，每一步都有注释标记 ①②③④。

### 3.2 API 客户端封装模式 🔴 必须能画图说明

```
测试用例                     API 客户端                   第三方 API
────────                    ──────────                  ──────────
test_weather(api)  ──调用──→  api.get_now_weather()  ──HTTP──→  和风天气
  只写断言                       │                              服务器
  不写 requests                  ├─ URL 拼接
  不写 URL                       ├─ 注入 API Key
                                 ├─ 设置超时
                                 └─ 异常处理
```

> 对应代码在 `apis/qweather_api.py:_get()` 方法。

### 3.3 为什么用 .env 管理 Key？

```
❌ 硬编码在代码里  → 泄露风险，git 提交就完了
❌ 环境变量直接设  → 换机器就丢失
✅ .env 文件       → 本地用，.gitignore 不提交，CI 用环境变量
✅ .env.example    → 模板，告诉别人需要哪些 Key，可以提交
```

### 3.4 fixture scope 的选择原则

| scope | 什么时候用 | 本项目中的例子 |
|-------|-----------|---------------|
| `session` | 无状态、全局唯一 | `config` fixture（配置单例） |
| `module` | 无状态、一个文件内共用 | `api` fixture（API 客户端） |
| `function` | 需要隔离、每个测试独立 | 本项目未使用（不需要） |

> 🔑 口诀：**能大不小** —— 能 session 不 module，能 module 不 function。每个测试 new 对象是浪费。

### 3.5 数据驱动 parametrize 的价值

```python
# ❌ 硬编码：加一个城市要改代码
def test_shenzhen(api): ...
def test_guangzhou(api): ...
def test_beijing(api): ...

# ✅ 数据驱动：加城市只改 CSV
@pytest.mark.parametrize("city,location_id,province", load_cities())
def test_multi_cities(self, api, city, location_id, province):
    ...
```

> **关键好处**：非技术人员（PM/QA）可以 Excel 编辑 CSV 来维护测试数据。

---

## 4. 必须能盲敲的代码（肌肉记忆）

以下代码要做到**不开参考、直接敲出来**。每天敲一遍，一周就熟了。

### 4.1 Config 单例模式 ⭐⭐⭐

```python
# 盲敲目标：30 秒写出完整 Config 类框架
import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent

class Config:
    def __init__(self):
        self._load_dotenv()
        # 单 Key
        self.SOME_API_KEY = os.getenv("SOME_API_KEY", "")
        # 多 Key（逗号分隔，如 KEY1,KEY2）
        _raw = os.getenv("MULTI_API_KEY", "")
        self.MULTI_API_KEYS = [k.strip() for k in _raw.split(",") if k.strip()]
        self.SOME_BASE_URL = "https://api.example.com"

    def _load_dotenv(self):
        try:
            from dotenv import load_dotenv
            env_path = ROOT_DIR / ".env"
            if env_path.exists():
                load_dotenv(env_path)
        except ImportError:
            pass

    def has_some_key(self) -> bool:
        return bool(self.SOME_API_KEY and "your_" not in self.SOME_API_KEY)

_config = None

def get_config():
    global _config
    if _config is None:
        _config = Config()
    return _config
```

### 4.2 API 客户端 _get 统一入口 ⭐⭐⭐

```python
# 盲敲目标：45 秒写出带 _get 的 API 客户端
import requests

class XxxAPI:
    # 需要切换 Key 重试的认证错误码
    _AUTH_ERRORS = {10001, 10002, 10003}

    def __init__(self, api_keys: list, base_url: str, timeout: int = 10):
        self.api_keys = api_keys  # 支持多个 Key 自动切换
        self.base_url = base_url
        self.timeout = timeout

    def _get(self, endpoint: str, **params) -> dict:
        """带多 Key 自动切换的通用请求"""
        for i, key in enumerate(self.api_keys):
            params["key"] = key
            url = f"{self.base_url}/{endpoint}"
            resp = requests.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            # 成功直接返回，认证错误换下一个 Key
            if data.get("error_code") == 0:
                return data
            if data.get("error_code") in self._AUTH_ERRORS:
                if i < len(self.api_keys) - 1:
                    continue
            return data
        return {"error_code": -1, "reason": "所有 Key 都不可用"}

    def get_something(self, param1: str) -> dict:
        return self._get("something/endpoint", param1=param1)
```

### 4.3 Pytest fixture (module scope) ⭐⭐

```python
# 盲敲目标：20 秒写出 fixture
import pytest

@pytest.fixture(scope="module")
def api():
    return XxxAPI(api_key="xxx")
```

### 4.4 数据驱动 parametrize + CSV ⭐⭐⭐

```python
# 盲敲目标：60 秒写出完整的数据驱动测试
import csv

def load_test_data():
    data = []
    with open("data/test.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append((row["col1"], row["col2"]))
    return data

@pytest.mark.parametrize("param1,param2", load_test_data())
def test_data_driven(api, param1, param2):
    result = api.get_something(param1)
    assert result["code"] == "200"
```

### 4.5 标准测试类结构 ⭐⭐

```python
# 盲敲目标：30 秒写出测试类框架
class TestXxxBasic:
    """基础功能 / 冒烟测试"""

    def test_basic_smoke(self, api):
        data = api.get_something()

        # ① 响应结构
        required = ["field1", "field2", "field3"]
        for f in required:
            assert f in data, f"缺少字段: {f}"

        # ② 字段类型
        assert isinstance(data["field1"], int)
        assert isinstance(data["field2"], str)

        # ③ 业务逻辑
        assert len(data["field2"]) > 0

class TestXxxCategories:
    """分类/过滤测试 —— 用 parametrize"""

    @pytest.mark.parametrize("category", ["a", "b", "c"])
    def test_category_filter(self, api, category):
        data = api.get_something(category)
        assert data["type"] == category

class TestXxxEdgeCases:
    """异常/边界场景"""

    def test_invalid_param(self, api):
        # 传入无效参数，验证不崩溃且返回合理
        data = api.get_something("invalid")
        assert "error" in data or data["code"] != "200"
```

### 4.6 条件跳过（无 Key 自动 skip + 连接预检） ⭐⭐

```python
# 盲敲目标：30 秒写出带连接预检的条件跳过逻辑
cfg = get_config()
SKIP_REASON = None
if not cfg.has_xxx_key():
    SKIP_REASON = "未配置 XXX API Key。\n  1. 注册 xxx.com\n  2. .env 写入 XXX_API_KEY=你的key"

@pytest.fixture(scope="module")
def api():
    if SKIP_REASON:
        pytest.skip(SKIP_REASON)
    client = XxxAPI(api_keys=cfg.XXX_API_KEYS)
    # 连接预检：Key 格式有效不代表能用，发一个轻量请求验证
    is_valid, msg = client.verify_connection()
    if not is_valid:
        pytest.skip(f"XXX API Key 不可用:\n{msg}")
    return client
```

> 🔑 **进阶技巧**：`verify_connection()` 是连接预检模式 —— 格式检查（`has_xxx_key()`）只能过滤占位符，网络验证才能确认 Key 是否真的激活了。在 fixture 里做，所有依赖该 fixture 的测试自动受益。

---

## 5. 项目架构速记图

```
RealAPITesting/
│
├── config.py              ← ① 配置层：读 .env → 单例 Config
│
├── apis/                  ← ② 封装层：API 客户端（类似 Page Object）
│   ├── hitokoto_api.py    ←   最简单，先看这个
│   ├── qweather_api.py    ←   核心：_get() 统一入口
│   └── juhe_api.py        ←   同上模式 + is_success()
│
├── tests/                 ← ③ 测试层：pytest 用例
│   ├── conftest.py        ←   fixtures + pytest 配置
│   ├── test_hitokoto.py   ←   最重要：五步法、四种测试模式
│   ├── test_qweather.py   ←   数据驱动（CSV parametrize）
│   └── test_juhe.py       ←   翻页去重、多分类
│
├── data/                  ← ④ 数据层：CSV 测试数据
│   └── cities.csv         ←   8 个城市的 Location ID
│
├── .env.example           ← ⑤ 配置模板：告诉别人需要哪些 Key
├── .env                   ←   真实 Key（不提交 Git）
├── requirements.txt       ←   依赖：requests + pytest + pytest-html + python-dotenv
└── pytest.ini             ←   pytest 全局配置
```

> 数据流向：`.env` → `config.py` → `apis/` → `tests/` → 断言通过/失败

---

## 6. 可以扩展的方向（理解了基础后再做）

| 方向 | 做什么 | 难度 |
|------|--------|------|
| 加新 API | 仿照 `hitokoto_api.py` 封装一个自己的 API（如微博热搜、天气预警） | ⭐ |
| 加响应 Schema 校验 | 用 `jsonschema` 或 `pydantic` 替代手动 `isinstance` 检查 | ⭐⭐ |
| Allure 报告 | 替换 `pytest-html` 为 Allure，生成更漂亮的测试报告 | ⭐⭐ |
| CI 集成 | 写 GitHub Actions，每次 push 自动跑测试 | ⭐⭐ |
| 并发测试 | 用 `pytest-xdist` 并行跑多城市天气测试 | ⭐ |
| Mock 服务 | 用 `responses` 或 `wiremock` mock 第三方 API，测试异常路径 | ⭐⭐⭐ |

---

## 7. 学习检查清单

学完后问自己，能答上来就过关：

- [ ] API 测试五步法是什么？每一步对应什么断言？
- [ ] `_get()` 方法做了什么？为什么所有业务方法都调它？
- [ ] `.env` 和 `.env.example` 的区别？为什么两个都要有？
- [ ] `has_xxx_key()` 为什么检查 `"your_"`？
- [ ] fixture 三个 scope 分别什么时候用？
- [ ] `parametrize` 比手写多个测试函数好在哪里？
- [ ] CSV 数据驱动的 `load_cities()` 返回什么格式？
- [ ] 没有 API Key 时测试怎么跳过？跳过的代码在哪里？
- [ ] `verify_connection()` 连接预检和 `has_xxx_key()` 格式检查有什么区别？为什么两个都要？
- [ ] 聚合数据多 Key 自动切换是怎么实现的？什么错误码会触发切换？
- [ ] 翻页不重复的断言逻辑怎么写？
- [ ] 如果接口新增了一个字段，哪些测试需要改？

---

> 💡 **建议**：先把 `test_hitokoto.py` 跑通（不需要 Key），然后对照这份文档读代码。每天敲一遍第 4 节的盲敲代码，一周后就是肌肉记忆。
