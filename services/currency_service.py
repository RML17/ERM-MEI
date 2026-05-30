"""
Serviço de Conversão de Moedas
Sistema completo para conversão internacional com cotações em tempo real
"""

import requests
import json
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
from app import db


class CurrencyService:
    """Serviço principal para conversão de moedas"""
    
    # Cache de cotações (evitar muitas chamadas à API)
    _cache = {}
    _cache_duration = timedelta(minutes=30)  # Cache por 30 minutos
    
    # Moedas principais suportadas
    SUPPORTED_CURRENCIES = {
        'USD': {'name': 'Dólar Americano', 'symbol': '$', 'flag': '🇺🇸'},
        'EUR': {'name': 'Euro', 'symbol': '€', 'flag': '🇪🇺'},
        'BRL': {'name': 'Real Brasileiro', 'symbol': 'R$', 'flag': '🇧🇷'},
        'GBP': {'name': 'Libra Esterlina', 'symbol': '£', 'flag': '🇬🇧'},
        'JPY': {'name': 'Iene Japonês', 'symbol': '¥', 'flag': '🇯🇵'},
        'CAD': {'name': 'Dólar Canadense', 'symbol': 'C$', 'flag': '🇨🇦'},
        'AUD': {'name': 'Dólar Australiano', 'symbol': 'A$', 'flag': '🇦🇺'},
        'CHF': {'name': 'Franco Suíço', 'symbol': 'CHF', 'flag': '🇨🇭'},
        'CNY': {'name': 'Yuan Chinês', 'symbol': '¥', 'flag': '🇨🇳'},
        'ARS': {'name': 'Peso Argentino', 'symbol': '$', 'flag': '🇦🇷'},
        'MXN': {'name': 'Peso Mexicano', 'symbol': '$', 'flag': '🇲🇽'},
        'CLP': {'name': 'Peso Chileno', 'symbol': '$', 'flag': '🇨🇱'},
        'COP': {'name': 'Peso Colombiano', 'symbol': '$', 'flag': '🇨🇴'},
        'PEN': {'name': 'Sol Peruano', 'symbol': 'S/', 'flag': '🇵🇪'},
        'UYU': {'name': 'Peso Uruguaio', 'symbol': '$', 'flag': '🇺🇾'},
    }
    
    # API endpoints - usando múltiplas fontes para redundância
    API_SOURCES = {
        'exchangerate': {
            'url': 'https://api.exchangerate-api.com/v4/latest/',
            'key_required': False,
            'free_tier': True
        },
        'fixer': {
            'url': 'http://data.fixer.io/api/latest',
            'key_required': True,
            'free_tier': True
        },
        'currencyapi': {
            'url': 'https://api.currencyapi.com/v3/latest',
            'key_required': True,
            'free_tier': True
        }
    }
    
    def __init__(self):
        self.api_key = os.environ.get('CURRENCY_API_KEY')
        self.base_currency = 'USD'  # Moeda base padrão
    
    def get_exchange_rate(self, from_currency: str, to_currency: str, amount: Decimal = Decimal('1')) -> Dict:
        """
        Obtém taxa de câmbio entre duas moedas
        
        Args:
            from_currency: Moeda de origem (ex: 'USD')
            to_currency: Moeda de destino (ex: 'BRL')
            amount: Valor a ser convertido
            
        Returns:
            Dict com informações da conversão
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Verificar se as moedas são suportadas
        if from_currency not in self.SUPPORTED_CURRENCIES or to_currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Moeda não suportada: {from_currency} -> {to_currency}")
        
        # Se for a mesma moeda, retornar 1:1
        if from_currency == to_currency:
            return {
                'from_currency': from_currency,
                'to_currency': to_currency,
                'rate': Decimal('1'),
                'amount': amount,
                'converted_amount': amount,
                'timestamp': datetime.now().isoformat(),
                'source': 'same_currency'
            }
        
        # Verificar cache primeiro
        cache_key = f"{from_currency}_{to_currency}"
        if self._is_cache_valid(cache_key):
            cached_data = self._cache[cache_key]
            converted_amount = amount * cached_data['rate']
            
            return {
                'from_currency': from_currency,
                'to_currency': to_currency,
                'rate': cached_data['rate'],
                'amount': amount,
                'converted_amount': converted_amount,
                'timestamp': cached_data['timestamp'],
                'source': 'cache'
            }
        
        # Buscar cotação em tempo real
        try:
            rate_data = self._fetch_live_rate(from_currency, to_currency)
            converted_amount = amount * rate_data['rate']
            
            # Salvar no cache
            self._cache[cache_key] = {
                'rate': rate_data['rate'],
                'timestamp': datetime.now().isoformat(),
                'cached_at': datetime.now()
            }
            
            return {
                'from_currency': from_currency,
                'to_currency': to_currency,
                'rate': rate_data['rate'],
                'amount': amount,
                'converted_amount': converted_amount,
                'timestamp': rate_data['timestamp'],
                'source': rate_data['source']
            }
            
        except Exception as e:
            # Fallback: usar cotação estimada ou última conhecida
            return self._get_fallback_rate(from_currency, to_currency, amount, str(e))
    
    def _fetch_live_rate(self, from_currency: str, to_currency: str) -> Dict:
        """Busca cotação em tempo real das APIs"""
        
        # Tentar API gratuita primeiro (ExchangeRate-API)
        try:
            url = f"{self.API_SOURCES['exchangerate']['url']}{from_currency}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if to_currency in data.get('rates', {}):
                    return {
                        'rate': Decimal(str(data['rates'][to_currency])),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'exchangerate-api'
                    }
        except Exception as e:
            print(f"Erro na ExchangeRate-API: {e}")
        
        # Se tiver API key, tentar Fixer.io
        if self.api_key:
            try:
                url = f"{self.API_SOURCES['fixer']['url']}?access_key={self.api_key}&base={from_currency}&symbols={to_currency}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and to_currency in data.get('rates', {}):
                        return {
                            'rate': Decimal(str(data['rates'][to_currency])),
                            'timestamp': datetime.now().isoformat(),
                            'source': 'fixer.io'
                        }
            except Exception as e:
                print(f"Erro na Fixer.io: {e}")
        
        # Se nenhuma API funcionou, usar cotações estimadas do Banco Central (para BRL)
        if to_currency == 'BRL' or from_currency == 'BRL':
            return self._get_bcb_rate(from_currency, to_currency)
        
        raise Exception("Não foi possível obter cotação de nenhuma fonte")
    
    def _get_bcb_rate(self, from_currency: str, to_currency: str) -> Dict:
        """Busca cotação do Banco Central do Brasil (apenas para BRL)"""
        try:
            # API do Banco Central do Brasil - gratuita e confiável
            if from_currency == 'BRL':
                # BRL para outra moeda
                currency_map = {'USD': 1, 'EUR': 978, 'GBP': 826, 'JPY': 392}
                if to_currency in currency_map:
                    url = f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='{to_currency}'&@dataCotacao='{datetime.now().strftime('%m-%d-%Y')}'&$top=1&$format=json"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('value'):
                            rate = Decimal('1') / Decimal(str(data['value'][0]['cotacaoVenda']))
                            return {
                                'rate': rate,
                                'timestamp': datetime.now().isoformat(),
                                'source': 'banco-central-brasil'
                            }
            
            elif to_currency == 'BRL':
                # Outra moeda para BRL
                currency_map = {'USD': 1, 'EUR': 978, 'GBP': 826, 'JPY': 392}
                if from_currency in currency_map:
                    url = f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='{from_currency}'&@dataCotacao='{datetime.now().strftime('%m-%d-%Y')}'&$top=1&$format=json"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('value'):
                            rate = Decimal(str(data['value'][0]['cotacaoVenda']))
                            return {
                                'rate': rate,
                                'timestamp': datetime.now().isoformat(),
                                'source': 'banco-central-brasil'
                            }
        
        except Exception as e:
            print(f"Erro na API do Banco Central: {e}")
        
        raise Exception("Não foi possível obter cotação do Banco Central")
    
    def _get_fallback_rate(self, from_currency: str, to_currency: str, amount: Decimal, error: str) -> Dict:
        """Retorna cotação estimada quando APIs falham"""
        
        # Cotações estimadas baseadas em médias históricas (apenas para demonstração)
        fallback_rates = {
            'USD_BRL': Decimal('5.20'),
            'EUR_BRL': Decimal('5.60'),
            'GBP_BRL': Decimal('6.40'),
            'JPY_BRL': Decimal('0.035'),
            'USD_EUR': Decimal('0.85'),
            'EUR_USD': Decimal('1.18'),
            'GBP_USD': Decimal('1.25'),
            'USD_GBP': Decimal('0.80'),
        }
        
        # Tentar encontrar taxa direta
        rate_key = f"{from_currency}_{to_currency}"
        reverse_key = f"{to_currency}_{from_currency}"
        
        if rate_key in fallback_rates:
            rate = fallback_rates[rate_key]
        elif reverse_key in fallback_rates:
            rate = Decimal('1') / fallback_rates[reverse_key]
        else:
            # Taxa padrão conservadora
            rate = Decimal('1.0')
        
        converted_amount = amount * rate
        
        return {
            'from_currency': from_currency,
            'to_currency': to_currency,
            'rate': rate,
            'amount': amount,
            'converted_amount': converted_amount,
            'timestamp': datetime.now().isoformat(),
            'source': 'fallback',
            'warning': f'Cotação estimada - APIs indisponíveis: {error}',
            'is_estimate': True
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica se o cache ainda é válido"""
        if cache_key not in self._cache:
            return False
        
        cached_time = self._cache[cache_key].get('cached_at')
        if not cached_time:
            return False
        
        return datetime.now() - cached_time < self._cache_duration
    
    def get_multiple_rates(self, base_currency: str, target_currencies: List[str]) -> Dict:
        """Obtém múltiplas cotações de uma vez"""
        results = {}
        
        for target in target_currencies:
            try:
                result = self.get_exchange_rate(base_currency, target)
                results[target] = result
            except Exception as e:
                results[target] = {
                    'error': str(e),
                    'from_currency': base_currency,
                    'to_currency': target
                }
        
        return {
            'base_currency': base_currency,
            'rates': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_currency_info(self, currency_code: str) -> Dict:
        """Retorna informações sobre uma moeda"""
        currency_code = currency_code.upper()
        
        if currency_code not in self.SUPPORTED_CURRENCIES:
            return {'error': f'Moeda {currency_code} não suportada'}
        
        return {
            'code': currency_code,
            **self.SUPPORTED_CURRENCIES[currency_code]
        }
    
    def calculate_profit_margin(self, cost_currency: str, cost_amount: Decimal, 
                              sale_currency: str, sale_amount: Decimal) -> Dict:
        """Calcula margem de lucro considerando conversão de moedas"""
        
        # Converter custo para moeda de venda
        cost_conversion = self.get_exchange_rate(cost_currency, sale_currency, cost_amount)
        cost_in_sale_currency = cost_conversion['converted_amount']
        
        # Calcular margem
        profit = sale_amount - cost_in_sale_currency
        margin_percentage = (profit / sale_amount * 100) if sale_amount > 0 else Decimal('0')
        
        return {
            'cost': {
                'amount': cost_amount,
                'currency': cost_currency,
                'converted_amount': cost_in_sale_currency,
                'converted_currency': sale_currency,
                'exchange_rate': cost_conversion['rate']
            },
            'sale': {
                'amount': sale_amount,
                'currency': sale_currency
            },
            'profit': {
                'amount': profit,
                'currency': sale_currency,
                'margin_percentage': margin_percentage
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_historical_trend(self, from_currency: str, to_currency: str, days: int = 30) -> Dict:
        """Simula tendência histórica (implementação básica)"""
        # Em uma implementação real, isso buscaria dados históricos de APIs
        current_rate = self.get_exchange_rate(from_currency, to_currency)
        
        # Simular variações para demonstração
        import random
        trend_data = []
        base_rate = float(current_rate['rate'])
        
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i)
            # Variação simulada de ±2%
            variation = random.uniform(-0.02, 0.02)
            simulated_rate = base_rate * (1 + variation)
            
            trend_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'rate': round(simulated_rate, 6)
            })
        
        return {
            'from_currency': from_currency,
            'to_currency': to_currency,
            'period_days': days,
            'current_rate': float(current_rate['rate']),
            'trend_data': trend_data,
            'note': 'Dados simulados para demonstração'
        }


# Instância global do serviço
currency_service = CurrencyService()


def convert_currency(from_currency: str, to_currency: str, amount: float) -> Dict:
    """Função helper para conversão simples"""
    return currency_service.get_exchange_rate(from_currency, to_currency, Decimal(str(amount)))


def get_supported_currencies() -> Dict:
    """Retorna lista de moedas suportadas"""
    return currency_service.SUPPORTED_CURRENCIES