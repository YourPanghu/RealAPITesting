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

多 Key 支持：
  聚合数据每个接口需要单独订阅，不同接口可能用不同的 Key。
  支持传入多个 Key（列表或逗号分隔字符串），请求失败时自动
  切换到下一个 Key 重试。
"""

import requests
from typing import Optional, List, Union


class JuheAPI:
    """聚合数据 API 客户端（支持多 Key 自动切换）"""

    # 需要切换 Key 重试的错误码（认证/权限类，换 Key 可能解决）
    _AUTH_ERROR_CODES = {10001, 10002, 10003, 10008, 10009}

    def __init__(self, api_key: Union[str, List[str]] = None,
                 api_keys: List[str] = None,
                 base_url: str = "https://v.juhe.cn",
                 timeout: int = 10):
        """
        Args:
            api_key: 单个 Key 或逗号分隔的多个 Key（向后兼容）
            api_keys: Key 列表（优先级高于 api_key）
            base_url: API 基础地址
            timeout: 请求超时秒数
        """
        # 解析 Key 列表
        if api_keys:
            self.api_keys = api_keys
        elif api_key:
            if isinstance(api_key, str) and "," in api_key:
                self.api_keys = [k.strip() for k in api_key.split(",") if k.strip()]
            elif isinstance(api_key, list):
                self.api_keys = api_key
            else:
                self.api_keys = [api_key]
        else:
            self.api_keys = []

        self.base_url = base_url
        self.timeout = timeout
        # 记录每个 Key 的最后一次使用，方便调试
        self._key_usage = {k: 0 for k in self.api_keys}

    def _get(self, endpoint: str, **params) -> dict:
        """
        通用 GET 请求（带多 Key 自动切换）

        先尝试用第一个 Key 请求，如果返回认证类错误（10001 等），
        自动切换到下一个 Key 重试，直到成功或所有 Key 都失败。

        Args:
            endpoint: API 路径
            **params: 业务参数

        Returns:
            解析后的 JSON 字典

        Raises:
            requests.HTTPError: HTTP 非 2xx 时抛出
        """
        last_response = None
        last_error = None

        for i, key in enumerate(self.api_keys):
            params["key"] = key
            url = f"{self.base_url}/{endpoint}"

            try:
                resp = requests.get(url, params=params, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()

                error_code = data.get("error_code")
                # 成功（error_code == 0）直接返回
                if error_code == 0:
                    self._key_usage[key] += 1
                    return data

                # 认证类错误 → 尝试下一个 Key
                if error_code in self._AUTH_ERROR_CODES:
                    last_response = data
                    if i < len(self.api_keys) - 1:
                        continue  # 还有 Key 可试
                    else:
                        # 所有 Key 都试过了
                        return data

                # 非认证类错误（如参数错误 209501）→ 不切换 Key，直接返回
                return data

            except requests.HTTPError as e:
                last_error = e
                # 403 可能是 Key 无效，尝试下一个
                if resp.status_code == 403 and i < len(self.api_keys) - 1:
                    continue
                raise

        # 所有 Key 都失败
        if last_response:
            return last_response
        if last_error:
            raise last_error
        return {"error_code": -1, "reason": "无可用 API Key"}

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
            time: 时间戳（10位Unix秒级），默认当前时间。用于分页翻页，
                  传入上一页最后一条的 unixtime 即可获取更早的数据

        Returns:
            {
                "error_code": 0,
                "reason": "Success",
                "result": {
                    "data": [
                        {"content": "笑话内容...", "hashId": "...",
                         "unixtime": ..., "updatetime": "..."},
                        ...
                    ]
                }
            }
        """
        import time as _time
        params = {
            "page": page,
            "pagesize": pagesize,
            "sort": sort,
            # 聚合数据新版笑话 API 要求必传 time 参数（10位Unix时间戳）
            "time": time if time else str(int(_time.time())),
        }
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

    @property
    def active_keys_count(self) -> int:
        """返回成功使用过的 Key 数量"""
        return sum(1 for v in self._key_usage.values() if v > 0)
