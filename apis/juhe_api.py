"""
聚合数据 API 客户端
==================
聚合数据（juhe.cn）：国内最大的 API 聚合平台，提供数百个免费接口。
注册后获取 AppKey，大多数接口有免费调用次数。

注册地址：https://www.juhe.cn/
文档地址：https://www.juhe.cn/docs

本模块封装两个常用免费接口：
  1. 笑话大全 —— 随机获取笑话
  2. 新闻头条 —— 获取最新新闻
"""

import requests
from typing import Optional


class JuheAPI:
    """聚合数据 API 客户端"""

    def __init__(self, api_key: str, base_url: str = "https://v.juhe.cn",
                 timeout: int = 10):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    def _get(self, endpoint: str, **params) -> dict:
        """
        通用 GET 请求 —— 所有 API 调用的统一入口

        自动附加 key（聚合数据的认证方式）到请求参数中。
        集中处理 URL 拼接、超时、异常，上层方法只需关心业务参数。

        Args:
            endpoint: API 路径，如 "joke/content/list.php"、"toutiao/index"
            **params: 业务参数，如 page、news_type 等

        Returns:
            解析后的 JSON 字典（聚合数据格式：{"error_code": 0, "reason": "...", "result": {...}}）

        Raises:
            requests.HTTPError: HTTP 状态码非 2xx 时抛出
        """
        # 自动注入 AppKey（聚合数据的认证方式：参数中传 key）
        params["key"] = self.api_key
        url = f"{self.base_url}/{endpoint}"
        resp = requests.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()  # 非 200 直接抛异常
        return resp.json()

    # ============================================================
    # 笑话大全
    # ============================================================
    def get_jokes(self, page: int = 1, pagesize: int = 5,
                  sort: str = "desc", time: str = "") -> dict:
        """
        获取笑话列表

        Args:
            page: 页码
            pagesize: 每页条数（最大 20）
            sort: 排序（desc=最新，asc=最早）
            time: 时间戳（用于分页）

        Returns:
            {
                "error_code": 0,
                "reason": "Success",
                "result": {
                    "data": [
                        {"content": "笑话内容...", "hashId": "...", "updatetime": "..."},
                        ...
                    ]
                }
            }
        """
        params = {
            "page": page,
            "pagesize": pagesize,
            "sort": sort,
        }
        if time:
            params["time"] = time
        return self._get("joke/content/list.php", **params)

    # ============================================================
    # 新闻头条
    # ============================================================
    def get_news(self, news_type: str = "top",
                 page: int = 1, page_size: int = 10) -> dict:
        """
        获取新闻头条

        Args:
            news_type: 新闻类型
                top=推荐, guonei=国内, guoji=国际,
                yule=娱乐, tiyu=体育, junshi=军事,
                keji=科技, caijing=财经, shishang=时尚
            page: 页码
            page_size: 每页条数

        Returns:
            {
                "error_code": 0,
                "reason": "成功",
                "result": {
                    "stat": "1",
                    "data": [
                        {
                            "title": "新闻标题",
                            "date": "2024-01-01",
                            "author_name": "来源",
                            "url": "详情链接",
                            "category": "分类"
                        },
                        ...
                    ]
                }
            }
        """
        params = {
            "type": news_type,
            "page": page,
            "page_size": page_size,
        }
        return self._get("toutiao/index", **params)

    # ============================================================
    # 辅助方法
    # ============================================================
    def is_success(self, response: dict) -> bool:
        """检查聚合数据 API 返回是否成功"""
        return response.get("error_code") == 0
