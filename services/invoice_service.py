from decimal import Decimal
from datetime import datetime

from app import db
from models import Invoice, InvoiceItem, InvoiceType, InvoiceStatus, Product


def create_invoice_from_form(form, user_id):
    """
    Cria uma nova nota fiscal a partir dos dados do formulário
    """
    try:
        # Criar a invoice
        invoice = Invoice(
            number=form.number.data,
            type=form.type.data,
            status=InvoiceStatus.DRAFT,
            issue_date=form.issue_date.data,
            due_date=form.due_date.data,
            customer_name=form.customer_name.data,
            customer_document=form.customer_document.data,
            customer_email=form.customer_email.data,
            customer_address=form.customer_address.data,
            observations=form.observations.data,
            created_by=user_id
        )
        
        db.session.add(invoice)
        db.session.flush()  # Para obter o ID
        
        # Calcular subtotal dos itens
        subtotal = Decimal('0.00')
        
        # Adicionar itens
        for item_form in form.items.data:
            if item_form.get('product_id'):
                product = Product.query.get(item_form['product_id'])
                
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=product.id if product else None,
                    description=item_form['description'] or (product.name if product else ''),
                    quantity=Decimal(str(item_form['quantity'])),
                    unit_price=Decimal(str(item_form['unit_price'])),
                    discount=Decimal(str(item_form.get('discount', 0))),
                    unit=item_form.get('unit', 'UN'),
                    ncm=product.ncm if product else item_form.get('ncm', '')
                )
                
                # Calcular total do item
                item_total = item.quantity * item.unit_price
                if item.discount > 0:
                    item_total -= (item_total * item.discount / 100)
                
                item.total = item_total
                subtotal += item_total
                
                db.session.add(item)
        
        # Atualizar totais da invoice
        invoice.subtotal = subtotal
        invoice.total_tax = Decimal('0.00')  # Será calculado pelo módulo fiscal
        invoice.total = subtotal + invoice.total_tax
        
        db.session.commit()
        return invoice
        
    except Exception as e:
        db.session.rollback()
        raise e


def update_invoice_from_form(invoice, form):
    """
    Atualiza uma nota fiscal existente a partir dos dados do formulário
    """
    try:
        # Atualizar dados da invoice
        invoice.number = form.number.data
        invoice.type = form.type.data
        invoice.issue_date = form.issue_date.data
        invoice.due_date = form.due_date.data
        invoice.customer_name = form.customer_name.data
        invoice.customer_document = form.customer_document.data
        invoice.customer_email = form.customer_email.data
        invoice.customer_address = form.customer_address.data
        invoice.observations = form.observations.data
        invoice.updated_at = datetime.utcnow()
        
        # Remover itens existentes
        InvoiceItem.query.filter_by(invoice_id=invoice.id).delete()
        
        # Calcular subtotal dos novos itens
        subtotal = Decimal('0.00')
        
        # Adicionar novos itens
        for item_form in form.items.data:
            if item_form.get('product_id'):
                product = Product.query.get(item_form['product_id'])
                
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=product.id if product else None,
                    description=item_form['description'] or (product.name if product else ''),
                    quantity=Decimal(str(item_form['quantity'])),
                    unit_price=Decimal(str(item_form['unit_price'])),
                    discount=Decimal(str(item_form.get('discount', 0))),
                    unit=item_form.get('unit', 'UN'),
                    ncm=product.ncm if product else item_form.get('ncm', '')
                )
                
                # Calcular total do item
                item_total = item.quantity * item.unit_price
                if item.discount > 0:
                    item_total -= (item_total * item.discount / 100)
                
                item.total = item_total
                subtotal += item_total
                
                db.session.add(item)
        
        # Atualizar totais da invoice
        invoice.subtotal = subtotal
        invoice.total_tax = Decimal('0.00')  # Será calculado pelo módulo fiscal
        invoice.total = subtotal + invoice.total_tax
        
        db.session.commit()
        return invoice
        
    except Exception as e:
        db.session.rollback()
        raise e