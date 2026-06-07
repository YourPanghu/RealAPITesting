"""
配置管理模块
============
从 .env 文件读取 API Key，提供统一的配置入口。

用法：
    from config import get_config
    cfg = get_config()
    api_key = cfg.QWEATHER_API_KEY
"""

import os
from pathlib import Path

# 项目根目录（config.py 所在目录）
ROOT_DIR = Path(__file__).parent


class Config:
    """应用配置，从环境变量/.env 读取"""

    def __init__(self):
        # 尝试加载 .env 文件
        self._load_dotenv()

        # ============================================================
        # 和风天气配置
        # ============================================================
        self.QWEATHER_API_KEY = os.getenv("QWEATHER_API_KEY", "")
        self.QWEATHER_BASE_URL = "https://devapi.qweather.com/v7"

        # ============================================================
        # 聚合数据配置
        # ============================================================
        self.JUHE_API_KEY = os.getenv("JUHE_API_KEY", "")
        self.JUHE_BASE_URL = "https://v.juhe.cn"

        # ============================================================
        # 一言配置（无需 Key）
        # ============================================================
        self.HITOKOTO_BASE_URL = "https://v1.hitokoto.cn"

    def _load_dotenv(self):
        """尝试加载 .env 文件（python-dotenv 可选）"""
        try:
            from dotenv import load_dotenv
            env_path = ROOT_DIR / ".env"
            if env_path.exists():
                load_dotenv(env_path)
        except ImportError:
            pass  # python-dotenv 未安装，直接读环境变量

    def has_qweather_key(self) -> bool:
        """检查是否配置了和风天气 Key"""
        return bool(self.QWEATHER_API_KEY and
                    "your_" not in self.QWEATHER_API_KEY)

    def has_juhe_key(self) -> bool:
        """检查是否配置了聚合数据 Key"""
        return bool(self.JUHE_API_KEY and
                    "your_" not in self.JUHE_API_KEY)


# 全局单例
_config = None


def get_config() -> Config:
    """获取配置单例"""
    global _config
    if _config is None:
        _config = Config()
    return _config
