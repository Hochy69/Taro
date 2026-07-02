from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AIResponse:
    text: str
    past: str
    present: str
    future: str
    advice: str
    conclusion: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    generation_time_ms: int = 0


class AIProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        pass


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            max_tokens=2000,
        )
        content = response.choices[0].message.content or ""
        usage = response.usage
        return (
            content,
            usage.prompt_tokens if usage else 0,
            usage.completion_tokens if usage else 0,
        )


class ClaudeProvider(AIProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key)
        response = await client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        content = response.content[0].text if response.content else ""
        return content, response.usage.input_tokens, response.usage.output_tokens


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model, system_instruction=system_prompt)
        response = await model.generate_content_async(user_prompt)
        content = response.text or ""
        return content, 0, 0


class OpenRouterProvider(AIProvider):
    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    async def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.8,
                    "max_tokens": 2000,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return content, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def get_ai_provider() -> AIProvider:
    from app.core.config import settings

    providers = {
        "openai": lambda: OpenAIProvider(settings.openai_api_key, settings.ai_model),
        "claude": lambda: ClaudeProvider(settings.anthropic_api_key, settings.ai_model),
        "gemini": lambda: GeminiProvider(settings.google_api_key, settings.ai_model),
        "openrouter": lambda: OpenRouterProvider(
            settings.openrouter_api_key, settings.ai_model, settings.openrouter_base_url
        ),
    }
    factory = providers.get(settings.ai_provider)
    if not factory:
        raise ValueError(f"Unknown AI provider: {settings.ai_provider}")
    return factory()
