from huggingface_hub import InferenceClient

from src.config import HF_LLM_FALLBACK, HF_LLM_MODEL, HF_TOKEN
from src.generation.prompts import SYSTEM_PROMPT

DEFAULT_MAX_TOKENS = 256


class LLMClient:
    """Cloud-hosted text generation via Hugging Face Inference API."""

    def __init__(
        self,
        model: str | None = None,
        fallback_model: str | None = None,
        token: str | None = None,
    ):
        self.model = model or HF_LLM_MODEL
        self.fallback_model = fallback_model or HF_LLM_FALLBACK
        self.token = token or HF_TOKEN or None
        self.client = InferenceClient(token=self.token)

    def generate(self, user_prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        gen_kwargs = {
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "repetition_penalty": 1.15,
        }

        for model in (self.model, self.fallback_model):
            try:
                print(f"\nTrying chat model: {model}")

                response = self.client.chat_completion(
                    messages=messages,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0.1,
                )

                content = response.choices[0].message.content.strip()

                return content

            except Exception as e:
                print(f"\nChat completion failed for {model}")
                print(e)
                continue

        print("\n===== USING TEXT GENERATION FALLBACK =====")

        try:
            prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_prompt}\n\nAssistant:"

            response = self.client.text_generation(
                prompt,
                model=self.fallback_model,
                max_new_tokens=max_tokens,
                temperature=0.1,
                return_full_text=False,
            )


            return response.strip()

        except Exception as e:
            print("\n===== TEXT GENERATION FAILED =====")
            print(e)

            return f"Generation error: {e}"