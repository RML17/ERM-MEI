from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import desc
from datetime import datetime, date

from app import db
from models import Payment, PaymentMethod, PaymentStatus, Invoice, AuditLog
from forms import PaymentForm, PaymentSearchForm

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/')
@login_required
def index():
    form = PaymentSearchForm(request.args)
    
    # Base query
    query = Payment.query
    
    # Apply filters if provided
    if form.validate():
        if form.invoice_number.data:
            query = query.join(Invoice).filter(Invoice.invoice_number.ilike(f'%{form.invoice_number.data}%'))
        
        if form.start_due_date.data:
            query = query.filter(Payment.due_date >= form.start_due_date.data)
            
        if form.end_due_date.data:
            query = query.filter(Payment.due_date <= form.end_due_date.data)
            
        if form.payment_method.data:
            query = query.filter(Payment.payment_method == form.payment_method.data)
            
        if form.status.data:
            query = query.filter(Payment.status == form.status.data)
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
    
    payments = query.order_by(desc(Payment.due_date)).paginate(page=page, per_page=per_page)
    
    return render_template('payments/list.html', payments=payments, form=form)

@payments_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = PaymentForm()
    
    # Preencher as opções dos selects
    form.invoice_id.choices = [(i.id, f"{i.invoice_number} - {i.total_value}") for i in Invoice.query.filter(
        Invoice.status.in_([status for status in InvoiceStatus if status != InvoiceStatus.CANCELLED])
    ).all()]
    
    if form.validate_on_submit():
        try:
            payment = Payment(
                invoice_id=form.invoice_id.data,
                payment_method=form.payment_method.data,
                status=PaymentStatus.PENDING,
                due_date=form.due_date.data,
                amount=form.amount.data,
                paid_amount=0,
                document_number=form.document_number.data,
                notes=form.notes.data,
                registered_by_id=current_user.id
            )
            
            db.session.add(payment)
            
            # Registrar log de auditoria
            log = AuditLog(
                user_id=current_user.id,
                action='create',
                table_name='payments',
                row_id=None,  # Será atualizado após o commit
                new_values=f"payment_method={payment.payment_method.value}, amount={payment.amount}, due_date={payment.due_date}",
                ip_address=request.remote_addr
            )
            
            db.session.add(log)
            db.session.commit()
            
            # Atualizar o row_id do log com o ID do pagamento criado
            log.row_id = payment.id
            db.session.commit()
            
            flash('Pagamento registrado com sucesso!', 'success')
            return redirect(url_for('payments.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar pagamento: {str(e)}', 'danger')
    
    return render_template('payments/create.html', form=form)

@payments_bp.route('/<int:id>')
@login_required
def view(id):
    payment = Payment.query.get_or_404(id)
    return render_template('payments/view.html', payment=payment)

@payments_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    payment = Payment.query.get_or_404(id)
    
    # Verificar se o pagamento pode ser editado
    if payment.status == PaymentStatus.PAID and payment.paid_amount >= payment.amount:
        flash('Este pagamento já foi quitado e não pode ser editado.', 'warning')
        return redirect(url_for('payments.view', id=payment.id))
    
    form = PaymentForm(obj=payment)
    form.invoice_id.choices = [(i.id, f"{i.invoice_number} - {i.total_value}") for i in Invoice.query.filter(
        Invoice.status.in_([status for status in InvoiceStatus if status != InvoiceStatus.CANCELLED])
    ).all()]
    
    if form.validate_on_submit():
        try:
            old_values = f"payment_method={payment.payment_method.value}, amount={payment.amount}, due_date={payment.due_date}"
            
            payment.invoice_id = form.invoice_id.data
            payment.payment_method = form.payment_method.data
            payment.due_date = form.due_date.data
            payment.amount = form.amount.data
            payment.document_number = form.document_number.data
            payment.notes = form.notes.data
            payment.updated_at = datetime.utcnow()
            
            # Registrar log de auditoria
            log = AuditLog(
                user_id=current_user.id,
                action='update',
                table_name='payments',
                row_id=payment.id,
                old_values=old_values,
                new_values=f"payment_method={payment.payment_method.value}, amount={payment.amount}, due_date={payment.due_date}",
                ip_address=request.remote_addr
            )
            
            db.session.add(log)
            db.session.commit()
            
            flash('Pagamento atualizado com sucesso!', 'success')
            return redirect(url_for('payments.view', id=payment.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar pagamento: {str(e)}', 'danger')
    
    return render_template('payments/edit.html', form=form, payment=payment)

@payments_bp.route('/<int:id>/record-payment', methods=['POST'])
@login_required
def record_payment(id):
    payment = Payment.query.get_or_404(id)
    
    # Verificar se o pagamento já foi quitado
    if payment.status == PaymentStatus.PAID and payment.paid_amount >= payment.amount:
        flash('Este pagamento já foi quitado.', 'warning')
        return redirect(url_for('payments.view', id=payment.id))
    
    # Obter dados do formulário
    paid_amount = float(request.form.get('paid_amount', 0))
    payment_date = request.form.get('payment_date')
    transaction_id = request.form.get('transaction_id', '')
    
    try:
        old_status = payment.status
        old_paid_amount = payment.paid_amount
        
        # Converter data
        try:
            payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
        except:
            payment_date = date.today()
        
        # Atualizar pagamento
        payment.paid_amount = float(payment.paid_amount or 0) + paid_amount
        payment.payment_date = payment_date
        payment.transaction_id = transaction_id
        
        # Atualizar status
        if payment.paid_amount >= payment.amount:
            payment.status = PaymentStatus.PAID
        elif payment.paid_amount > 0:
            payment.status = PaymentStatus.PARTIAL
        
        payment.updated_at = datetime.utcnow()
        
        # Registrar log de auditoria
        log = AuditLog(
            user_id=current_user.id,
            action='payment',
            table_name='payments',
            row_id=payment.id,
            old_values=f"status={old_status.value}, paid_amount={old_paid_amount}",
            new_values=f"status={payment.status.value}, paid_amount={payment.paid_amount}, payment_date={payment_date}",
            ip_address=request.remote_addr
        )
        
        db.session.add(log)
        db.session.commit()
        
        flash('Pagamento registrado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao registrar pagamento: {str(e)}', 'danger')
    
    return redirect(url_for('payments.view', id=payment.id))

@payments_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel(id):
    payment = Payment.query.get_or_404(id)
    
    # Verificar se o pagamento pode ser cancelado
    if payment.status == PaymentStatus.CANCELLED:
        flash('Este pagamento já está cancelado.', 'warning')
        return redirect(url_for('payments.view', id=payment.id))
    
    try:
        old_status = payment.status
        
        payment.status = PaymentStatus.CANCELLED
        payment.updated_at = datetime.utcnow()
        
        # Registrar log de auditoria
        log = AuditLog(
            user_id=current_user.id,
            action='cancel',
            table_name='payments',
            row_id=payment.id,
            old_values=f"status={old_status.value}",
            new_values=f"status={payment.status.value}",
            ip_address=request.remote_addr
        )
        
        db.session.add(log)
        db.session.commit()
        
        flash('Pagamento cancelado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cancelar pagamento: {str(e)}', 'danger')
    
    return redirect(url_for('payments.view', id=payment.id))

@payments_bp.route('/overdue')
@login_required
def overdue():
    # Buscar pagamentos vencidos
    overdue_payments = Payment.query.filter(
        Payment.due_date < date.today(),
        Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.PARTIAL])
    ).order_by(Payment.due_date).all()
    
    return render_template('payments/overdue.html', payments=overdue_payments)
