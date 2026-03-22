import json
from llm.client import ask_llm


PLANNER_PROMPT = """
Ты планировщик инструментов AI-ассистента.

Твоя задача — определить, нужно ли вызвать инструмент.

Доступные инструменты:

1) calculator — математические вычисления
Аргументы:
{
  "expression": "2+2"
}

2) unit_converter — конвертация единиц измерения
Аргументы:
{
  "value": 10,
  "from_unit": "km",
  "to_unit": "m"
}
3) notes — личные заметки
Аргументы:
{
  "action": "add" или "list",
  "content": "текст заметки"
}

Если инструмент нужен — верни строго JSON:
{
  "tool": "название_инструмента",
  "args": {...}
}

Если инструмент не нужен — верни:
{
  "tool": null
}

Никакого текста. Только JSON.
"""


def decide(user_input: str):

    messages = [
        {"role": "system", "content": PLANNER_PROMPT},
        {"role": "user", "content": user_input}
    ]

    response = ask_llm(messages)

    try:
        decision = json.loads(response)
        return decision
    except Exception:
        return {"tool": None}
