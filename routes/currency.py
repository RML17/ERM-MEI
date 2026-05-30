from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.currency_service import currency_service, convert_currency, get_supported_currencies
from decimal import Decimal
import json

currency_bp = Blueprint('currency', __name__, url_prefix='/currency')


@currency_bp.route('/')
@login_required
def dashboard():
    """Dashboard de conversão de moedas"""
    
    # Moedas principais para exibição rápida
    main_currencies = ['USD', 'EUR', 'BRL', 'GBP', 'JPY']
    
    # Obter cotações principais em relação ao USD
    quick_rates = {}
    try:
        rates_data = currency_service.get_multiple_rates('USD', ['BRL', 'EUR', 'GBP', 'JPY'])
        quick_rates = rates_data.get('rates', {})
    except Exception as e:
        flash(f'Erro ao carregar cotações: {str(e)}', 'warning')
    
    return render_template('currency/dashboard.html', 
                         supported_currencies=get_supported_currencies(),
                         main_currencies=main_currencies,
                         quick_rates=quick_rates)


@currency_bp.route('/converter')
@login_required
def converter():
    """Página do conversor de moedas"""
    return render_template('currency/converter.html', 
                         supported_currencies=get_supported_currencies())


@currency_bp.route('/api/convert', methods=['POST'])
@login_required
def api_convert():
    """API para conversão de moedas"""
    try:
        data = request.get_json()
        
        from_currency = data.get('from_currency', '').upper()
        to_currency = data.get('to_currency', '').upper()
        amount = float(data.get('amount', 0))
        
        if not from_currency or not to_currency or amount <= 0:
            return jsonify({'error': 'Dados inválidos'}), 400
        
        result = convert_currency(from_currency, to_currency, amount)
        
        # Converter Decimal para float para JSON
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [decimal_to_float(item) for item in obj]
            return obj
        
        return jsonify(decimal_to_float(result))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@currency_bp.route('/api/rates/<base_currency>')
@login_required
def api_rates(base_currency):
    """API para obter múltiplas cotações"""
    try:
        base_currency = base_currency.upper()
        target_currencies = request.args.getlist('targets')
        
        if not target_currencies:
            # Se não especificado, usar moedas principais
            target_currencies = ['USD', 'EUR', 'BRL', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF']
        
        # Remover moeda base da lista
        target_currencies = [c.upper() for c in target_currencies if c.upper() != base_currency]
        
        result = currency_service.get_multiple_rates(base_currency, target_currencies)
        
        # Converter Decimal para float
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [decimal_to_float(item) for item in obj]
            return obj
        
        return jsonify(decimal_to_float(result))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@currency_bp.route('/api/currency-info/<currency_code>')
@login_required
def api_currency_info(currency_code):
    """API para informações de uma moeda"""
    try:
        info = currency_service.get_currency_info(currency_code)
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@currency_bp.route('/profit-calculator')
@login_required
def profit_calculator():
    """Calculadora de margem de lucro internacional"""
    return render_template('currency/profit_calculator.html', 
                         supported_currencies=get_supported_currencies())


@currency_bp.route('/api/calculate-profit', methods=['POST'])
@login_required
def api_calculate_profit():
    """API para calcular margem de lucro com conversão"""
    try:
        data = request.get_json()
        
        cost_currency = data.get('cost_currency', '').upper()
        cost_amount = Decimal(str(data.get('cost_amount', 0)))
        sale_currency = data.get('sale_currency', '').upper()
        sale_amount = Decimal(str(data.get('sale_amount', 0)))
        
        if not all([cost_currency, cost_amount, sale_currency, sale_amount]):
            return jsonify({'error': 'Dados incompletos'}), 400
        
        result = currency_service.calculate_profit_margin(
            cost_currency, cost_amount, sale_currency, sale_amount
        )
        
        # Converter Decimal para float
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [decimal_to_float(item) for item in obj]
            return obj
        
        return jsonify(decimal_to_float(result))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@currency_bp.route('/trends')
@login_required
def trends():
    """Página de tendências de câmbio"""
    return render_template('currency/trends.html', 
                         supported_currencies=get_supported_currencies())


@currency_bp.route('/api/trends/<from_currency>/<to_currency>')
@login_required
def api_trends(from_currency, to_currency):
    """API para tendências históricas"""
    try:
        days = int(request.args.get('days', 30))
        
        result = currency_service.get_historical_trend(
            from_currency.upper(), to_currency.upper(), days
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@currency_bp.route('/monitor')
@login_required
def monitor():
    """Monitor de taxas de câmbio em tempo real"""
    # Pares de moedas mais importantes para o usuário
    important_pairs = [
        ('USD', 'BRL'),
        ('EUR', 'BRL'),
        ('USD', 'EUR'),
        ('GBP', 'USD'),
        ('JPY', 'USD'),
        ('CAD', 'USD'),
        ('AUD', 'USD'),
        ('CHF', 'USD')
    ]
    
    return render_template('currency/monitor.html', 
                         important_pairs=important_pairs,
                         supported_currencies=get_supported_currencies())


@currency_bp.route('/api/monitor-rates')
@login_required
def api_monitor_rates():
    """API para monitor em tempo real"""
    try:
        pairs = request.args.getlist('pairs')
        if not pairs:
            # Pares padrão
            pairs = ['USD_BRL', 'EUR_BRL', 'USD_EUR', 'GBP_USD']
        
        results = {}
        
        for pair in pairs:
            if '_' in pair:
                from_curr, to_curr = pair.split('_', 1)
                try:
                    rate_data = currency_service.get_exchange_rate(from_curr, to_curr)
                    results[pair] = {
                        'rate': float(rate_data['rate']),
                        'timestamp': rate_data['timestamp'],
                        'source': rate_data['source'],
                        'from_currency': from_curr,
                        'to_currency': to_curr,
                        'is_estimate': rate_data.get('is_estimate', False)
                    }
                except Exception as e:
                    results[pair] = {'error': str(e)}
        
        return jsonify({
            'rates': results,
            'timestamp': currency_service.get_exchange_rate('USD', 'USD')['timestamp']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@currency_bp.route('/alerts')
@login_required
def alerts():
    """Sistema de alertas de câmbio"""
    return render_template('currency/alerts.html', 
                         supported_currencies=get_supported_currencies())


@currency_bp.route('/integration')
@login_required
def integration():
    """Guia de integração com outros módulos"""
    return render_template('currency/integration.html')


@currency_bp.route('/api/invoice-conversion', methods=['POST'])
@login_required
def api_invoice_conversion():
    """API para conversão de valores de nota fiscal"""
    try:
        data = request.get_json()
        
        invoice_currency = data.get('invoice_currency', 'BRL').upper()
        target_currency = data.get('target_currency', 'USD').upper()
        items = data.get('items', [])
        
        if not items:
            return jsonify({'error': 'Nenhum item fornecido'}), 400
        
        converted_items = []
        total_original = Decimal('0')
        total_converted = Decimal('0')
        
        for item in items:
            original_value = Decimal(str(item.get('value', 0)))
            conversion = currency_service.get_exchange_rate(
                invoice_currency, target_currency, original_value
            )
            
            converted_items.append({
                'description': item.get('description', ''),
                'original_value': float(original_value),
                'converted_value': float(conversion['converted_amount']),
                'exchange_rate': float(conversion['rate'])
            })
            
            total_original += original_value
            total_converted += conversion['converted_amount']
        
        # Obter informações das moedas
        invoice_curr_info = currency_service.get_currency_info(invoice_currency)
        target_curr_info = currency_service.get_currency_info(target_currency)
        
        return jsonify({
            'invoice_currency': invoice_currency,
            'target_currency': target_currency,
            'invoice_currency_info': invoice_curr_info,
            'target_currency_info': target_curr_info,
            'items': converted_items,
            'totals': {
                'original': float(total_original),
                'converted': float(total_converted)
            },
            'conversion_rate': float(total_converted / total_original) if total_original > 0 else 0,
            'timestamp': currency_service.get_exchange_rate('USD', 'USD')['timestamp']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500