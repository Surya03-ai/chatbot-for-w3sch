from __future__ import annotations

import time

import google.generativeai as genai


class GeminiModelClient:
    def __init__(self, model_names: list[str]):
        if not model_names:
            raise RuntimeError("No Gemini models available for generateContent")

        self.model_names = model_names
        self.current_index = 0
        self.model = self._create_model(self.model_names[self.current_index])

    @property
    def current_model_name(self) -> str:
        return self.model_names[self.current_index]

    def _create_model(self, model_name: str) -> genai.GenerativeModel:
        return genai.GenerativeModel(model_name)

    def switch_to_next_model(self) -> bool:
        for next_index in range(self.current_index + 1, len(self.model_names)):
            try:
                self.model = self._create_model(self.model_names[next_index])
                self.current_index = next_index
                return True
            except Exception:
                continue
        return False


def generate_answer(model: GeminiModelClient, prompt: str) -> str:
    retries = 3

    for attempt in range(retries):
        try:
            response = model.model.generate_content(prompt)
            answer = response.text if response.text is not None else ""
            print("=== RAW MODEL RESPONSE ===", response.text)
            answer = answer.strip()
            if not answer or len(answer) < 10:
                return "Sorry, I couldn't generate a proper response."
            return answer
        except Exception as error:
            error_text = str(error)
            if "429" in error_text:
                print("Rate limit hit, retrying...")
                time.sleep((2**attempt) * 10)
                continue
            raise

    return "Sorry, API is busy. Please try again later."


def configure_gemini(api_key: str, model_names: list[str]) -> GeminiModelClient:
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    genai.configure(api_key=api_key)
    return GeminiModelClient(model_names)
