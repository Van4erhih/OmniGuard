from .unit_converter import UnitConverterTool

from .calculator import CalculatorTool

TOOLS = {
    "calculator": CalculatorTool(),
    "unit_converter": UnitConverterTool(),
}
