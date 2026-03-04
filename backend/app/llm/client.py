import time
import logging
from zai import ZhipuAiClient
from app.config import get_settings

logger = logging.getLogger("llm")
settings = get_settings()
_client = ZhipuAiClient(api_key=settings.ZHIPUAI_API_KEY)


def chat_completion(
    messages: list[dict],
    temperature: float = 0.6,
    model: str = "glm-5",
    label: str = "",
) -> str:
    tag = f"[{label}] " if label else ""
    prompt_preview = messages[-1]["content"][:80] if messages else ""
    logger.info(f"{tag}LLM 调用开始 | prompt: {prompt_preview}...")

    start = time.time()
    response = _client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        thinking={"type": "disabled"}, # 这里取消thinking会快一点
    )
    elapsed = time.time() - start
    content = response.choices[0].message.content
    logger.info(f"{tag}LLM 调用完成 | 耗时: {elapsed:.1f}s | 回复长度: {len(content)}")
    return content


def llm_call(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.6,
    label: str = "",
) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return chat_completion(messages, temperature=temperature, label=label)
