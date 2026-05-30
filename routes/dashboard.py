from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func, desc, and_, case
from datetime import datetime, timedelta, date
import calendar

from app import db
from models import Invoice, InvoiceStatus, InvoiceType, Product, Payment, PaymentStatus, InvoiceItem

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # Data atual para cálculos
    now = datetime.now()
    today = date.today()
    current_month_start = date(today.year, today.month, 1)
    current_month_end = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
    
    # =====================
    # MÉTRICAS FINANCEIRAS
    # =====================
    
    # Total de vendas (notas de saída aprovadas e emitidas)
    total_sales = Invoice.query.with_entities(
        func.sum(Invoice.total_value)
    ).filter(
        Invoice.type == InvoiceType.OUTBOUND,
        Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.APPROVED])
    ).scalar() or 0
    
    # Total de compras (notas de entrada aprovadas e emitidas)
    total_purchases = Invoice.query.with_entities(
        func.sum(Invoice.total_value)
    ).filter(
        Invoice.type == InvoiceType.INBOUND,
        Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.APPROVED])
    ).scalar() or 0
    
    # Receitas do mês atual
    current_month_revenue = Invoice.query.with_entities(
        func.sum(Invoice.total_value)
    ).filter(
        Invoice.type == InvoiceType.OUTBOUND,
        Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.APPROVED]),
        Invoice.issue_date.between(current_month_start, current_month_end)
    ).scalar() or 0
    
    # Despesas do mês atual
    current_month_expenses = Invoice.query.with_entities(
        func.sum(Invoice.total_value)
    ).filter(
        Invoice.type == InvoiceType.INBOUND,
        Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.APPROVED]),
        Invoice.issue_date.between(current_month_start, current_month_end)
    ).scalar() or 0
    
    # Lucro do mês atual
    current_month_profit = current_month_revenue - current_month_expenses
    
    # =====================
    # INDICADORES DE NOTAS
    # =====================
    
    # Total de notas por status
    invoice_by_status = dict(
        Invoice.query.with_entities(
            Invoice.status, func.count(Invoice.id)
        ).group_by(Invoice.status).all()
    )
    
    # Contagem de notas por tipo
    invoice_by_type = dict(
        Invoice.query.with_entities(
            Invoice.type, func.count(Invoice.id)
        ).group_by(Invoice.type).all()
    )
    
    # Notas fiscais recentes
    recent_invoices = Invoice.query.order_by(
        desc(Invoice.created_at)
    ).limit(5).all()
    
    # =====================
    # PAGAMENTOS
    # =====================
    
    # Pagamentos pendentes
    pending_payments = Payment.query.filter_by(
        status=PaymentStatus.PENDING
    ).order_by(Payment.due_date).limit(5).all()
    
    # Total de pagamentos pendentes
    total_pending_payments = Payment.query.with_entities(
        func.sum(Payment.amount)
    ).filter_by(
        status=PaymentStatus.PENDING
    ).scalar() or 0
    
    # Pagamentos vencidos
    overdue_payments = Payment.query.with_entities(
        func.sum(Payment.amount)
    ).filter(
        Payment.status == PaymentStatus.PENDING,
        Payment.due_date < today
    ).scalar() or 0
    
    # Pagamentos a vencer em 7 dias
    upcoming_payments = Payment.query.with_entities(
        func.sum(Payment.amount)
    ).filter(
        Payment.status == PaymentStatus.PENDING,
        Payment.due_date.between(today, today + timedelta(days=7))
    ).scalar() or 0
    
    # =====================
    # ESTOQUE
    # =====================
    
    # Produtos com estoque baixo
    low_stock_products = []
    products = Product.query.all()
    for product in products:
        current_stock = product.current_stock()
        if current_stock is not None and current_stock <= product.min_stock:
            low_stock_products.append({
                'id': product.id,
                'sku': product.sku,
                'name': product.name,
                'current_stock': current_stock,
                'min_stock': product.min_stock
            })
            if len(low_stock_products) >= 5:
                break
    
    # =====================
    # GRÁFICOS
    # =====================
    
    # Faturamento mensal (últimos 6 meses)
    six_months_ago = datetime.now() - timedelta(days=180)
    
    # Obter faturas nos últimos 6 meses
    recent_invoices = Invoice.query.filter(
        Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.APPROVED]),
        Invoice.issue_date >= six_months_ago
    ).all()
    
    # Vamos processar os dados manualmente para obter receitas e despesas por mês
    monthly_data = {}
    
    for invoice in recent_invoices:
        month_key = f"{invoice.issue_date.year}-{invoice.issue_date.month:02d}"
        
        if month_key not in monthly_data:
            monthly_data[month_key] = {'income': 0, 'expense': 0}
        
        if invoice.type == InvoiceType.OUTBOUND:
            monthly_data[month_key]['income'] += invoice.total_value
        elif invoice.type == InvoiceType.INBOUND:
            monthly_data[month_key]['expense'] += invoice.total_value
    
    # Ordenar os dados por mês
    sorted_months = sorted(monthly_data.keys())
    sales_by_month = [(month, monthly_data[month]['income'], monthly_data[month]['expense']) 
                      for month in sorted_months]
    
    # Formatar para gráfico
    months_labels = []
    income_values = []
    expense_values = []
    sales_values = []  # Mantido para compatibilidade
    
    for month_date, income, expense in sales_by_month:
        # Converter para objeto datetime se não for
        if isinstance(month_date, str):
            month_date = datetime.strptime(month_date, '%Y-%m-%d')
        
        month_name = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                     'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'][month_date.month-1]
        month_label = f"{month_name}/{month_date.year}"
        
        months_labels.append(month_label)
        income_values.append(float(income) if income else 0)
        expense_values.append(float(expense) if expense else 0)
        sales_values.append(float(income) if income else 0)  # Mantido para compatibilidade
    
    # Obtém todos os itens de nota para calcular os produtos mais vendidos
    all_items = db.session.query(
        InvoiceItem, Product, Invoice
    ).join(
        Product, InvoiceItem.product_id == Product.id
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        Invoice.type == InvoiceType.OUTBOUND,
        Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.APPROVED])
    ).all()
    
    # Processar dados manualmente para obter produtos mais vendidos
    product_sales = {}
    for item, product, invoice in all_items:
        if product.id not in product_sales:
            product_sales[product.id] = {
                'name': product.name,
                'quantity': 0,
                'value': 0
            }
        
        product_sales[product.id]['quantity'] += item.quantity
        product_sales[product.id]['value'] += item.quantity * item.unit_price
    
    # Ordenar por quantidade vendida
    sorted_products = sorted(
        product_sales.values(), 
        key=lambda x: x['quantity'], 
        reverse=True
    )[:5]
    
    # Formatar para gráfico
    top_products = [(p['name'], p['quantity'], p['value']) for p in sorted_products]
    
    # Formatar para gráfico
    top_product_names = []
    top_product_quantities = []
    top_product_values = []
    
    for name, quantity, value in top_products:
        top_product_names.append(name)
        top_product_quantities.append(float(quantity) if quantity else 0)
        top_product_values.append(float(value) if value else 0)
    
    # Indicadores de desempenho
    kpi_data = {
        'total_sales': total_sales,
        'total_purchases': total_purchases,
        'profit_margin': ((total_sales - total_purchases) / total_sales * 100) if total_sales > 0 else 0,
        'current_month_revenue': current_month_revenue,
        'current_month_expenses': current_month_expenses,
        'current_month_profit': current_month_profit,
        'overdue_payments': overdue_payments,
        'upcoming_payments': upcoming_payments,
        'total_pending_payments': total_pending_payments
    }
    
    return render_template(
        'dashboard.html',
        invoice_by_status=invoice_by_status,
        invoice_by_type=invoice_by_type,
        recent_invoices=recent_invoices,
        pending_payments=pending_payments,
        low_stock_products=low_stock_products,
        months_labels=months_labels,
        sales_values=sales_values,
        income_values=income_values,
        expense_values=expense_values,
        top_product_names=top_product_names,
        top_product_quantities=top_product_quantities,
        top_product_values=top_product_values,
        kpi_data=kpi_data,
        now=now
    )
