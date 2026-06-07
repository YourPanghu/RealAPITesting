"""
一言 API 客户端
===============
一言（hitokoto.cn）：免费、无需注册、无需 Key 的随机句子 API。
这是三个 API 中最简单的，先跑它，建立信心！

API 文档：https://developer.hitokoto.cn/

示例请求：
    GET https://v1.hitokoto.cn/?c=d
    返回：{"id": 123, "hitokoto": "...", "from": "源名称", "from_who": "作者", ...}
"""

import requests
from typing import Optional

# ============================================================
# 参数说明
# ============================================================
CATEGORIES = {
    "a": "动画",
    "b": "漫画",
    "c": "游戏",
    "d": "文学",
    "e": "原创",
    "f": "来自网络",
    "g": "其他",
    "h": "影视",
    "i": "诗词",
    "j": "网易云",
    "k": "哲学",
    "l": "抖机灵",
}

BASE_URL = "https://v1.hitokoto.cn"


class HitokotoAPI:
    """一言 API 客户端"""

    def __init__(self, timeout: int = 10):
        self.base_url = BASE_URL
        self.timeout = timeout

    def get_sentence(self, category: Optional[str] = None) -> dict:
        """
        获取一句随机句子

        Args:
            category: 分类字母（a-l），None 表示不限制分类

        Returns:
            {
                "id": 句子ID,
                "uuid": "全局唯一ID",
                "hitokoto": "句子内容",
                "type": "分类字母",
                "from": "来源",
                "from_who": "作者（可能为null）",
                "creator": "提交者",
                "created_at": "创建时间"
            }
        """
        params = {}
        if category and category in CATEGORIES:
            params["c"] = category

        resp = requests.get(
            self.base_url,
            params=params,
            timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()

    def get_sentence_with_params(self, **kwargs) -> dict:
        """
        带自定义参数的请求（用于测试异常场景）

        Args:
            **kwargs: 传递给 API 的查询参数
        """
        resp = requests.get(
            self.base_url,
            params=kwargs,
            timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()
