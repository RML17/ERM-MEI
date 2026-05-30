from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from datetime import datetime

from app import db
from models import (
    Product, InventoryEntry, InventoryMovement, 
    InvoiceItem, Invoice, AuditLog
)
from forms import ProductForm, InventoryMovementForm, ProductSearchForm

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/products')
@login_required
def products():
    form = ProductSearchForm(request.args)
    
    # Base query
    query = Product.query
    
    # Apply filters if provided
    if form.validate():
        if form.sku.data:
            query = query.filter(Product.sku.ilike(f'%{form.sku.data}%'))
        
        if form.name.data:
            query = query.filter(Product.name.ilike(f'%{form.name.data}%'))
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
    
    products = query.order_by(Product.name).paginate(page=page, per_page=per_page)
    
    # Carregar os dados de estoque atual
    for product in products.items:
        product.stock = product.current_stock()
    
    return render_template('inventory/products.html', products=products, form=form)

@inventory_bp.route('/products/create', methods=['GET', 'POST'])
@login_required
def create_product():
    form = ProductForm()
    
    if form.validate_on_submit():
        try:
            product = Product(
                sku=form.sku.data,
                name=form.name.data,
                description=form.description.data,
                purchase_price=form.purchase_price.data,
                sale_price=form.sale_price.data,
                min_stock=form.min_stock.data,
                ncm=form.ncm.data,
                weight=form.weight.data
            )
            
            db.session.add(product)
            
            # Registrar log de auditoria
            log = AuditLog(
                user_id=current_user.id,
                action='create',
                table_name='products',
                row_id=None,  # Será atualizado após o commit
                new_values=f"sku={product.sku}, name={product.name}, purchase_price={product.purchase_price}",
                ip_address=request.remote_addr
            )
            
            db.session.add(log)
            db.session.commit()
            
            # Atualizar o row_id do log com o ID do produto criado
            log.row_id = product.id
            db.session.commit()
            
            flash('Produto cadastrado com sucesso!', 'success')
            return redirect(url_for('inventory.products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar produto: {str(e)}', 'danger')
    
    return render_template('inventory/create_product.html', form=form)

@inventory_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        try:
            old_values = f"sku={product.sku}, name={product.name}, purchase_price={product.purchase_price}, sale_price={product.sale_price}"
            
            product.sku = form.sku.data
            product.name = form.name.data
            product.description = form.description.data
            product.purchase_price = form.purchase_price.data
            product.sale_price = form.sale_price.data
            product.min_stock = form.min_stock.data
            product.ncm = form.ncm.data
            product.weight = form.weight.data
            product.updated_at = datetime.utcnow()
            
            # Registrar log de auditoria
            log = AuditLog(
                user_id=current_user.id,
                action='update',
                table_name='products',
                row_id=product.id,
                old_values=old_values,
                new_values=f"sku={product.sku}, name={product.name}, purchase_price={product.purchase_price}, sale_price={product.sale_price}",
                ip_address=request.remote_addr
            )
            
            db.session.add(log)
            db.session.commit()
            
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('inventory.products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar produto: {str(e)}', 'danger')
    
    return render_template('inventory/edit_product.html', form=form, product=product)

@inventory_bp.route('/products/<int:id>')
@login_required
def view_product(id):
    product = Product.query.get_or_404(id)
    current_stock = product.current_stock()
    
    # Buscar movimentações recentes
    movements = InventoryMovement.query.filter_by(product_id=product.id).order_by(
        desc(InventoryMovement.movement_date)
    ).limit(100).all()
    
    # Buscar entradas de estoque ativas (FIFO)
    entries = InventoryEntry.query.filter_by(product_id=product.id).filter(
        InventoryEntry.remaining_quantity > 0
    ).order_by(InventoryEntry.entry_date).all()
    
    return render_template(
        'inventory/view_product.html', 
        product=product, 
        current_stock=current_stock,
        movements=movements,
        entries=entries
    )

@inventory_bp.route('/movements')
@login_required
def movements():
    # Filtros
    product_id = request.args.get('product_id', type=int)
    movement_type = request.args.get('movement_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query
    query = InventoryMovement.query
    
    # Apply filters if provided
    if product_id:
        query = query.filter_by(product_id=product_id)
    
    if movement_type:
        query = query.filter_by(movement_type=movement_type)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(InventoryMovement.movement_date >= start_date)
        except ValueError:
            flash('Formato de data de início inválido. Use o formato YYYY-MM-DD.', 'warning')
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date = datetime.combine(end_date, datetime.max.time())
            query = query.filter(InventoryMovement.movement_date <= end_date)
        except ValueError:
            flash('Formato de data de fim inválido. Use o formato YYYY-MM-DD.', 'warning')
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
    
    movements = query.order_by(desc(InventoryMovement.movement_date)).paginate(page=page, per_page=per_page)
    
    # Lista de produtos para o filtro
    products = Product.query.order_by(Product.name).all()
    
    return render_template(
        'inventory/movements.html', 
        movements=movements, 
        products=products,
        filters={
            'product_id': product_id,
            'movement_type': movement_type,
            'start_date': start_date,
            'end_date': end_date
        }
    )

@inventory_bp.route('/movement/create', methods=['GET', 'POST'])
@login_required
def create_movement():
    form = InventoryMovementForm()
    form.product_id.choices = [(p.id, f"{p.sku} - {p.name}") for p in Product.query.all()]
    
    if form.validate_on_submit():
        try:
            product_id = form.product_id.data
            quantity = form.quantity.data
            movement_type = form.movement_type.data
            notes = form.notes.data
            
            # Verificar estoque disponível para saídas
            product = Product.query.get(product_id)
            current_stock = product.current_stock()
            
            if movement_type == 'saída' and (current_stock is None or quantity > current_stock):
                flash(f'Estoque insuficiente. Disponível: {current_stock}', 'danger')
                return render_template('inventory/create_movement.html', form=form)
            
            # Processar a movimentação
            if movement_type == 'entrada':
                # Criar uma nova entrada no estoque
                entry = InventoryEntry(
                    product_id=product_id,
                    quantity=quantity,
                    unit_cost=form.unit_cost.data,
                    remaining_quantity=quantity,
                    notes=notes
                )
                db.session.add(entry)
                db.session.flush()  # Para obter o ID da entrada
                
                # Registrar a movimentação
                movement = InventoryMovement(
                    product_id=product_id,
                    inventory_entry_id=entry.id,
                    movement_type=movement_type,
                    quantity=quantity,
                    unit_cost=form.unit_cost.data,
                    notes=notes
                )
                db.session.add(movement)
            else:  # Saída
                from services.inventory_service import process_inventory_output
                
                # Processar saída usando FIFO
                entries_used = process_inventory_output(product_id, quantity)
                
                # Registrar as movimentações para cada entrada utilizada
                for entry_id, qty, cost in entries_used:
                    movement = InventoryMovement(
                        product_id=product_id,
                        inventory_entry_id=entry_id,
                        movement_type=movement_type,
                        quantity=qty,
                        unit_cost=cost,
                        notes=notes
                    )
                    db.session.add(movement)
            
            # Registrar log de auditoria
            log = AuditLog(
                user_id=current_user.id,
                action='create',
                table_name='inventory_movements',
                row_id=None,
                new_values=f"product_id={product_id}, movement_type={movement_type}, quantity={quantity}",
                ip_address=request.remote_addr
            )
            
            db.session.add(log)
            db.session.commit()
            
            flash('Movimentação de estoque registrada com sucesso!', 'success')
            return redirect(url_for('inventory.movements'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar movimentação: {str(e)}', 'danger')
    
    return render_template('inventory/create_movement.html', form=form)
