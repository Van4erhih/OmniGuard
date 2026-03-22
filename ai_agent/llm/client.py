import requests
from config import OPENROUTER_API_KEY, MODEL

def ask_llm(messages):
    try:
        print("⏳ Отправка запроса к модели...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": messages
            }
        )

        data = response.json()

        if "choices" not in data:
            print("LLM ERROR:", data)
            return "Ошибка API."

        print("✅ Ответ получен")

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("LLM ERROR:", e)
        return "Ошибка подключения."
