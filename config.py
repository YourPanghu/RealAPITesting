"""
==========================================================================
RealAPITesting - 配置管理模块
==========================================================================
负责从 .env 文件和环境变量中读取 API Key，提供统一的配置入口。

核心理念：
  1. 配置集中管理 —— 所有 API Key 和 URL 在一个地方维护
  2. 安全 —— .env 文件不会提交到 Git（在 .gitignore 中）
  3. 无 Key 自动降级 —— 没配置 Key 的 API 测试自动 skip，不影响其他测试
  4. Key 安全校验 —— 拒绝示例占位符（如 "your_xxx_key_here"），防止误用

用法：
    from config import get_config
    cfg = get_config()
    api_key = cfg.QWEATHER_API_KEY              # 获取和风天气 Key
    has_key = cfg.has_qweather_key()            # 检查是否配置了有效 Key
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
        """
        尝试加载 .env 文件，将变量注入 os.environ
        python-dotenv 未安装时静默跳过，直接读系统环境变量
        """
        try:
            from dotenv import load_dotenv
            env_path = ROOT_DIR / ".env"
            if env_path.exists():
                load_dotenv(env_path)
        except ImportError:
            pass  # python-dotenv 未安装，直接读环境变量

    def has_qweather_key(self) -> bool:
        """
        检查是否配置了有效的和风天气 Key

        安全策略：
        1. Key 不能为空字符串
        2. Key 不能包含 "your_" —— 拒绝示例占位符（如 .env.example 中的值）
           （这很重要：防止有人忘记改 .env，用示例 Key 发请求）
        """
        return bool(self.QWEATHER_API_KEY and
                    "your_" not in self.QWEATHER_API_KEY)

    def has_juhe_key(self) -> bool:
        """检查是否配置了有效的聚合数据 Key（策略同 has_qweather_key）"""
        return bool(self.JUHE_API_KEY and
                    "your_" not in self.JUHE_API_KEY)


# ==================================================================
# 全局单例：确保整个测试会话共用同一个 Config 对象
# 好处：
#   1. .env 文件只解析一次，不重复 I/O
#   2. 多线程安全（单线程测试场景下）
# ==================================================================
_config: Config | None = None


def get_config() -> Config:
    """
    获取配置单例（线程安全 lazy-init）

    为什么用单例？
    - 测试模块多处调用 get_config() 时不会重复解析 .env
    - fixture scope="session" 天然保证了单例行为
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
