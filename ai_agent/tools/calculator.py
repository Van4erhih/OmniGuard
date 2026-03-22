from .base import BaseTool

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Выполняет математические вычисления"

    def run(self, expression: str):
        try:
            result = eval(expression, {"__builtins__": {}})
            return f"Результат: {result}"
        except Exception:
            return "Ошибка вычисления."
