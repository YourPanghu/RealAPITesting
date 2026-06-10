"""
和风天气 API 客户端
==================
和风天气（devapi.qweather.com）：免费注册，50,000次/月调用额度。
这是国内最常用的天气 API 之一，适合练手真实 API 测试。

注册地址：https://dev.qweather.com/
文档地址：https://dev.qweather.com/docs/

城市 Location ID 格式：101XXXXXX（前3位省级，后6位城市级）
示例：北京=101010100，广州=101280101，深圳=101280601

注意：
  - 天气类 API（实况/预报/空气质量）使用 https://devapi.qweather.com/v7
  - 地理类 API（城市搜索）使用 https://geoapi.qweather.com/v2
"""

import requests
from typing import Optional


class QWeatherAPI:
    """和风天气 API 客户端"""

    # 和风天气有两套 API Host：
    #   - devapi.qweather.com：天气数据（实况/预报/空气质量/预警等）
    #   - geoapi.qweather.com：地理信息（城市搜索等）
    WEATHER_BASE = "https://devapi.qweather.com/v7"
    GEO_BASE = "https://geoapi.qweather.com/v2"

    def __init__(self, api_key: str,
                 weather_base_url: str = None,
                 geo_base_url: str = None,
                 timeout: int = 10):
        self.api_key = api_key
        self.weather_base = weather_base_url or self.WEATHER_BASE
        self.geo_base = geo_base_url or self.GEO_BASE
        self.timeout = timeout

    def _get(self, base: str, endpoint: str, **params) -> dict:
        """
        通用 GET 请求 —— 所有 API 调用的统一入口

        自动附加 API Key 到请求参数中，让上层方法不用每次传 key。
        这是 API 客户端封装的核心：把重复的认证/URL拼接/错误处理集中到一处。

        Args:
            base: API 基础 URL（self.weather_base 或 self.geo_base）
            endpoint: API 路径，如 "weather/now"、"city/lookup"
            **params: 业务参数，如 location、keyword 等

        Returns:
            解析后的 JSON 字典

        Raises:
            requests.HTTPError: HTTP 状态码非 2xx 时抛出
        """
        params["key"] = self.api_key
        url = f"{base}/{endpoint}"
        resp = requests.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()  # 非 2xx 直接抛异常，测试用例不用手动检查状态码
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
        return self._get(self.weather_base, "weather/now", location=location)

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
        return self._get(self.weather_base, "weather/7d", location=location)

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
        return self._get(self.weather_base, "air/now", location=location)

    # ============================================================
    # 城市信息查询
    # ============================================================
    def search_city(self, keyword: str) -> dict:
        """
        搜索城市 Location ID

        使用 geoapi.qweather.com（地理信息 API），与天气 API 是不同的 Host。

        Args:
            keyword: 城市名（中文或拼音），如 "深圳" 或 "shenzhen"
        """
        return self._get(self.geo_base, "city/lookup", location=keyword)

    # ============================================================
    # 连接验证
    # ============================================================
    def verify_connection(self) -> tuple[bool, str]:
        """
        验证 API Key 是否有效

        发一个轻量请求（深圳实况天气）来检查 Key 是否可用。
        用于测试前置检查，避免所有测试都因为 Key 无效而失败。

        Returns:
            (is_valid, message): 是否可用及说明信息
        """
        try:
            data = self.get_now_weather("101280601")
            if data.get("code") == "200":
                return True, "API Key 有效"
            else:
                return False, f"API 返回错误: code={data.get('code')}"
        except requests.HTTPError as e:
            status = e.response.status_code if hasattr(e, 'response') else '?'
            return False, (
                f"API Key 验证失败 (HTTP {status})。\n"
                f"  请确认：\n"
                f"  1. 已在 https://dev.qweather.com/ 注册并完成实名认证\n"
                f"  2. 已在控制台创建项目和凭证（API Key）\n"
                f"  3. .env 中 QWEATHER_API_KEY 的值正确\n"
                f"  详细错误: {e}"
            )
        except Exception as e:
            return False, f"网络连接失败: {e}"
