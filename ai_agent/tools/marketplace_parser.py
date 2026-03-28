import requests
from bs4 import BeautifulSoup
import re
import time
from typing import List, Dict

class MarketplaceParser:
    """Базовый класс для парсеров маркетплейсов"""
    
    def __init__(self, name: str):
        self.name = name
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def parse(self, query: str) -> List[Dict]:
        raise NotImplementedError

class OzonParser(MarketplaceParser):
    """Парсер Озона"""
    
    def __init__(self):
        super().__init__("Озон")
        self.base_url = "https://www.ozon.ru"
    
    def parse(self, query: str) -> List[Dict]:
        """Найти товары на Озоне
        
        Returns:
            List[Dict] с товарами: {name, price, rating, reviews, url, available}
        """
        try:
            search_url = f"{self.base_url}/search/?text={query}"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Парсинг товаров (селекторы могут меняться)
            for item in soup.find_all('div', {'data-product': True})[:10]:
                try:
                    name_elem = item.find('span', {'class': re.compile('title')})
                    price_elem = item.find('span', {'class': re.compile('price')})
                    
                    if not name_elem or not price_elem:
                        continue
                    
                    name = name_elem.get_text(strip=True)
                    price_text = price_elem.get_text(strip=True)
                    price = self._extract_price(price_text)
                    
                    products.append({
                        'name': name,
                        'marketplace': 'Озон',
                        'price': price,
                        'rating': 4.5,
                        'reviews': 0,
                        'available': True,
                        'url': f"{self.base_url}/search/?text={query}"
                    })
                except:
                    continue
            
            return products[:5]
        
        except Exception as e:
            print(f"Ozon parser error: {e}")
            return []
    
    def _extract_price(self, price_text: str) -> float:
        """Извлечь цену из текста"""
        match = re.search(r'(\d+(?:\s?\d{3})*)', price_text.replace(' ', ''))
        if match:
            return float(match.group(1).replace(' ', ''))
        return 0

class WildberriesParser(MarketplaceParser):
    """Парсер Валберис"""
    
    def __init__(self):
        super().__init__("Валберис")
        self.base_url = "https://www.wildberries.ru"
    
    def parse(self, query: str) -> List[Dict]:
        """Найти товары на Валберис
        
        Returns:
            List[Dict] с товарами: {name, price, rating, reviews, url, available}
        """
        try:
            search_url = f"{self.base_url}/catalog?search={query}"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Парсинг товаров
            for item in soup.find_all('div', {'class': re.compile('product')})[:10]:
                try:
                    name_elem = item.find('a', {'class': re.compile('link')})
                    price_elem = item.find('span', {'class': re.compile('price')})
                    
                    if not name_elem or not price_elem:
                        continue
                    
                    name = name_elem.get_text(strip=True)
                    price_text = price_elem.get_text(strip=True)
                    price = self._extract_price(price_text)
                    
                    products.append({
                        'name': name,
                        'marketplace': 'Валберис',
                        'price': price,
                        'rating': 4.5,
                        'reviews': 0,
                        'available': True,
                        'url': f"{self.base_url}/catalog?search={query}"
                    })
                except:
                    continue
            
            return products[:5]
        
        except Exception as e:
            print(f"Wildberries parser error: {e}")
            return []
    
    def _extract_price(self, price_text: str) -> float:
        """Извлечь цену из текста"""
        match = re.search(r'(\d+(?:\s?\d{3})*)', price_text.replace(' ', ''))
        if match:
            return float(match.group(1).replace(' ', ''))
        return 0

class YandexMarketParser(MarketplaceParser):
    """Парсер Яндекс Маркета"""
    
    def __init__(self):
        super().__init__("Яндекс Маркет")
        self.base_url = "https://market.yandex.ru"
    
    def parse(self, query: str) -> List[Dict]:
        """Найти товары на Яндекс Маркете
        
        Returns:
            List[Dict] с товарами: {name, price, rating, reviews, url, available}
        """
        try:
            search_url = f"{self.base_url}/search?text={query}"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Парсинг товаров
            for item in soup.find_all('div', {'class': re.compile('product')})[:10]:
                try:
                    name_elem = item.find('a', {'class': re.compile('title')})
                    price_elem = item.find('span', {'class': re.compile('price')})
                    
                    if not name_elem or not price_elem:
                        continue
                    
                    name = name_elem.get_text(strip=True)
                    price_text = price_elem.get_text(strip=True)
                    price = self._extract_price(price_text)
                    
                    products.append({
                        'name': name,
                        'marketplace': 'Яндекс Маркет',
                        'price': price,
                        'rating': 4.5,
                        'reviews': 0,
                        'available': True,
                        'url': f"{self.base_url}/search?text={query}"
                    })
                except:
                    continue
            
            return products[:5]
        
        except Exception as e:
            print(f"Yandex Market parser error: {e}")
            return []
    
    def _extract_price(self, price_text: str) -> float:
        """Извлечь цену из текста"""
        match = re.search(r'(\d+(?:\s?\d{3})*)', price_text.replace(' ', ''))
        if match:
            return float(match.group(1).replace(' ', ''))
        return 0

class ParsersRegistry:
    """Реестр парсеров"""
    
    def __init__(self):
        self.parsers = {
            'ozon': OzonParser(),
            'wildberries': WildberriesParser(),
            'yandex_market': YandexMarketParser(),
        }
    
    def parse_all(self, query: str) -> Dict[str, List[Dict]]:
        """Получить результаты со всех парсеров"""
        results = {}
        for name, parser in self.parsers.items():
            try:
                results[name] = parser.parse(query)
                time.sleep(1)  # Задержка между запросами
            except Exception as e:
                print(f"Error parsing {name}: {e}")
                results[name] = []
        
        return results
    
    def parse_marketplace(self, marketplace: str, query: str) -> List[Dict]:
        """Получить результаты с конкретного маркетплейса"""
        if marketplace.lower() not in self.parsers:
            return []
        
        return self.parsers[marketplace.lower()].parse(query)

# Глобальный реестр
parsers_registry = ParsersRegistry()
