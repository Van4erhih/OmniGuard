from .base import BaseTool
from .marketplace_parser import parsers_registry
from .excel_generator import ExcelGenerator

class MarketplaceParserTool(BaseTool):
    """Инструмент для парсинга маркетплейсов"""
    
    name = "marketplace_parser"
    description = "Парсит товары с Озона, Валберис и Яндекс Маркета по запросу"
    
    def __init__(self):
        self.excel_gen = ExcelGenerator()
    
    def run(self, query: str, marketplace: str = None, **kwargs):
        """
        Args:
            query: поисковый запрос (например, "ноутбук")
            marketplace: конкретный маркетплейс (ozon, wildberries, yandex_market) или None для всех
        """
        
        if not query or len(query) < 2:
            return "❌ Запрос слишком короткий. Введите минимум 2 символа."
        
        try:
            if marketplace:
                results = {marketplace: parsers_registry.parse_marketplace(marketplace, query)}
            else:
                results = parsers_registry.parse_all(query)
            
            # Подготовить текст ответа
            response = f"🛍️ Результаты поиска: '{query}'\n\n"
            
            total_products = 0
            all_products = []
            
            for market_name, products in results.items():
                if not products:
                    response += f"❌ {market_name}: товары не найдены\n"
                    continue
                
                response += f"✅ {market_name.upper()}:\n"
                
                for idx, product in enumerate(products, 1):
                    response += (
                        f"  {idx}. {product['name']}\n"
                        f"     Цена: {product['price']} ₽\n"
                    )
                    total_products += 1
                    all_products.append(product)
                
                response += "\n"
            
            # Создать Excel с результатами если есть товары
            if all_products:
                response += "\n📊 Создаю Excel отчёт с результатами...\n"
                filepath = self.excel_gen.create_product_analysis(all_products)
                response += f"✅ Файл создан: {filepath}"
            
            return response
        
        except Exception as e:
            return f"❌ Ошибка при парсинге: {str(e)}"

class PriceComparisonTool(BaseTool):
    """Инструмент для сравнения цен между маркетплейсами"""
    
    name = "price_comparison"
    description = "Сравнивает цены товара на разных маркетплейсах"
    
    def __init__(self):
        self.excel_gen = ExcelGenerator()
    
    def run(self, product_name: str, **kwargs):
        """
        Args:
            product_name: название товара для сравнения
        """
        
        if not product_name or len(product_name) < 2:
            return "❌ Название товара слишком короткое."
        
        try:
            # Получить цены со всех маркетплейсов
            results = parsers_registry.parse_all(product_name)
            
            comparison_data = []
            
            # Группировать товары для сравнения
            product_dict = {}
            
            for marketplace, products in results.items():
                for product in products[:1]:  # Берём первый результат с каждого маркета
                    key = product['name'][:30]  # Укоротить для группировки
                    
                    if key not in product_dict:
                        product_dict[key] = {
                            'name': key,
                            'ozon': '-',
                            'wildberries': '-',
                            'yandex_market': '-'
                        }
                    
                    if marketplace == 'ozon':
                        product_dict[key]['ozon'] = product['price']
                    elif marketplace == 'wildberries':
                        product_dict[key]['wildberries'] = product['price']
                    elif marketplace == 'yandex_market':
                        product_dict[key]['yandex_market'] = product['price']
            
            # Вычислить минимальные цены
            for key in product_dict:
                prices = [
                    product_dict[key]['ozon'],
                    product_dict[key]['wildberries'],
                    product_dict[key]['yandex_market']
                ]
                prices = [p for p in prices if p != '-']
                
                if prices:
                    min_price = min(prices)
                    product_dict[key]['min_price'] = min_price
                    
                    # Найти где минимальная цена
                    if product_dict[key]['ozon'] == min_price:
                        product_dict[key]['best_marketplace'] = 'Озон'
                    elif product_dict[key]['wildberries'] == min_price:
                        product_dict[key]['best_marketplace'] = 'Валберис'
                    else:
                        product_dict[key]['best_marketplace'] = 'Яндекс Маркет'
            
            comparison_data = list(product_dict.values())
            
            # Создать отчёт
            response = f"💰 Сравнение цен для: '{product_name}'\n\n"
            
            for item in comparison_data:
                response += f"{item['name']}:\n"
                response += f"  Озон: {item['ozon']} ₽\n"
                response += f"  Валберис: {item['wildberries']} ₽\n"
                response += f"  Яндекс: {item['yandex_market']} ₽\n"
                response += f"  🏆 Лучшее предложение: {item['best_marketplace']} ({item['min_price']} ₽)\n\n"
            
            # Создать Excel
            response += "\n📊 Создаю Excel отчёт...\n"
            filepath = self.excel_gen.create_price_comparison(comparison_data)
            response += f"✅ Файл сравнения цен: {filepath}"
            
            return response
        
        except Exception as e:
            return f"❌ Ошибка при сравнении цен: {str(e)}"

class CustomReportTool(BaseTool):
    """Инструмент для создания пользовательских Excel отчётов"""
    
    name = "custom_report"
    description = "Создаёт пользовательский Excel отчёт по заданным параметрам"
    
    def __init__(self):
        self.excel_gen = ExcelGenerator()
    
    def run(self, title: str, data: str, **kwargs):
        """
        Args:
            title: название отчёта
            data: JSON или текстовое представление данных
        """
        
        try:
            # Попытаться распарсить JSON
            import json
            if data.startswith('{') or data.startswith('['):
                parsed_data = json.loads(data)
            else:
                return "❌ Данные должны быть в формате JSON"
            
            response = f"📝 Создаю отчёт: {title}\n"
            
            # Если это список списков - прямо генерировать
            if isinstance(parsed_data, list) and len(parsed_data) > 0:
                if isinstance(parsed_data[0], list):
                    # Определить колонки из первой строки (если строка содержит скаляры)
                    columns = [f"Колонка {i+1}" for i in range(len(parsed_data[0]))]
                    filepath = self.excel_gen.create_custom_report(title, columns, parsed_data)
                    response += f"✅ Отчёт создан: {filepath}"
                    return response
            
            return "❌ Неподдерживаемый формат данных"
        
        except Exception as e:
            return f"❌ Ошибка при создании отчёта: {str(e)}"
