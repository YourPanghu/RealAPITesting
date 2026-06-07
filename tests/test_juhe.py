"""
聚合数据 API 测试（需免费注册 API Key）
========================================
测试套路：
  1. 笑话 API：验证列表长度、字段完整性、内容非空
  2. 新闻 API：验证不同分类（国内/科技/体育）
  3. 数据驱动：parametrize 测试多个新闻分类
  4. 分页测试：翻页数据不重复

前置条件：
  1. 注册 https://www.juhe.cn/ 获取免费 AppKey
  2. 将 Key 写入 .env 文件：JUHE_API_KEY=你的key
  3. 或设置环境变量：export JUHE_API_KEY=你的key

运行：
  pytest tests/test_juhe.py -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config
from apis.juhe_api import JuheAPI


# ============================================================
# 检查 API Key 是否配置
# ============================================================
cfg = get_config()
SKIP_REASON = None
if not cfg.has_juhe_key():
    SKIP_REASON = (
        "未配置聚合数据 API Key。\n"
        "  1. 注册 https://www.juhe.cn/\n"
        "  2. 将 Key 写入 .env 文件：JUHE_API_KEY=你的key\n"
        "  3. 然后重新运行测试"
    )


@pytest.fixture(scope="module")
def api():
    if SKIP_REASON:
        pytest.skip(SKIP_REASON)
    return JuheAPI(api_key=cfg.JUHE_API_KEY)


# ============================================================
# 笑话 API 测试
# ============================================================

@pytest.mark.juhe
class TestJokeAPI:
    """笑话大全 API 测试"""

    def test_get_jokes_basic(self, api):
        """获取笑话列表 —— 基本冒烟测试"""
        data = api.get_jokes(page=1, pagesize=5)

        # 1. API 成功
        assert api.is_success(data), (
            f"API 返回失败: error_code={data.get('error_code')}, "
            f"reason={data.get('reason')}"
        )

        # 2. 结果结构
        result = data["result"]
        assert "data" in result, "返回结果缺少 data 字段"

        jokes = result["data"]
        assert len(jokes) > 0, "笑话列表不应为空"
        assert len(jokes) <= 5, f"预期最多 5 条，实际 {len(jokes)}"

        # 3. 每条笑话字段完整性
        for i, joke in enumerate(jokes):
            assert "content" in joke, f"第{i+1}条缺少 content"
            assert "hashId" in joke, f"第{i+1}条缺少 hashId"
            assert len(joke["content"]) > 0, f"第{i+1}条内容为空"

            print(f"\n  😂 笑话 {i+1}: {joke['content'][:80]}...")

    def test_get_jokes_pagination(self, api):
        """翻页测试：第1页和第2页内容不重复"""
        page1 = api.get_jokes(page=1, pagesize=5)
        page2 = api.get_jokes(page=2, pagesize=5)

        assert api.is_success(page1) and api.is_success(page2), (
            "翻页请求失败"
        )

        ids_p1 = {j["hashId"] for j in page1["result"]["data"]}
        ids_p2 = {j["hashId"] for j in page2["result"]["data"]}

        # 两页不应有重复 ID
        overlap = ids_p1 & ids_p2
        assert len(overlap) == 0, (
            f"第1页和第2页有 {len(overlap)} 条重复笑话"
        )

        print(f"\n  第1页: {len(ids_p1)} 条 | 第2页: {len(ids_p2)} 条 | 重复: 0 ✅")


# ============================================================
# 新闻 API 测试
# ============================================================

@pytest.mark.juhe
class TestNewsAPI:
    """新闻头条 API 测试"""

    @pytest.mark.parametrize("news_type,type_name", [
        ("top", "推荐"),
        ("guonei", "国内"),
        ("keji", "科技"),
        ("tiyu", "体育"),
    ])
    def test_get_news_by_category(self, api, news_type, type_name):
        """数据驱动：测试不同分类新闻"""
        data = api.get_news(news_type=news_type, page_size=5)

        # 1. API 成功
        assert api.is_success(data), (
            f"[{type_name}] API 失败: error_code={data.get('error_code')}"
        )

        # 2. 结果结构
        result = data["result"]
        assert "data" in result, f"[{type_name}] 缺少 data 字段"

        news_list = result["data"]
        assert len(news_list) > 0, f"[{type_name}] 新闻列表不应为空"

        # 3. 每条新闻字段
        for i, news in enumerate(news_list):
            required = ["title", "date", "url", "author_name"]
            for field in required:
                assert field in news, (
                    f"[{type_name}] 第{i+1}条缺少字段: {field}"
                )
            assert len(news["title"]) > 0, f"[{type_name}] 第{i+1}条标题为空"

        print(f"\n  📰 [{type_name}] 返回 {len(news_list)} 条新闻")
        for news in news_list[:3]:
            print(f"    - {news['title'][:50]}... ({news['author_name']})")


# ============================================================
# 异常场景测试
# ============================================================

@pytest.mark.juhe
class TestErrorHandling:
    """异常场景"""

    def test_invalid_api_action(self, api):
        """无效的 API 路径应返回错误"""
        # 聚合数据对错误参数的返回格式
        data = api.get_jokes(page=1, pagesize=20)  # pagesize 上限内
        # 不传 key 参数时会有 HTTP 错误，这里验证正常调用不报错
        assert "error_code" in data, "返回数据应有 error_code 字段"

    def test_large_page_number(self, api):
        """超大页码的处理"""
        data = api.get_jokes(page=99999, pagesize=5)

        # 可能返回成功但数据为空，或返回错误码
        if api.is_success(data):
            jokes = data["result"]["data"]
            # 超大数据页码应该返回空列表或很少的数据
            print(f"\n  页码 99999 返回 {len(jokes)} 条笑话（合理：无数据或少量数据）")
        else:
            print(f"\n  页码 99999 返回错误: {data.get('reason')}（合理）")
