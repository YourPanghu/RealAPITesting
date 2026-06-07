"""
一言 API 测试（无需 Key，开箱即用）
===================================
这是三个 API 中唯一不需要注册的，先跑它体验"真实 API 测试"的感觉。

测试套路：
  1. 状态码检查 → 200 OK
  2. 响应结构检查 → 必需字段都存在
  3. 字段类型检查 → id是int, hitokoto是str
  4. 业务逻辑检查 → 句子不为空，分类在合法范围内
  5. 异常场景 → 无效分类的处理

运行：
  pytest tests/test_hitokoto.py -v
"""

import pytest
import sys
import os

# 确保能 import apis 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apis.hitokoto_api import HitokotoAPI, CATEGORIES


@pytest.fixture(scope="module")
def api():
    """创建 API 客户端（module 级别复用）"""
    return HitokotoAPI()


# ============================================================
# 基础功能测试
# ============================================================

class TestHitokotoBasic:
    """基础请求测试 —— 验证 API 是否可用"""

    def test_get_random_sentence(self, api):
        """测试获取随机句子 —— 最基础的冒烟测试"""
        data = api.get_sentence()

        # 1. 状态码（通过 raise_for_status 已检查）
        # 2. 响应结构
        required_fields = ["id", "uuid", "hitokoto", "type", "from", "creator"]
        for field in required_fields:
            assert field in data, f"缺少必需字段: {field}"

        # 3. 字段类型
        assert isinstance(data["id"], int), f"id 应为 int，实际 {type(data['id'])}"
        assert isinstance(data["hitokoto"], str), f"hitokoto 应为 str"
        assert isinstance(data["type"], str), f"type 应为 str"
        assert isinstance(data["from"], str), f"from 应为 str"

        # 4. 业务逻辑
        assert len(data["hitokoto"]) > 0, "句子不应为空"
        assert data["type"] in CATEGORIES, (
            f"分类 '{data['type']}' 不在已知分类中"
        )

        print(f"\n  📝 句子: {data['hitokoto'][:60]}...")
        print(f"  📂 分类: {CATEGORIES.get(data['type'], '未知')}")
        print(f"  📖 来源: {data['from']}")


# ============================================================
# 分类过滤测试
# ============================================================

class TestHitokotoCategories:
    """测试不同分类的请求"""

    @pytest.mark.parametrize("category_key,category_name", [
        ("a", "动画"),
        ("d", "文学"),
        ("i", "诗词"),
        ("k", "哲学"),
    ])
    def test_category_filter(self, api, category_key, category_name):
        """数据驱动：测试指定分类返回正确"""
        data = api.get_sentence(category=category_key)

        assert data["type"] == category_key, (
            f"期望分类 {category_key}({category_name})，"
            f"实际 {data['type']}"
        )
        assert len(data["hitokoto"]) > 0, "句子不应为空"

        print(f"\n  [{category_name}] {data['hitokoto'][:50]}...")


# ============================================================
# 异常场景测试
# ============================================================

class TestHitokotoEdgeCases:
    """异常/边界场景"""

    def test_invalid_category_behavior(self, api):
        """
        测试无效分类参数的行为
        一言 API 对无效分类的处理策略：
        传入无效分类字母时，API 返回语句可能为 type=""，但 id 和 hitokoto 仍存在
        """
        data = api.get_sentence(category="z")  # 无效分类

        # API 应该返回 200（不会报错），核心字段还存在
        assert "hitokoto" in data, "即使无效分类，也应返回句子"
        assert len(data["hitokoto"]) > 0, "句子不应为空"

        print(f"\n  无效分类 'z' 返回 type='{data['type']}'")

    def test_multiple_requests_not_identical(self, api):
        """多次请求返回不同句子（随机性验证）"""
        sentences = set()
        for i in range(5):
            data = api.get_sentence()
            sentences.add(data["id"])

        # 5 次请求中至少有 2 个不同 ID（允许偶然重复，但概率极低）
        assert len(sentences) >= 2, (
            f"5 次请求应该返回不同句子，实际只有 {len(sentences)} 个不同 ID"
        )

        print(f"\n  5 次请求返回 {len(sentences)} 个不同句子")


# ============================================================
# 性能测试
# ============================================================

class TestHitokotoPerformance:
    """响应时间检查"""

    @pytest.mark.slow
    def test_response_time(self, api):
        """响应时间应在可接受范围内"""
        import time

        start = time.time()
        api.get_sentence()
        elapsed = time.time() - start

        assert elapsed < 3.0, f"响应时间 {elapsed:.2f}s 超过 3 秒上限"

        print(f"\n  ⏱ 响应时间: {elapsed:.3f}s")
