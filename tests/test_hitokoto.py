"""
==========================================================================
一言 API 测试（无需 Key，开箱即用！）
==========================================================================
这是三个 API 中唯一不需要注册的，新手先跑它建立信心！

测试套路（这是 API 自动化测试的标准五步法）：
  ① 状态码检查 → 200 OK（或通过 raise_for_status 隐式检查）
  ② 响应结构检查 → 必需字段都存在（data["xxx"] 不报 KeyError）
  ③ 字段类型检查 → id 是 int、hitokoto 是 str（类型不对说明接口变了）
  ④ 业务逻辑检查 → 句子不为空、分类在合法范围内
  ⑤ 异常场景测试 → 无效分类参数能否正确处理

参考面试话术：
  "我先跑冒烟测试确认 API 通不通，然后验证响应结构和字段类型，
   再覆盖业务逻辑和异常场景。每一步都有断言，失败能快速定位问题。"

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
    """
    创建一言 API 客户端（module 级别复用）

    为什么用 module scope？
    - HitokotoAPI 是无状态的，多个测试共享一个实例完全安全
    - 避免每个测试函数都 new 一个对象，减少 GC 压力
    - 如果将来需要隔离（比如登录态），可以改成 function scope
    """
    return HitokotoAPI()


# ============================================================
# 基础功能测试
# ============================================================

class TestHitokotoBasic:
    """基础请求测试 —— 验证 API 是否可用"""

    def test_get_random_sentence(self, api):
        """
        冒烟测试 —— 获取随机句子，验证完整响应结构

        这是整个项目最核心的测试方法，展示了 API 测试的标准套路：
        ① HTTP 状态码（API 客户端的 raise_for_status 已处理）
        ② 响应字段存在性（用循环断言 required_fields）
        ③ 字段类型正确性（isinstance 检查，类型不对说明接口改了）
        ④ 业务数据合理性（句子非空、分类合法）
        """
        data = api.get_sentence()

        # ① HTTP 状态码 —— API 客户端中 raise_for_status 已检查，200 才往下走

        # ② 响应结构检查：所有必需字段必须存在
        required_fields = ["id", "uuid", "hitokoto", "type", "from", "creator"]
        for field in required_fields:
            assert field in data, f"缺少必需字段: {field}"

        # ③ 字段类型检查：API 返回的字段类型必须和文档一致
        assert isinstance(data["id"], int), f"id 应为 int，实际 {type(data['id'])}"
        assert isinstance(data["hitokoto"], str), f"hitokoto 应为 str"
        assert isinstance(data["type"], str), f"type 应为 str"
        assert isinstance(data["from"], str), f"from 应为 str"

        # ④ 业务逻辑检查：数据在业务上必须合理
        assert len(data["hitokoto"]) > 0, "句子不应为空"
        assert data["type"] in CATEGORIES, (
            f"分类 '{data['type']}' 不在已知分类中"
        )

        # print 输出帮助开发者快速看到返回了什么（不参与断言）
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
