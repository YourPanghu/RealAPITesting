"""
==========================================================================
RealAPITesting - Pytest 全局配置
==========================================================================
提供共享的 fixtures 和测试配置。

Fixture 机制回顾（这是 pytest 的核心能力）：
  - fixture 是 pytest 的"依赖注入"系统 —— 测试函数声明参数，pytest 自动注入
  - scope="session"：整个测试会话共用（适用于无状态对象，如 API 客户端）
  - scope="module"：同一个 .py 文件内共用
  - scope="function"：每个测试函数独立（默认值，适用于需要隔离的场景）

本文件包含：
  1. config fixture  —— 全局配置单例
  2. pytest_configure —— pytest 启动钩子，注册自定义 markers
  3. 路径处理        —— 确保项目根目录在 sys.path 中
"""

import pytest
import sys
import os

# ==================================================================
# 路径处理：确保项目根目录和 tests 目录都在 Python 搜索路径中
# 这样测试文件可以用 from apis.xxx import Xxx 来导入 API 客户端
# ==================================================================
# 当前文件所在目录（tests/）加到 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 项目根目录（tests/ 的父目录）加到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config


# ============================================================
# Session 级 Fixtures
# ============================================================

@pytest.fixture(scope="session")
def config():
    """
    全局配置 fixture（整个测试会话共用一个实例）

    session scope 的意义：
      - Config 是无状态对象，所有测试共享是安全的
      - .env 文件只加载一次，不重复 I/O
      - 如果改成 function scope，每个测试都会重新创建 Config，浪费时间
    """
    return get_config()


# ============================================================
# Pytest 启动钩子
# ============================================================

def pytest_configure(config):
    """
    Pytest 启动时自动调用的钩子函数

    注意：这里的参数名 config 是 pytest 的 Config 对象，
    不是上面我们定义的 config fixture。
    这个钩子用于注册自定义 markers，让 pytest.ini 中的 markers 定义有对应的描述。
    """
    config.addinivalue_line(
        "markers",
        "slow: 标记为慢速测试（需要网络请求，耗时较长）"
    )


# ============================================================
# 无 Key 自动跳过策略说明
# ============================================================
# 为什么不在 conftest 中统一跳过？
#
# 因为每个 API 的跳过逻辑不同：
#   - 一言不需要 Key → 永远不跳过
#   - 和风天气需要 QWEATHER_API_KEY
#   - 聚合数据需要 JUHE_API_KEY
#
# 统一跳过需要知道"当前测试用到哪个 API"，耦合度高。
# 所以把跳过逻辑放在各自的 test_xxx.py 的 module fixture 中，
# 每个模块自己判断是否有对应的 Key，更灵活。
