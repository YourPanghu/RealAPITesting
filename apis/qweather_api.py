"""
和风天气 API 客户端
==================
和风天气（devapi.qweather.com）：免费注册，1000次/天调用额度。
这是国内最常用的天气 API 之一，适合练手真实 API 测试。

注册地址：https://devapi.qweather.com/
文档地址：https://devapi.qweather.com/v7/

城市 Location ID 格式：101XXXXXX（前3位省级，后6位城市级）
示例：北京=101010100，广州=101280101，深圳=101280601
"""

import requests
from typing import Optional


class QWeatherAPI:
    """和风天气 API 客户端"""

    def __init__(self, api_key: str, base_url: str = "https://devapi.qweather.com/v7",
                 timeout: int = 10):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    def _get(self, endpoint: str, **params) -> dict:
        """
        通用 GET 请求 —— 所有 API 调用的统一入口

        自动附加 API Key 到请求参数中，让上层方法不用每次传 key。
        这是 API 客户端封装的核心：把重复的认证/URL拼接/错误处理集中到一处。

        Args:
            endpoint: API 路径，如 "weather/now"、"air/now"
            **params: 业务参数，如 location、keyword 等

        Returns:
            解析后的 JSON 字典

        Raises:
            requests.HTTPError: HTTP 状态码非 2xx 时抛出
        """
        # 自动注入 API Key（和风天气的认证方式：参数中传 key）
        params["key"] = self.api_key
        url = f"{self.base_url}/{endpoint}"
        resp = requests.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()  # 非 200 直接抛异常，测试用例不用手动检查状态码
        return resp.json()

    # ============================================================
    # 实况天气
    # ============================================================
    def get_now_weather(self, location: str) -> dict:
        """
        获取指定城市的实况天气

        Args:
            location: 城市 Location ID（如 "101280601"=深圳）

        Returns:
            {
                "code": "200",
                "now": {
                    "temp": "28",         # 温度（℃）
                    "feelsLike": "30",    # 体感温度
                    "text": "晴",          # 天气现象
                    "windDir": "东南风",   # 风向
                    "windScale": "3",     # 风力等级
                    "humidity": "65",     # 相对湿度
                    "pressure": "1010"    # 气压（hPa）
                }
            }
        """
        return self._get("weather/now", location=location)

    # ============================================================
    # 7天天气预报
    # ============================================================
    def get_7day_forecast(self, location: str) -> dict:
        """
        获取7天天气预报

        Returns:
            {
                "code": "200",
                "daily": [
                    {
                        "fxDate": "2024-01-01",
                        "tempMax": "25",
                        "tempMin": "15",
                        "textDay": "晴",
                        "textNight": "多云",
                        ...
                    },
                    ...
                ]
            }
        """
        return self._get("weather/7d", location=location)

    # ============================================================
    # 空气质量
    # ============================================================
    def get_air_quality(self, location: str) -> dict:
        """
        获取当前空气质量

        Returns:
            {
                "code": "200",
                "now": {
                    "aqi": "50",       # 空气质量指数
                    "level": "1",      # 等级
                    "category": "优",   # 类别
                    "primary": "PM10", # 首要污染物
                    "pm2p5": "30",
                    "pm10": "50",
                    ...
                }
            }
        """
        return self._get("air/now", location=location)

    # ============================================================
    # 城市信息查询
    # ============================================================
    def search_city(self, keyword: str) -> dict:
        """
        搜索城市 Location ID

        Args:
            keyword: 城市名（中文或拼音），如 "深圳" 或 "shenzhen"
        """
        return self._get("city/lookup", location=keyword)
