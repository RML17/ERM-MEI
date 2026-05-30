from datetime import datetime, date, timedelta
from app import db
from models import Payment, PaymentStatus, Invoice, InvoiceStatus


def register_payment(payment_id, paid_amount, payment_date, transaction_id, user_id):
    """
    Registra um pagamento para uma fatura
    
    Args:
        payment_id: ID do pagamento
        paid_amount: Valor pago
        payment_date: Data do pagamento
        transaction_id: ID da transação (opcional)
        user_id: ID do usuário que registrou o pagamento
    
    Returns:
        Objeto Payment atualizado
    """
    payment = Payment.query.get(payment_id)
    
    if not payment:
        raise ValueError("Pagamento não encontrado")
    
    # Verificar se o pagamento já foi quitado
    if payment.status == PaymentStatus.PAID and payment.paid_amount >= payment.amount:
        raise ValueError("Este pagamento já foi quitado")
    
    if payment.status == PaymentStatus.CANCELLED:
        raise ValueError("Este pagamento está cancelado")
    
    # Atualizar pagamento
    payment.paid_amount = float(payment.paid_amount or 0) + float(paid_amount)
    payment.payment_date = payment_date
    
    if transaction_id:
        payment.transaction_id = transaction_id
    
    # Atualizar status
    if payment.paid_amount >= payment.amount:
        payment.status = PaymentStatus.PAID
    elif payment.paid_amount > 0:
        payment.status = PaymentStatus.PARTIAL
    
    payment.updated_at = datetime.utcnow()
    payment.registered_by_id = user_id
    
    db.session.commit()
    
    return payment


def cancel_payment(payment_id, user_id):
    """
    Cancela um pagamento
    
    Args:
        payment_id: ID do pagamento
        user_id: ID do usuário que cancelou o pagamento
    
    Returns:
        Objeto Payment atualizado
    """
    payment = Payment.query.get(payment_id)
    
    if not payment:
        raise ValueError("Pagamento não encontrado")
    
    # Verificar se o pagamento já está cancelado
    if payment.status == PaymentStatus.CANCELLED:
        raise ValueError("Este pagamento já está cancelado")
    
    # Cancelar pagamento
    payment.status = PaymentStatus.CANCELLED
    payment.updated_at = datetime.utcnow()
    payment.registered_by_id = user_id
    
    db.session.commit()
    
    return payment


def get_overdue_payments():
    """
    Retorna todos os pagamentos vencidos
    
    Returns:
        Lista de objetos Payment vencidos
    """
    today = date.today()
    
    overdue_payments = Payment.query.filter(
        Payment.due_date < today,
        Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.PARTIAL])
    ).order_by(Payment.due_date).all()
    
    return overdue_payments


def get_upcoming_payments(days=7):
    """
    Retorna pagamentos a vencer nos próximos dias
    
    Args:
        days: Número de dias para verificar
    
    Returns:
        Lista de objetos Payment a vencer
    """
    today = date.today()
    future_date = today + timedelta(days=days)
    
    upcoming_payments = Payment.query.filter(
        Payment.due_date.between(today, future_date),
        Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.PARTIAL])
    ).order_by(Payment.due_date).all()
    
    return upcoming_payments


def create_payment_from_invoice(invoice_id, payment_method, due_date, amount, document_number=None, notes=None, user_id=None):
    """
    Cria um novo pagamento a partir de uma nota fiscal
    
    Args:
        invoice_id: ID da nota fiscal
        payment_method: Método de pagamento
        due_date: Data de vencimento
        amount: Valor do pagamento
        document_number: Número do documento (opcional)
        notes: Observações (opcional)
        user_id: ID do usuário que registrou o pagamento
    
    Returns:
        Objeto Payment criado
    """
    invoice = Invoice.query.get(invoice_id)
    
    if not invoice:
        raise ValueError("Nota fiscal não encontrada")
    
    # Verificar se a nota pode gerar pagamento
    if invoice.status == InvoiceStatus.CANCELLED:
        raise ValueError("Não é possível criar pagamento para nota cancelada")
    
    payment = Payment(
        invoice_id=invoice_id,
        payment_method=payment_method,
        status=PaymentStatus.PENDING,
        due_date=due_date,
        amount=amount,
        paid_amount=0,
        document_number=document_number,
        notes=notes,
        registered_by_id=user_id
    )
    
    db.session.add(payment)
    db.session.commit()
    
    return payment


def get_payment_summary(start_date=None, end_date=None):
    """
    Retorna um resumo dos pagamentos por status
    
    Args:
        start_date: Data inicial para o período (opcional)
        end_date: Data final para o período (opcional)
    
    Returns:
        Dicionário com contagem e valores por status
    """
    query = Payment.query
    
    if start_date:
        query = query.filter(Payment.due_date >= start_date)
    
    if end_date:
        query = query.filter(Payment.due_date <= end_date)
    
    payments = query.all()
    
    summary = {
        'PENDING': {'count': 0, 'value': 0},
        'PAID': {'count': 0, 'value': 0},
        'PARTIAL': {'count': 0, 'value': 0},
        'OVERDUE': {'count': 0, 'value': 0},
        'CANCELLED': {'count': 0, 'value': 0},
        'TOTAL': {'count': 0, 'value': 0}
    }
    
    today = date.today()
    
    for payment in payments:
        status_key = payment.status.name
        
        # Tratar pagamentos vencidos
        if payment.status in [PaymentStatus.PENDING, PaymentStatus.PARTIAL] and payment.due_date < today:
            status_key = 'OVERDUE'
        
        summary[status_key]['count'] += 1
        summary[status_key]['value'] += float(payment.amount)
        
        summary['TOTAL']['count'] += 1
        summary['TOTAL']['value'] += float(payment.amount)
    
    return summary
