from decimal import Decimal
from datetime import datetime

from app import db
from models import (
    Product, InventoryEntry, InventoryMovement, 
    InvoiceItem, Invoice, InvoiceType, InvoiceStatus
)


def get_current_stock(product_id):
    """
    Calcula o estoque atual de um produto
    
    Args:
        product_id: ID do produto
    
    Returns:
        Quantidade em estoque ou None se não houver registros
    """
    # Consultar todas as movimentações do produto
    movements = InventoryMovement.query.filter_by(product_id=product_id).all()
    
    if not movements:
        return 0  # Sem movimentações, estoque é zero
    
    # Calcular o saldo
    stock = 0
    for movement in movements:
        if movement.movement_type == 'entrada':
            stock += float(movement.quantity)
        else:
            stock -= float(movement.quantity)
    
    return stock


def process_inventory_output(product_id, quantity):
    """
    Processa uma saída de estoque usando o método FIFO
    
    Args:
        product_id: ID do produto
        quantity: Quantidade a ser retirada
    
    Returns:
        Lista de tuplas com os IDs das entradas usadas, quantidades e custos
        [(entry_id, quantity, cost), ...]
    """
    # Verificar se há estoque suficiente
    current_stock = get_current_stock(product_id)
    if current_stock is None or float(quantity) > current_stock:
        raise ValueError(f"Estoque insuficiente. Disponível: {current_stock}")
    
    # Buscar entradas com saldo, ordenadas por data (FIFO)
    entries = InventoryEntry.query.filter_by(
        product_id=product_id
    ).filter(
        InventoryEntry.remaining_quantity > 0
    ).order_by(
        InventoryEntry.entry_date
    ).all()
    
    remaining_quantity = float(quantity)
    entries_used = []
    
    for entry in entries:
        if remaining_quantity <= 0:
            break
        
        entry_available = float(entry.remaining_quantity)
        
        if entry_available >= remaining_quantity:
            # Esta entrada tem quantidade suficiente
            qty_to_use = remaining_quantity
            entry.remaining_quantity = entry_available - qty_to_use
            remaining_quantity = 0
        else:
            # Usar toda a quantidade disponível desta entrada
            qty_to_use = entry_available
            entry.remaining_quantity = 0
            remaining_quantity -= qty_to_use
        
        entries_used.append((entry.id, qty_to_use, float(entry.unit_cost)))
    
    db.session.commit()
    
    return entries_used


def process_invoice_inventory(invoice):
    """
    Processa a movimentação de estoque para uma nota fiscal
    
    Args:
        invoice: Objeto da nota fiscal
    """
    # Ignorar processamento se a nota estiver em rascunho ou cancelada
    if invoice.status in [InvoiceStatus.DRAFT, InvoiceStatus.CANCELLED]:
        return
    
    # Verificar o tipo de nota
    if invoice.type == InvoiceType.INBOUND:
        # Nota de entrada - adicionar itens ao estoque
        for item in invoice.items:
            # Criar entrada no estoque
            entry = InventoryEntry(
                product_id=item.product_id,
                invoice_item_id=item.id,
                quantity=item.quantity,
                unit_cost=item.unit_price,
                remaining_quantity=item.quantity,
                notes=f"Entrada via NF {invoice.invoice_number}"
            )
            db.session.add(entry)
            db.session.flush()  # Para obter o ID da entrada
            
            # Registrar movimentação
            movement = InventoryMovement(
                product_id=item.product_id,
                invoice_item_id=item.id,
                inventory_entry_id=entry.id,
                movement_type='entrada',
                quantity=item.quantity,
                unit_cost=item.unit_price,
                notes=f"Entrada via NF {invoice.invoice_number}"
            )
            db.session.add(movement)
    
    elif invoice.type == InvoiceType.OUTBOUND:
        # Nota de saída - remover itens do estoque
        for item in invoice.items:
            try:
                # Processar saída usando FIFO
                entries_used = process_inventory_output(
                    item.product_id,
                    item.quantity
                )
                
                # Registrar as movimentações para cada entrada utilizada
                for entry_id, qty, cost in entries_used:
                    movement = InventoryMovement(
                        product_id=item.product_id,
                        invoice_item_id=item.id,
                        inventory_entry_id=entry_id,
                        movement_type='saída',
                        quantity=qty,
                        unit_cost=cost,
                        notes=f"Saída via NF {invoice.invoice_number}"
                    )
                    db.session.add(movement)
            
            except ValueError as e:
                # Rollback e propagar erro
                db.session.rollback()
                raise ValueError(f"Erro ao processar item {item.product.name}: {str(e)}")
    
    db.session.commit()


def get_inventory_valuation():
    """
    Calcula a valoração atual do estoque
    
    Returns:
        Lista de dicionários com produto, quantidade e valor
    """
    products = Product.query.all()
    result = []
    
    for product in products:
        stock = get_current_stock(product.id)
        
        if stock and stock > 0:
            # Buscar entradas com saldo
            entries = InventoryEntry.query.filter_by(
                product_id=product.id
            ).filter(
                InventoryEntry.remaining_quantity > 0
            ).all()
            
            # Calcular valor total do estoque deste produto
            value = sum(float(entry.remaining_quantity) * float(entry.unit_cost) for entry in entries)
            
            result.append({
                'product': product,
                'quantity': stock,
                'value': value,
                'avg_cost': value / stock if stock > 0 else 0
            })
    
    return result
