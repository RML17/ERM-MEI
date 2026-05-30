from flask import Blueprint, render_template, request, send_file, flash, current_app, redirect, url_for
from flask_login import login_required, current_user
import os
import tempfile
from datetime import datetime, timedelta, date
from sqlalchemy import func, desc, case, literal_column

from app import db
from models import (
    Invoice, InvoiceStatus, InvoiceType, User, Customer, 
    Supplier, Product, AuditLog, Payment, PaymentStatus
)
from services.report_service import (
    generate_invoice_report, generate_user_report, 
    generate_inventory_report, generate_financial_report
)
from forms import ReportForm

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def index():
    return redirect(url_for('reports.summary'))

@reports_bp.route('/generate')
@login_required
def report_generator():
    form = ReportForm()
    return render_template('reports/generate.html', form=form)

@reports_bp.route('/summary')
@login_required
def summary():
    # Determinar o período de análise
    period = request.args.get('period', 'month')
    today = date.today()
    
    if period == 'month':
        # Mês atual
        start_date = date(today.year, today.month, 1)
        end_date = today
    elif period == 'quarter':
        # Trimestre atual
        quarter = (today.month - 1) // 3 + 1
        start_date = date(today.year, (quarter - 1) * 3 + 1, 1)
        if quarter < 4:
            end_date = date(today.year, quarter * 3 + 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, 12, 31)
    elif period == 'year':
        # Ano atual
        start_date = date(today.year, 1, 1)
        end_date = date(today.year, 12, 31)
    else:
        # Período personalizado
        try:
            start_date = datetime.strptime(request.args.get('start_date', today.strftime('%Y-%m-01')), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.args.get('end_date', today.strftime('%Y-%m-%d')), '%Y-%m-%d').date()
        except ValueError:
            start_date = date(today.year, today.month, 1)
            end_date = today
            flash('Formato de data inválido. Usando o mês atual como padrão.', 'warning')
    
    # Resumo financeiro
    summary = get_financial_summary(start_date, end_date)
    
    # Resumo de pagamentos
    payment_summary = get_payment_summary(start_date, end_date)
    
    # Top clientes
    top_customers = get_top_customers(start_date, end_date)
    
    # Top produtos
    top_products = get_top_products(start_date, end_date)
    
    return render_template(
        'reports/summary.html',
        period=period,
        start_date=start_date,
        end_date=end_date,
        summary=summary,
        payment_summary=payment_summary,
        top_customers=top_customers,
        top_products=top_products
    )

def get_financial_summary(start_date, end_date):
    """
    Gera um resumo financeiro do período
    
    Args:
        start_date: Data inicial
        end_date: Data final
        
    Returns:
        Dicionário com os dados do resumo
    """
    # Valores padrão
    summary = {
        'total_income': 0.0,
        'total_expense': 0.0,
        'balance': 0.0,
        'total_tax': 0.0,
        'tax_percentage': 0.0,
        'margin': 0.0,
        'invoice_count_in': 0,
        'invoice_count_out': 0
    }
    
    # Buscar invoices do período
    invoices = Invoice.query.filter(
        Invoice.issue_date.between(start_date, end_date),
        Invoice.status != InvoiceStatus.CANCELLED
    ).all()
    
    if not invoices:
        return summary
    
    # Separar entre entrada e saída
    inbound_invoices = []
    outbound_invoices = []
    
    for invoice in invoices:
        if invoice.type == InvoiceType.INBOUND:
            inbound_invoices.append(invoice)
        else:
            outbound_invoices.append(invoice)
    
    # Calcular totais
    total_inbound = sum(float(inv.total_value) for inv in inbound_invoices)
    total_outbound = sum(float(inv.total_value) for inv in outbound_invoices)
    total_tax = sum(float(inv.total_tax) for inv in invoices)
    
    # Calcular o balanço
    balance = total_outbound - total_inbound
    
    # Calcular percentuais
    tax_percentage = (total_tax / total_outbound * 100) if total_outbound > 0 else 0
    margin = (balance / total_outbound * 100) if total_outbound > 0 else 0
    
    # Montar o resumo
    summary['total_income'] = total_outbound
    summary['total_expense'] = total_inbound
    summary['balance'] = balance
    summary['total_tax'] = total_tax
    summary['tax_percentage'] = tax_percentage
    summary['margin'] = margin
    summary['invoice_count_in'] = len(inbound_invoices)
    summary['invoice_count_out'] = len(outbound_invoices)
    
    return summary

def get_payment_summary(start_date, end_date):
    """
    Gera um resumo dos pagamentos do período
    
    Args:
        start_date: Data inicial
        end_date: Data final
        
    Returns:
        Dicionário com os dados do resumo
    """
    # Valores padrão
    summary = {
        'paid': 0.0,
        'pending': 0.0,
        'overdue': 0.0,
        'cancelled': 0.0,
        'paid_count': 0,
        'pending_count': 0,
        'overdue_count': 0,
        'cancelled_count': 0
    }
    
    # Pagamentos pagos
    paid_result = db.session.query(
        func.sum(Payment.amount).label('total'),
        func.count(Payment.id).label('count')
    ).filter(
        Payment.status == PaymentStatus.PAID,
        Payment.due_date.between(start_date, end_date)
    ).first()
    
    if paid_result and paid_result.total:
        summary['paid'] = float(paid_result.total)
        summary['paid_count'] = paid_result.count
    
    # Pagamentos pendentes
    pending_result = db.session.query(
        func.sum(Payment.amount).label('total'),
        func.count(Payment.id).label('count')
    ).filter(
        Payment.status == PaymentStatus.PENDING,
        Payment.due_date.between(start_date, end_date),
        Payment.due_date >= date.today()  # Não vencido ainda
    ).first()
    
    if pending_result and pending_result.total:
        summary['pending'] = float(pending_result.total)
        summary['pending_count'] = pending_result.count
    
    # Pagamentos vencidos
    overdue_result = db.session.query(
        func.sum(Payment.amount).label('total'),
        func.count(Payment.id).label('count')
    ).filter(
        Payment.status == PaymentStatus.PENDING,
        Payment.due_date.between(start_date, end_date),
        Payment.due_date < date.today()  # Já vencido
    ).first()
    
    if overdue_result and overdue_result.total:
        summary['overdue'] = float(overdue_result.total)
        summary['overdue_count'] = overdue_result.count
    
    # Pagamentos cancelados
    cancelled_result = db.session.query(
        func.sum(Payment.amount).label('total'),
        func.count(Payment.id).label('count')
    ).filter(
        Payment.status == PaymentStatus.CANCELLED,
        Payment.due_date.between(start_date, end_date)
    ).first()
    
    if cancelled_result and cancelled_result.total:
        summary['cancelled'] = float(cancelled_result.total)
        summary['cancelled_count'] = cancelled_result.count
    
    return summary

def get_top_customers(start_date, end_date, limit=5):
    """
    Retorna os principais clientes do período
    
    Args:
        start_date: Data inicial
        end_date: Data final
        limit: Limite de resultados
        
    Returns:
        Lista com os principais clientes
    """
    # Buscar as notas fiscais de saída
    outbound_invoices = Invoice.query.filter(
        Invoice.issue_date.between(start_date, end_date),
        Invoice.type == InvoiceType.OUTBOUND,
        Invoice.status != InvoiceStatus.CANCELLED,
        Invoice.customer_id.isnot(None)
    ).all()
    
    if not outbound_invoices:
        return []
    
    # Agrupar por cliente
    customers = {}
    total_value = 0.0
    
    for invoice in outbound_invoices:
        if not invoice.customer:
            continue
            
        customer_id = invoice.customer.id
        
        if customer_id not in customers:
            customers[customer_id] = {
                'id': customer_id,
                'name': invoice.customer.name,
                'total': 0.0,
                'count': 0
            }
        
        customers[customer_id]['total'] += float(invoice.total_value)
        customers[customer_id]['count'] += 1
        total_value += float(invoice.total_value)
    
    # Calcular percentual sobre o total
    for customer_id in customers:
        customers[customer_id]['percentage'] = (customers[customer_id]['total'] / total_value * 100) if total_value > 0 else 0
    
    # Ordenar e limitar
    result = sorted(customers.values(), key=lambda x: x['total'], reverse=True)
    return result[:limit]

def get_top_products(start_date, end_date, limit=5):
    """
    Retorna os principais produtos vendidos no período
    
    Args:
        start_date: Data inicial
        end_date: Data final
        limit: Limite de resultados
        
    Returns:
        Lista com os principais produtos
    """
    # Buscar as notas fiscais de saída
    outbound_invoices = Invoice.query.filter(
        Invoice.issue_date.between(start_date, end_date),
        Invoice.type == InvoiceType.OUTBOUND,
        Invoice.status != InvoiceStatus.CANCELLED
    ).all()
    
    if not outbound_invoices:
        return []
    
    # Agrupar por produto
    products = {}
    total_value = 0.0
    
    for invoice in outbound_invoices:
        for item in invoice.items:
            if not item.product:
                continue
                
            product_id = item.product.id
            
            if product_id not in products:
                products[product_id] = {
                    'id': product_id,
                    'name': item.product.name,
                    'quantity': 0.0,
                    'total': 0.0
                }
            
            products[product_id]['quantity'] += float(item.quantity)
            products[product_id]['total'] += float(item.total)
            total_value += float(item.total)
    
    # Calcular percentual sobre o total
    for product_id in products:
        products[product_id]['percentage'] = (products[product_id]['total'] / total_value * 100) if total_value > 0 else 0
    
    # Ordenar e limitar
    result = sorted(products.values(), key=lambda x: x['total'], reverse=True)
    return result[:limit]

@reports_bp.route('/generate', methods=['POST'])
@login_required
def report_generation():
    form = ReportForm()
    
    if form.validate_on_submit():
        report_type = form.report_type.data
        format_type = form.format_type.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        
        try:
            # Criar diretório temporário para o relatório
            temp_dir = tempfile.mkdtemp()
            
            if report_type == 'invoices':
                # Filtrar notas fiscais
                query = Invoice.query.filter(
                    Invoice.issue_date.between(start_date, end_date)
                )
                
                if form.invoice_type.data:
                    query = query.filter(Invoice.type == form.invoice_type.data)
                
                if form.invoice_status.data:
                    query = query.filter(Invoice.status == form.invoice_status.data)
                
                invoices = query.all()
                
                if not invoices:
                    flash('Nenhuma nota fiscal encontrada para o período selecionado.', 'warning')
                    return render_template('reports/generate.html', form=form)
                
                # Gerar relatório
                filename = generate_invoice_report(
                    invoices, 
                    format_type, 
                    temp_dir, 
                    form.include_items.data
                )
                
                report_title = "Relatório de Notas Fiscais"
            
            elif report_type == 'users':
                # Filtrar usuários
                users = User.query.all()
                
                if not users:
                    flash('Nenhum usuário encontrado.', 'warning')
                    return render_template('reports/generate.html', form=form)
                
                # Gerar relatório
                filename = generate_user_report(users, format_type, temp_dir)
                report_title = "Relatório de Usuários"
            
            elif report_type == 'inventory':
                # Buscar produtos e estoque atual
                products = Product.query.all()
                
                if not products:
                    flash('Nenhum produto encontrado.', 'warning')
                    return render_template('reports/generate.html', form=form)
                
                # Gerar relatório
                filename = generate_inventory_report(products, format_type, temp_dir)
                report_title = "Relatório de Estoque"
            
            elif report_type == 'financial':
                # Filtrar dados financeiros
                invoices = Invoice.query.filter(
                    Invoice.issue_date.between(start_date, end_date),
                    Invoice.status != InvoiceStatus.CANCELLED
                ).all()
                
                if not invoices:
                    flash('Nenhuma nota fiscal encontrada para o período selecionado.', 'warning')
                    return render_template('reports/generate.html', form=form)
                
                # Gerar relatório financeiro
                filename = generate_financial_report(
                    invoices, 
                    format_type, 
                    temp_dir, 
                    start_date, 
                    end_date
                )
                report_title = "Relatório Financeiro"
            
            # Registrar log de auditoria
            log = AuditLog(
                user_id=current_user.id,
                action='report',
                table_name=report_type,
                row_id=None,
                new_values=f"Relatório gerado: {report_title} ({format_type}), período: {start_date} a {end_date}",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            # Enviar o arquivo
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if format_type == 'excel' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            
            return send_file(
                filename,
                as_attachment=True,
                download_name=f"{report_title}_{datetime.now().strftime('%Y%m%d')}.{'xlsx' if format_type == 'excel' else 'docx'}",
                mimetype=mimetype
            )
        
        except Exception as e:
            flash(f'Erro ao gerar relatório: {str(e)}', 'danger')
            return render_template('reports/generate.html', form=form)
    
    return render_template('reports/generate.html', form=form)

@reports_bp.route('/audit-logs')
@login_required
def audit_logs():
    # Verificar se o usuário tem permissão
    if current_user.role.value not in ['Administrador', 'Gerente']:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Filtros
    user_id = request.args.get('user_id', type=int)
    action = request.args.get('action')
    table_name = request.args.get('table_name')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query
    query = AuditLog.query
    
    # Apply filters if provided
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    if action:
        query = query.filter_by(action=action)
    
    if table_name:
        query = query.filter_by(table_name=table_name)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp >= start_date)
        except ValueError:
            flash('Formato de data de início inválido. Use o formato YYYY-MM-DD.', 'warning')
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date = datetime.combine(end_date, datetime.max.time())
            query = query.filter(AuditLog.timestamp <= end_date)
        except ValueError:
            flash('Formato de data de fim inválido. Use o formato YYYY-MM-DD.', 'warning')
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
    
    logs = query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=per_page)
    
    # Lista de usuários para o filtro
    users = User.query.all()
    
    # Lista de ações para o filtro
    actions = ['login', 'logout', 'create', 'update', 'delete', 'import', 'export', 'report', 'cancel']
    
    # Lista de tabelas para o filtro
    tables = ['users', 'invoices', 'products', 'customers', 'suppliers', 'inventory_movements', 'payments']
    
    return render_template(
        'reports/audit_logs_list.html', 
        logs=logs, 
        users=users,
        actions=actions,
        tables=tables,
        filters={
            'user_id': user_id,
            'action': action,
            'table_name': table_name,
            'start_date': start_date,
            'end_date': end_date
        }
    )
