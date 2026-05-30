from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from services.tax_service import tax_calculator, calculate_invoice_taxes, get_tax_simulation
from decimal import Decimal
import json

taxes_bp = Blueprint('taxes', __name__, url_prefix='/taxes')


@taxes_bp.route('/')
@login_required
def index():
    """Dashboard de impostos com simulações e informações"""
    
    # Estados do Brasil para simulação
    brazilian_states = list(tax_calculator.ICMS_RATES.keys())
    
    # Informações resumidas por região
    state_breakdown = tax_calculator.get_tax_breakdown_by_state(brazilian_states)
    
    return render_template('taxes/dashboard.html', 
                         state_breakdown=state_breakdown,
                         brazilian_states=brazilian_states)


@taxes_bp.route('/calculate', methods=['POST'])
@login_required
def calculate_taxes():
    """API para calcular impostos de uma nota fiscal"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Calcular impostos
        tax_result = calculate_invoice_taxes(data)
        
        # Converter Decimal para float para JSON
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [decimal_to_float(item) for item in obj]
            return obj
        
        result = decimal_to_float(tax_result)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@taxes_bp.route('/simulate', methods=['GET', 'POST'])
@login_required
def simulate():
    """Simulador de impostos por região"""
    
    if request.method == 'POST':
        try:
            base_value = float(request.form.get('base_value', 0))
            origin_state = request.form.get('origin_state', 'SP')
            
            # Simular cenários
            scenarios = get_tax_simulation(base_value, origin_state)
            
            # Converter Decimal para float
            for state, data in scenarios.items():
                for key, value in data.items():
                    if isinstance(value, Decimal):
                        scenarios[state][key] = float(value)
                    elif isinstance(value, dict):
                        for k, v in value.items():
                            if isinstance(v, Decimal):
                                data[key][k] = float(v)
            
            return render_template('taxes/simulate.html', 
                                 scenarios=scenarios,
                                 base_value=base_value,
                                 origin_state=origin_state,
                                 brazilian_states=list(tax_calculator.ICMS_RATES.keys()))
            
        except Exception as e:
            flash(f'Erro na simulação: {str(e)}', 'error')
    
    return render_template('taxes/simulate.html', 
                         brazilian_states=list(tax_calculator.ICMS_RATES.keys()))


@taxes_bp.route('/api/state-info/<state>')
@login_required
def api_state_info(state):
    """API para informações fiscais de um estado"""
    try:
        state = state.upper()
        
        if state not in tax_calculator.ICMS_RATES:
            return jsonify({'error': 'Estado não encontrado'}), 404
        
        info = {
            'state': state,
            'state_name': tax_calculator._get_state_name(state),
            'region': tax_calculator._get_state_region(state),
            'icms_rate': tax_calculator.ICMS_RATES[state],
            'ipi_rates': tax_calculator.IPI_RATES,
            'pis_cofins': tax_calculator.PIS_COFINS,
            'iss_rates': tax_calculator.ISS_RATES
        }
        
        return jsonify(info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@taxes_bp.route('/api/calculate-item', methods=['POST'])
@login_required
def api_calculate_item():
    """API para calcular impostos de um item específico"""
    try:
        data = request.get_json()
        
        value = Decimal(str(data.get('value', 0)))
        origin_state = data.get('origin_state', 'SP')
        destination_state = data.get('destination_state', 'SP')
        product_category = data.get('category', 'default')
        invoice_type = data.get('type', 'product')
        
        result = {}
        
        # Calcular ICMS
        if invoice_type == 'product':
            icms = tax_calculator.calculate_icms(value, origin_state, destination_state, product_category)
            result['icms'] = {
                'rate': icms['rate'],
                'value': float(icms['value']),
                'description': icms['description']
            }
            
            # Calcular IPI
            ipi = tax_calculator.calculate_ipi(value, product_category)
            result['ipi'] = {
                'rate': ipi['rate'],
                'value': float(ipi['value']),
                'description': ipi['description']
            }
        
        # Calcular PIS/COFINS
        pis_cofins = tax_calculator.calculate_pis_cofins(value)
        result['pis'] = {
            'rate': pis_cofins['pis']['rate'],
            'value': float(pis_cofins['pis']['value']),
            'description': pis_cofins['pis']['description']
        }
        result['cofins'] = {
            'rate': pis_cofins['cofins']['rate'],
            'value': float(pis_cofins['cofins']['value']),
            'description': pis_cofins['cofins']['description']
        }
        
        # Calcular ISS (para serviços)
        if invoice_type == 'service':
            iss = tax_calculator.calculate_iss(value, product_category)
            result['iss'] = {
                'rate': iss['rate'],
                'value': float(iss['value']),
                'description': iss['description']
            }
        
        # Total de impostos
        total_taxes = sum([
            result.get('icms', {}).get('value', 0),
            result.get('ipi', {}).get('value', 0),
            result.get('pis', {}).get('value', 0),
            result.get('cofins', {}).get('value', 0),
            result.get('iss', {}).get('value', 0)
        ])
        
        result['summary'] = {
            'base_value': float(value),
            'total_taxes': total_taxes,
            'final_value': float(value) + total_taxes,
            'tax_percentage': (total_taxes / float(value)) * 100 if value > 0 else 0
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@taxes_bp.route('/regulations')
@login_required
def regulations():
    """Página com informações sobre regulamentações fiscais"""
    
    # Informações sobre as regulamentações
    tax_info = {
        'icms': {
            'name': 'ICMS - Imposto sobre Circulação de Mercadorias e Serviços',
            'description': 'Imposto estadual incidente sobre a circulação de mercadorias e alguns serviços.',
            'rates': tax_calculator.ICMS_RATES,
            'interstate_rules': 'Alíquotas interestaduais variam de 7% a 12% conforme origem e destino.'
        },
        'ipi': {
            'name': 'IPI - Imposto sobre Produtos Industrializados',
            'description': 'Imposto federal sobre produtos industrializados.',
            'rates': tax_calculator.IPI_RATES,
            'rules': 'Varia conforme a classificação fiscal do produto (NCM).'
        },
        'pis_cofins': {
            'name': 'PIS/COFINS - Contribuições Sociais',
            'description': 'Contribuições federais sobre o faturamento das empresas.',
            'rates': tax_calculator.PIS_COFINS,
            'rules': 'Alíquotas diferentes para regime cumulativo e não-cumulativo.'
        },
        'iss': {
            'name': 'ISS - Imposto sobre Serviços',
            'description': 'Imposto municipal incidente sobre serviços.',
            'rates': tax_calculator.ISS_RATES,
            'rules': 'Varia por município, entre 2% e 5%.'
        }
    }
    
    return render_template('taxes/regulations.html', tax_info=tax_info)