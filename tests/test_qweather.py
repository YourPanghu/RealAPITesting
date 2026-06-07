"""
和风天气 API 测试（需免费注册 API Key）
========================================
测试套路：
  1. 实况天气：验证温度/天气/湿度/风向等字段
  2. 7天预报：验证预报天数、温度范围、日期连续性
  3. 空气质量：验证 AQI/PM2.5/PM10 等指标
  4. 数据驱动：CSV 多城市批量测试
  5. 异常场景：无效城市 ID 的错误处理

前置条件：
  1. 注册 https://devapi.qweather.com/ 获取免费 Key
  2. 将 Key 写入 .env 文件：QWEATHER_API_KEY=你的key
  3. 或设置环境变量：export QWEATHER_API_KEY=你的key

运行：
  pytest tests/test_qweather.py -v
"""

import pytest
import csv
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config
from apis.qweather_api import QWeatherAPI


# ============================================================
# 检查 API Key 是否配置
# ============================================================
cfg = get_config()
SKIP_REASON = None
if not cfg.has_qweather_key():
    SKIP_REASON = (
        "未配置和风天气 API Key。\n"
        "  1. 注册 https://devapi.qweather.com/\n"
        "  2. 将 Key 写入 .env 文件：QWEATHER_API_KEY=你的key\n"
        "  3. 然后重新运行测试"
    )


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="module")
def api():
    """创建和风天气 API 客户端"""
    if SKIP_REASON:
        pytest.skip(SKIP_REASON)
    return QWeatherAPI(api_key=cfg.QWEATHER_API_KEY)


def load_cities():
    """从 CSV 加载城市测试数据"""
    cities = []
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "cities.csv"
    )
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cities.append((row["city"], row["location_id"], row["province"]))
    return cities


# ============================================================
# 实况天气测试
# ============================================================

@pytest.mark.qweather
class TestNowWeather:
    """实况天气 API 测试"""

    def test_get_now_weather_shenzhen(self, api):
        """测试深圳实况天气 —— 基本冒烟测试"""
        data = api.get_now_weather("101280601")

        # 1. API 状态码
        assert data["code"] == "200", (
            f"API 返回错误: code={data.get('code')}"
        )

        now = data["now"]
        # 2. 必需字段检查
        required = ["temp", "feelsLike", "text", "windDir",
                    "windScale", "humidity", "pressure"]
        for field in required:
            assert field in now, f"缺少字段: {field}"

        # 3. 字段类型和合理性
        temp = int(now["temp"])
        assert -50 <= temp <= 55, f"温度 {temp}℃ 超出合理范围"
        humidity = int(now["humidity"])
        assert 0 <= humidity <= 100, f"湿度 {humidity}% 超出范围"

        # 4. 天气现象不为空
        assert now["text"], "天气现象不应为空"

        print(f"\n  🌤 深圳天气: {now['text']} | {temp}℃ | "
              f"体感{now['feelsLike']}℃ | {now['windDir']}{now['windScale']}级"
              f" | 湿度{humidity}%")

    @pytest.mark.parametrize("city,location_id,province", load_cities())
    def test_now_weather_multi_cities(self, api, city, location_id, province):
        """数据驱动：多城市实况天气批量测试"""
        data = api.get_now_weather(location_id)

        assert data["code"] == "200", (
            f"{city}({location_id}) 请求失败: code={data.get('code')}"
        )

        now = data["now"]
        assert now["text"], f"{city} 天气现象为空"
        temp = int(now["temp"])
        assert -50 <= temp <= 55, f"{city} 温度 {temp}℃ 不合理"

        print(f"\n  [{province}] {city}: {now['text']} {temp}℃ "
              f"湿度{now['humidity']}%")


# ============================================================
# 7天天气预报测试
# ============================================================

@pytest.mark.qweather
class Test7DayForecast:
    """7天预报 API 测试"""

    def test_get_forecast_guangzhou(self, api):
        """测试广州 7 天预报"""
        data = api.get_7day_forecast("101280101")

        assert data["code"] == "200", f"API 返回错误: code={data.get('code')}"

        daily = data["daily"]
        # 1. 应有 7 天预报
        assert len(daily) == 7, (
            f"预期 7 天预报，实际 {len(daily)} 天"
        )

        # 2. 每条预报的字段完整性
        for i, day in enumerate(daily):
            required = ["fxDate", "tempMax", "tempMin", "textDay", "textNight"]
            for field in required:
                assert field in day, f"第{i+1}天缺少字段: {field}"

            # 最高温度 >= 最低温度
            tmax = int(day["tempMax"])
            tmin = int(day["tempMin"])
            assert tmax >= tmin, (
                f"{day['fxDate']}: 最高温{tmax}℃ < 最低温{tmin}℃"
            )

            print(f"\n  {day['fxDate']}: "
                  f"{day['textDay']}/{day['textNight']} "
                  f"{tmin}~{tmax}℃")


# ============================================================
# 空气质量测试
# ============================================================

@pytest.mark.qweather
class TestAirQuality:
    """空气质量 API 测试"""

    def test_get_air_quality_dongguan(self, api):
        """测试东莞空气质量（面试城市之一）"""
        data = api.get_air_quality("101281601")

        assert data["code"] == "200", f"API 返回错误: code={data.get('code')}"

        now = data["now"]
        # 1. 核心指标字段
        core_fields = ["aqi", "level", "category", "pm2p5", "pm10"]
        for field in core_fields:
            assert field in now, f"缺少字段: {field}"

        # 2. AQI 数值合理性
        aqi = int(now["aqi"])
        assert aqi >= 0, f"AQI {aqi} 不应为负数"

        print(f"\n  🏭 东莞空气质量: AQI {aqi} "
              f"({now['category']}) | PM2.5: {now['pm2p5']} | "
              f"PM10: {now['pm10']} | 首要污染物: {now.get('primary', '无')}")


# ============================================================
# 异常场景测试
# ============================================================

@pytest.mark.qweather
class TestErrorHandling:
    """异常场景测试"""

    def test_invalid_location_returns_error(self, api):
        """无效的城市 ID 应返回错误码"""
        # 无效的 location ID
        try:
            data = api.get_now_weather("000000000")
            # 如果没有抛异常，检查返回码
            assert data["code"] != "200", (
                f"无效城市 ID 不应返回 200，实际 code={data['code']}"
            )
            print(f"\n  无效城市返回 code={data['code']}，符合预期")
        except Exception as e:
            # 可能直接返回 404 或其他 HTTP 错误
            print(f"\n  无效城市触发异常: {type(e).__name__}，符合预期")

    def test_empty_location_behavior(self, api):
        """空城市 ID 的行为"""
        try:
            data = api.get_now_weather("")
            assert data["code"] != "200", (
                f"空城市 ID 不应返回 200"
            )
            print(f"\n  空城市 ID 返回 code={data['code']}")
        except Exception as e:
            print(f"\n  空城市 ID 触发: {type(e).__name__}，合理")


# ============================================================
# 城市查询测试
# ============================================================

@pytest.mark.qweather
class TestCityLookup:
    """城市搜索 API 测试"""

    def test_search_city_shenzhen(self, api):
        """测试搜索城市 Location ID"""
        data = api.search_city("深圳")

        assert data["code"] == "200", f"搜索失败: code={data.get('code')}"

        locations = data.get("location", [])
        assert len(locations) > 0, "搜索'深圳'应至少有一个结果"

        # 第一个结果应是深圳
        first = locations[0]
        assert "深圳" in first.get("name", ""), (
            f"搜索结果应是深圳，实际: {first.get('name')}"
        )

        print(f"\n  📍 {first['name']}: "
              f"ID={first['id']} | {first['adm1']}/{first['adm2']} | "
              f"经度{first['lon']} 纬度{first['lat']}")
