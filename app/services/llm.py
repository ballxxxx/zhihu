# -*- coding: utf-8 -*-
"""LLM 双通道统一接口。

- DeepSeekChannel:批量生成(抽认卡、模拟题),额度不受官方限制
- ZhidaChannel:知乎直答,先检索知乎内容再生成,自带依据(划重点核心)
"""
import json
import re

import httpx

from app import config
from app.services import zhihu


class LLMError(RuntimeError):
    pass


def _extract_json(text: str) -> dict:
    """从模型输出中稳健提取 JSON 对象(容忍 ```json 代码块包裹)。"""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            return json.loads(match.group(0))
        raise LLMError("无法从模型输出中解析 JSON")


class BaseChannel:
    name = "base"

    def chat(self, prompt: str) -> str:
        raise NotImplementedError

    def chat_json(self, prompt: str, retries: int = 2) -> dict:
        """要求模型输出 JSON;解析失败时带纠错提示重试。"""
        last_err: Exception | None = None
        current = prompt
        for _ in range(retries + 1):
            try:
                return _extract_json(self.chat(current))
            except (json.JSONDecodeError, LLMError) as exc:
                last_err = exc
                current = (
                    prompt
                    + "\n\n(上次输出无法解析为 JSON,请直接输出一个合法的 JSON 对象,不要输出任何其他文字)"
                )
        raise LLMError(f"{self.name} 多次尝试仍无法输出合法 JSON: {last_err}")


class DeepSeekChannel(BaseChannel):
    """DeepSeek chat completions(OpenAI 兼容)。"""

    name = "deepseek"

    def __init__(self) -> None:
        if not config.DEEPSEEK_API_KEY:
            raise LLMError("缺少 DEEPSEEK_API_KEY,请在项目 .env 中配置")
        self.base_url = config.DEEPSEEK_BASE_URL.rstrip("/")
        self.model = config.DEEPSEEK_MODEL

    def chat(self, prompt: str, temperature: float = 0.3, timeout: int | None = None) -> str:
        timeout = timeout if timeout is not None else config.DEEPSEEK_TIMEOUT
        try:
            resp = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {config.DEEPSEEK_API_KEY}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                },
                timeout=timeout,
            )
        except httpx.HTTPError as exc:
            # 超时/连接失败统一包装成 LLMError,让路由层按 502 优雅降级而不是 500
            raise LLMError(f"DeepSeek 请求失败({type(exc).__name__})") from exc
        if resp.status_code != 200:
            raise LLMError(f"DeepSeek 请求失败 {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"]


class ZhidaChannel(BaseChannel):
    """知乎直答(通过 zhihu-cli)。返回结构实测后解析。"""

    name = "zhida"

    def __init__(self) -> None:
        self.model = config.ZHIDA_MODEL

    def chat(self, prompt: str, timeout: int = 180) -> str:
        raw = zhihu.answer(prompt, model=self.model, timeout=timeout)
        data = json.loads(raw)
        return self._parse_answer(data)

    @staticmethod
    def _parse_answer(data: dict) -> str:
        # 实测返回为 OpenAI chat.completions 兼容结构
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            content = choices[0].get("message", {}).get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
        raise LLMError(f"直答返回结构未识别: {json.dumps(data, ensure_ascii=False)[:300]}")


def get_channel(name: str) -> BaseChannel:
    channels = {
        "deepseek": DeepSeekChannel,
        "zhida": ZhidaChannel,
    }
    if name not in channels:
        raise LLMError(f"未知通道 {name},可选: {list(channels)}")
    return channels[name]()
