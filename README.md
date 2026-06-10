# RealAPITesting - 真实国内 API 测试实战

[![GitHub](https://img.shields.io/badge/GitHub-YourPanghu%2FRealAPITesting-blue?logo=github)](https://github.com/YourPanghu/RealAPITesting)

> 🎯 对接真实国内第三方 API，用 Pytest 做接口自动化测试  
> 📍 这是 [FirstPro](https://github.com/YourPanghu/FirstPro) 学习路线的第 9 站

---

## 📁 项目结构

```
RealAPITesting/
├── config.py              # 配置管理（从 .env 读取 API Key）
├── pytest.ini             # Pytest 配置
├── requirements.txt       # Python 依赖
├── .env.example           # API Key 模板（真实 Key 不提交）
│
├── apis/                  # API 客户端封装（类似 Page Object）
│   ├── hitokoto_api.py    # 一言：随机句子（无需 Key）
│   ├── qweather_api.py    # 和风天气：实况/预报/空气质量
│   └── juhe_api.py        # 聚合数据：笑话/新闻
│
├── tests/                 # 测试用例
│   ├── conftest.py        # Pytest fixtures
│   ├── test_hitokoto.py   # 一言测试（8 个用例）
│   ├── test_qweather.py   # 和风天气测试（14 个用例）
│   └── test_juhe.py       # 聚合数据测试（8 个用例）
│
├── data/                  # 测试数据
│   └── cities.csv         # 数据驱动：8 个城市天气
│
└── reports/               # HTML 测试报告
```

---

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 跑一言测试（无需任何 Key，立即体验）
```bash
pytest tests/test_hitokoto.py -v
```

### 3. 配置 API Key（可选）

需要测试和风天气和聚合数据时才需要：

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env，填入你的 Key
# QWEATHER_API_KEY=你的和风天气key    ← 注册 https://dev.qweather.com/
# JUHE_API_KEY=新闻的key,笑话的key     ← 注册 https://www.juhe.cn/（支持多 Key 逗号分隔）
```

### 4. 跑全部测试
```bash
# 全部测试（没 Key 的自动跳过）
pytest -v

# 生成 HTML 报告
pytest -v --html=reports/report.html

# 只跑不需要 Key 的
pytest tests/test_hitokoto.py -v
```

---

## 📊 三个 API 对比

| API | 提供方 | 需要 Key | 免费额度 | 测试用例数 |
|-----|--------|---------|----------|-----------|
| 一言 | hitokoto.cn | ❌ 不需要 | 无限 | 8 |
| 和风天气 | dev.qweather.com | ✅ 免费注册 | 50,000次/月 | 14 |
| 聚合数据 | juhe.cn | ✅ 免费注册 | 各接口不同 | 8 |

**总共 30 个测试用例**

---

## 🧪 测试覆盖

### 一言（hitokoto）
- 基础请求 + 响应结构验证
- 字段类型检查（id 是 int，hitokoto 是 str）
- 分类过滤：动画/文学/诗词/哲学
- 异常参数处理
- 随机性验证（多次请求不重复）
- 响应时间检查

### 和风天气（QWeather）
- 实况天气：多城市数据驱动（深圳/广州/东莞/北京/上海/杭州/成都/武汉）
- 7 天预报：字段完整性 + 最高温≥最低温
- 空气质量：AQI/PM2.5/PM10
- 城市搜索：Location ID 查询
- 异常场景：无效城市 ID / 空参数

### 聚合数据（Juhe）
- 笑话 API：列表 + 翻页不重复（新版必传 time 时间戳参数）
- 新闻 API：推荐/国内/科技/体育 多分类
- 多 Key 自动切换：不同接口用不同 Key 时自动 fallback
- 异常场景：超大页码

---

## 💡 设计要点

### API 客户端封装（类似 Page Object）
```python
# ❌ 直接在测试里写 requests
def test_weather():
    resp = requests.get("https://devapi.qweather.com/v7/weather/now?location=...&key=...")

# ✅ 封装成 API 类，测试只调用方法
def test_weather(api):
    data = api.get_now_weather("101280601")
    assert data["code"] == "200"
```

### API Key 管理
- `.env` 文件存 Key，不提交 Git
- `.env.example` 是模板，可以提交
- 没 Key 时测试自动跳过（含 API 连接预检），不影响 CI 跑其他测试
- 聚合数据支持**多 Key 逗号分隔**，不同接口自动匹配可用 Key

### 测试套路
```
状态码检查 → 响应结构验证 → 字段类型检查 → 业务逻辑断言 → 异常场景
```

---

## 📈 学习路线（来自 FirstPro）

| 阶段 | 内容 | 状态 |
|------|------|------|
| 🔰 入门 | Python 基础 | ✅ |
| 🟢 实战 | API CRUD + Pytest | ✅ |
| 🔵 工程 | Postman + Newman | ✅ |
| 🟢 实战 | Selenium Web 自动化 | ✅ |
| 🔵 进阶 | Selenium Alert/iframe/窗口 | ✅ |
| 🚀 工程 | Git + GitHub | ✅ |
| 🔵 工程 | MySQL 数据库测试 | ✅ |
| 🚀 工程 | JMeter 性能测试 | ✅ |
| 🔴 实战 | **真实国内 API 实战** | 🔄 |

---
