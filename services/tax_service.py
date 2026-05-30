"""
Serviço de Cálculo de Impostos
Sistema completo para cálculo automático de impostos por região
"""

from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json


class TaxCalculatorService:
    """Serviço principal para cálculo de impostos"""
    
    # Tabelas de impostos por região (dados reais do Brasil)
    ICMS_RATES = {
        # Estados e suas alíquotas internas
        'AC': 0.17,  # Acre
        'AL': 0.18,  # Alagoas
        'AP': 0.18,  # Amapá
        'AM': 0.18,  # Amazonas
        'BA': 0.18,  # Bahia
        'CE': 0.18,  # Ceará
        'DF': 0.18,  # Distrito Federal
        'ES': 0.17,  # Espírito Santo
        'GO': 0.17,  # Goiás
        'MA': 0.18,  # Maranhão
        'MT': 0.17,  # Mato Grosso
        'MS': 0.17,  # Mato Grosso do Sul
        'MG': 0.18,  # Minas Gerais
        'PA': 0.17,  # Pará
        'PB': 0.18,  # Paraíba
        'PR': 0.18,  # Paraná
        'PE': 0.18,  # Pernambuco
        'PI': 0.18,  # Piauí
        'RJ': 0.18,  # Rio de Janeiro
        'RN': 0.18,  # Rio Grande do Norte
        'RS': 0.18,  # Rio Grande do Sul
        'RO': 0.175, # Rondônia
        'RR': 0.17,  # Roraima
        'SC': 0.17,  # Santa Catarina
        'SP': 0.18,  # São Paulo
        'SE': 0.18,  # Sergipe
        'TO': 0.18,  # Tocantins
    }
    
    # ICMS Interestadual - Origem/Destino
    ICMS_INTERSTATE = {
        'north_northeast_to_south_southeast': 0.07,  # Norte/Nordeste para Sul/Sudeste
        'south_southeast_to_north_northeast': 0.12,  # Sul/Sudeste para Norte/Nordeste
        'same_region': 0.12,  # Mesma região
    }
    
    # Regiões para ICMS interestadual
    REGIONS = {
        'north': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
        'northeast': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
        'center_west': ['DF', 'GO', 'MT', 'MS'],
        'southeast': ['ES', 'MG', 'RJ', 'SP'],
        'south': ['PR', 'RS', 'SC']
    }
    
    # Outras alíquotas
    IPI_RATES = {
        'default': 0.10,
        'electronics': 0.15,
        'vehicles': 0.25,
        'food': 0.05,
        'medicine': 0.00,
        'books': 0.00,
    }
    
    PIS_COFINS = {
        'pis': 0.0165,
        'cofins': 0.076,
    }
    
    ISS_RATES = {
        'default': 0.05,
        'minimum': 0.02,
        'maximum': 0.05,
    }
    
    def __init__(self):
        self.calculation_history = []
    
    def calculate_icms(self, value: Decimal, origin_state: str, destination_state: str, 
                      product_type: str = 'default') -> Dict:
        """
        Calcula ICMS baseado na origem e destino
        
        Args:
            value: Valor da mercadoria
            origin_state: Estado de origem (sigla)
            destination_state: Estado de destino (sigla)
            product_type: Tipo do produto para alíquotas especiais
            
        Returns:
            Dict com detalhes do cálculo ICMS
        """
        origin_state = origin_state.upper()
        destination_state = destination_state.upper()
        
        if origin_state == destination_state:
            # Operação dentro do mesmo estado
            rate = self.ICMS_RATES.get(origin_state, 0.18)
            icms_value = value * Decimal(str(rate))
            
            return {
                'type': 'internal',
                'rate': rate,
                'value': icms_value,
                'base_calculation': value,
                'origin_state': origin_state,
                'destination_state': destination_state,
                'description': f'ICMS interno - {origin_state}'
            }
        else:
            # Operação interestadual
            origin_region = self._get_state_region(origin_state)
            destination_region = self._get_state_region(destination_state)
            
            # Determinar alíquota interestadual
            if ((origin_region in ['north', 'northeast'] and destination_region in ['south', 'southeast']) or
                (origin_region in ['south', 'southeast'] and destination_region in ['north', 'northeast'])):
                if origin_region in ['north', 'northeast']:
                    rate = self.ICMS_INTERSTATE['north_northeast_to_south_southeast']
                else:
                    rate = self.ICMS_INTERSTATE['south_southeast_to_north_northeast']
            else:
                rate = self.ICMS_INTERSTATE['same_region']
            
            icms_value = value * Decimal(str(rate))
            
            return {
                'type': 'interstate',
                'rate': rate,
                'value': icms_value,
                'base_calculation': value,
                'origin_state': origin_state,
                'destination_state': destination_state,
                'description': f'ICMS interestadual - {origin_state} para {destination_state}'
            }
    
    def calculate_ipi(self, value: Decimal, product_category: str = 'default') -> Dict:
        """Calcula IPI baseado na categoria do produto"""
        rate = self.IPI_RATES.get(product_category, self.IPI_RATES['default'])
        ipi_value = value * Decimal(str(rate))
        
        return {
            'rate': rate,
            'value': ipi_value,
            'base_calculation': value,
            'category': product_category,
            'description': f'IPI - {product_category}'
        }
    
    def calculate_pis_cofins(self, value: Decimal, regime: str = 'cumulative') -> Dict:
        """Calcula PIS e COFINS"""
        if regime == 'cumulative':
            pis_rate = 0.0065
            cofins_rate = 0.03
        else:  # non-cumulative
            pis_rate = self.PIS_COFINS['pis']
            cofins_rate = self.PIS_COFINS['cofins']
        
        pis_value = value * Decimal(str(pis_rate))
        cofins_value = value * Decimal(str(cofins_rate))
        
        return {
            'pis': {
                'rate': pis_rate,
                'value': pis_value,
                'description': f'PIS - {regime}'
            },
            'cofins': {
                'rate': cofins_rate,
                'value': cofins_value,
                'description': f'COFINS - {regime}'
            },
            'total': pis_value + cofins_value,
            'regime': regime
        }
    
    def calculate_iss(self, value: Decimal, service_type: str = 'default', 
                     city_code: str = None) -> Dict:
        """Calcula ISS para serviços"""
        # ISS varia por município, aqui usamos uma base geral
        rate = self.ISS_RATES['default']
        
        # Ajustar por tipo de serviço
        if service_type == 'consulting':
            rate = 0.05
        elif service_type == 'construction':
            rate = 0.04
        elif service_type == 'transport':
            rate = 0.02
        
        iss_value = value * Decimal(str(rate))
        
        return {
            'rate': rate,
            'value': iss_value,
            'base_calculation': value,
            'service_type': service_type,
            'description': f'ISS - {service_type}'
        }
    
    def calculate_total_taxes(self, invoice_data: Dict) -> Dict:
        """
        Calcula todos os impostos para uma nota fiscal
        
        Args:
            invoice_data: Dados da nota fiscal
            
        Returns:
            Dict com todos os impostos calculados
        """
        result = {
            'items': [],
            'totals': {
                'icms': Decimal('0'),
                'ipi': Decimal('0'),
                'pis': Decimal('0'),
                'cofins': Decimal('0'),
                'iss': Decimal('0'),
                'total_taxes': Decimal('0'),
                'subtotal': Decimal('0'),
                'grand_total': Decimal('0')
            },
            'details': {},
            'calculation_date': datetime.now().isoformat()
        }
        
        origin_state = invoice_data.get('origin_state', 'SP')
        destination_state = invoice_data.get('destination_state', 'SP')
        invoice_type = invoice_data.get('type', 'product')  # product or service
        
        for item in invoice_data.get('items', []):
            item_value = Decimal(str(item.get('total_value', 0)))
            product_category = item.get('category', 'default')
            
            item_taxes = {
                'item_id': item.get('id'),
                'description': item.get('description', ''),
                'value': item_value,
                'taxes': {}
            }
            
            # Calcular ICMS (apenas para produtos)
            if invoice_type == 'product':
                icms = self.calculate_icms(item_value, origin_state, destination_state, product_category)
                item_taxes['taxes']['icms'] = icms
                result['totals']['icms'] += icms['value']
                
                # Calcular IPI
                ipi = self.calculate_ipi(item_value, product_category)
                item_taxes['taxes']['ipi'] = ipi
                result['totals']['ipi'] += ipi['value']
            
            # Calcular PIS/COFINS
            pis_cofins = self.calculate_pis_cofins(item_value)
            item_taxes['taxes']['pis_cofins'] = pis_cofins
            result['totals']['pis'] += pis_cofins['pis']['value']
            result['totals']['cofins'] += pis_cofins['cofins']['value']
            
            # Calcular ISS (apenas para serviços)
            if invoice_type == 'service':
                iss = self.calculate_iss(item_value, product_category)
                item_taxes['taxes']['iss'] = iss
                result['totals']['iss'] += iss['value']
            
            result['totals']['subtotal'] += item_value
            result['items'].append(item_taxes)
        
        # Calcular total de impostos
        result['totals']['total_taxes'] = (
            result['totals']['icms'] + 
            result['totals']['ipi'] + 
            result['totals']['pis'] + 
            result['totals']['cofins'] + 
            result['totals']['iss']
        )
        
        result['totals']['grand_total'] = (
            result['totals']['subtotal'] + 
            result['totals']['total_taxes']
        )
        
        # Adicionar detalhes regionais
        result['details'] = {
            'origin_state': origin_state,
            'destination_state': destination_state,
            'operation_type': 'interstate' if origin_state != destination_state else 'internal',
            'invoice_type': invoice_type,
            'applicable_taxes': self._get_applicable_taxes(invoice_type)
        }
        
        # Salvar no histórico
        self.calculation_history.append({
            'timestamp': datetime.now(),
            'calculation': result
        })
        
        return result
    
    def get_tax_breakdown_by_state(self, states: List[str]) -> Dict:
        """Retorna um resumo das alíquotas por estado"""
        breakdown = {}
        
        for state in states:
            state = state.upper()
            if state in self.ICMS_RATES:
                breakdown[state] = {
                    'icms_internal': self.ICMS_RATES[state],
                    'region': self._get_state_region(state),
                    'state_name': self._get_state_name(state)
                }
        
        return breakdown
    
    def simulate_tax_scenarios(self, base_value: Decimal, origin_state: str) -> Dict:
        """Simula cenários de impostos para diferentes estados de destino"""
        scenarios = {}
        
        for dest_state in self.ICMS_RATES.keys():
            icms = self.calculate_icms(base_value, origin_state, dest_state)
            ipi = self.calculate_ipi(base_value)
            pis_cofins = self.calculate_pis_cofins(base_value)
            
            total_taxes = icms['value'] + ipi['value'] + pis_cofins['total']
            
            scenarios[dest_state] = {
                'destination': dest_state,
                'icms': icms,
                'ipi': ipi,
                'pis_cofins': pis_cofins,
                'total_taxes': total_taxes,
                'final_price': base_value + total_taxes,
                'tax_percentage': float((total_taxes / base_value) * 100)
            }
        
        return scenarios
    
    def _get_state_region(self, state: str) -> str:
        """Identifica a região do estado"""
        for region, states in self.REGIONS.items():
            if state in states:
                return region
        return 'center_west'  # default
    
    def _get_state_name(self, state: str) -> str:
        """Retorna o nome completo do estado"""
        state_names = {
            'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
            'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
            'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
            'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
            'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
            'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
            'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
        }
        return state_names.get(state, state)
    
    def _get_applicable_taxes(self, invoice_type: str) -> List[str]:
        """Retorna lista de impostos aplicáveis por tipo de operação"""
        if invoice_type == 'product':
            return ['ICMS', 'IPI', 'PIS', 'COFINS']
        elif invoice_type == 'service':
            return ['ISS', 'PIS', 'COFINS']
        else:
            return ['PIS', 'COFINS']


# Instância global do serviço
tax_calculator = TaxCalculatorService()


def calculate_invoice_taxes(invoice_data: Dict) -> Dict:
    """Função principal para calcular impostos de uma nota fiscal"""
    return tax_calculator.calculate_total_taxes(invoice_data)


def get_tax_simulation(base_value: float, origin_state: str) -> Dict:
    """Simula impostos para diferentes cenários"""
    return tax_calculator.simulate_tax_scenarios(Decimal(str(base_value)), origin_state)


def get_state_tax_info(state: str) -> Dict:
    """Retorna informações fiscais de um estado"""
    return tax_calculator.get_tax_breakdown_by_state([state]).get(state.upper(), {})