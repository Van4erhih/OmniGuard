from agent.memory import get_history, add_message
from llm.client import ask_llm

class Agent:
    def __init__(self):
        self.system_prompt = (
            "Ты OmniGuard — персональный AI ассистент в Telegram.  "
            "Ты умный, спокойный и структурированный.  "
            "Даёшь чёткие и полезные ответы без воды.  "
            "Не раскрываешь внутренние размышления.  "
            "Не прощаешься в конце ответа.  "
            "Учитываешь историю общения и стиль пользователя."
        )

    def run(self, user_id: int, user_input: str):
        history = get_history(user_id)

        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_input})

        response = ask_llm(messages)

        add_message(user_id, "user", user_input)
        add_message(user_id, "assistant", response)

        return response