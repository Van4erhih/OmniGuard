from .base import BaseTool


class UnitConverterTool(BaseTool):
    name = "unit_converter"
    description = "Конвертирует единицы измерения (длина, вес, температура)"

    def run(self, value: float, from_unit: str, to_unit: str):

        conversions = {
            # Длина
            ("km", "m"): lambda x: x * 1000,
            ("m", "km"): lambda x: x / 1000,
            ("cm", "m"): lambda x: x / 100,
            ("m", "cm"): lambda x: x * 100,

            # Вес
            ("kg", "g"): lambda x: x * 1000,
            ("g", "kg"): lambda x: x / 1000,

            # Температура
            ("c", "f"): lambda x: (x * 9/5) + 32,
            ("f", "c"): lambda x: (x - 32) * 5/9,
        }

        key = (from_unit.lower(), to_unit.lower())

        if key not in conversions:
            return "Неподдерживаемая конвертация."

        try:
            result = conversions[key](value)
            return f"{value} {from_unit} = {round(result, 4)} {to_unit}"
        except Exception:
            return "Ошибка конвертации."
