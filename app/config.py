# -*- coding: utf-8 -*-
"""全局配置:从 .env 与环境变量读取"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


def _load_env() -> None:
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


_load_env()

# DeepSeek 通道(批量生成:抽认卡/模拟题)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_TIMEOUT = float(os.getenv("DEEPSEEK_TIMEOUT", "180"))

# 知乎直答通道(划重点核心:先检索后生成,有依据)
ZHIDA_MODEL = os.getenv("ZHIDA_MODEL", "zhida-thinking-1p5")

# zhihu-cli 路径(官方 Skill 安装位置,可用环境变量覆盖)
ZHIHU_CLI = os.getenv(
    "ZHIHU_CLI",
    r"C:\Users\chen\AppData\Local\ZhihuCLI\current\zhihu-cli.exe",
)
