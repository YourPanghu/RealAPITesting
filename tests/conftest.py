"""
Pytest 全局配置 —— RealAPITesting
=================================
提供共享的 fixtures 和测试配置。

Fixture 概念（回顾）：
- fixture 是 pytest 的"共享工具箱"
- scope="session"：整个测试会话共用（API 客户端这种无状态的对象）
- scope="function"：每个测试函数独立（需要隔离的场景）
"""

import pytest
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config


# ============================================================
# Session 级 Fixtures
# ============================================================

@pytest.fixture(scope="session")
def config():
    """
    全局配置（整个测试会话共用）
    从 .env 文件读取 API Key
    """
    return get_config()


# ============================================================
# 测试报告增强
# ============================================================

def pytest_configure(config):
    """Pytest 启动时调用 —— 自定义配置"""
    config.addinivalue_line(
        "markers",
        "slow: 标记为慢速测试（需要网络请求，耗时较长）"
    )


# ============================================================
# 自动跳过没有 Key 的测试
# ============================================================
# 这个 check 在 test_qweather.py 和 test_juhe.py 的 module scope
# fixture 中处理，更灵活。如果要用全局 conftest 统一跳过，可以
# 在 pytest_collection_modifyitems 中实现。
