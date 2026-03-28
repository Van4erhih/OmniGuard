from .unit_converter import UnitConverterTool
from .calculator import CalculatorTool
from .marketplace_tools import (
    MarketplaceParserTool,
    PriceComparisonTool,
    CustomReportTool
)

TOOLS = {
    "calculator": CalculatorTool(),
    "unit_converter": UnitConverterTool(),
    "marketplace_parser": MarketplaceParserTool(),
    "price_comparison": PriceComparisonTool(),
    "custom_report": CustomReportTool(),
}
