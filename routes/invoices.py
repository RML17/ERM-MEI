from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from sqlalchemy import desc
import tempfile
import os
from datetime import datetime

from app import db
from models import (
    Invoice, InvoiceItem, InvoiceTax, InvoiceType, InvoiceStatus, 
    Product, Customer, Supplier, AuditLog
)
from forms import (
    InvoiceForm, InvoiceItemForm, InvoiceSearchForm, 
    UploadXMLForm, CustomerForm, SupplierForm
)
from services.invoice_service import create_invoice_from_form, update_invoice_from_form
from services.tax_service import calculate_invoice_taxes as calculate_taxes
from services.xml_service import import_invoice_from_xml, export_invoice_to_xml
from services.inventory_service import process_invoice_inventory

invoices_bp = Blueprint('invoices', __name__, url_prefix='/invoices')

@invoices_bp.route('/')
@login_required
def index():
    form = InvoiceSearchForm(request.args)
    
    # Base query
    query = Invoice.query
    
    # Apply filters if provided
    if form.validate():
        if form.invoice_number.data:
            query = query.filter(Invoice.invoice_number.ilike(f'%{form.invoice_number.data}%'))
        
        if form.start_date.data:
            query = query.filter(Invoice.issue_date >= form.start_date.data)
            
        if form.end_date.data:
            query = query.filter(Invoice.issue_date <= form.end_date.data)
            
        if form.type.data:
            query = query.filter(Invoice.type == form.type.data)
            
        if form.status.data:
            query = query.filter(Invoice.status == form.status.data)
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
    
    invoices = query.order_by(desc(Invoice.created_at)).paginate(page=page, per_page=per_page)
    
    return render_template('invoices/list.html', invoices=invoices, form=form)

@invoices_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = InvoiceForm()
    
    # Preencher as opções dos selects
    form.populate_select_fields()
    
    if form.validate_on_submit():
        try:
            invoice = create_invoice_from_form(form, current_user.id)
            
            # Processar movimentação de estoque
            if invoice.status != InvoiceStatus.DRAFT:
                process_invoice_inventory(invoice)
            
            # Registrar log de auditoria
            log = AuditLog(
                user_id=current_user.id,
                action='create',
                table_name='invoices',
                row_id=invoice.id,
                new_values=f"type={invoice.type.value}, status={invoice.status.value}, total={invoice.total_value}",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Nota fiscal criada com sucesso!', 'success')
            return redirect(url_for('invoices.view', id=invoice.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar nota fiscal: {str(e)}', 'danger')
    
    return render_template('invoices/create.html', form=form)

@invoices_bp.route('/<int:id>')
@login_required
def view(id):
    invoice = Invoice.query.get_or_404(id)
    items = invoice.items.all()
    taxes = invoice.taxes.all()
    payments = invoice.payments.all()
    
    return render_template(
        'invoices/view.html', 
        invoice=invoice, 
        items=items, 
        taxes=taxes,
        payments=payments
    )

@invoices_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    invoice = Invoice.query.get_or_404(id)
    
    # Verificar se a nota pode ser editada
    if invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.PENDING]:
        flash('Essa nota fiscal não pode ser editada no status atual.', 'warning')
        return redirect(url_for('invoices.view', id=invoice.id))
    
    form = InvoiceForm(obj=invoice)
    form.populate_select_fields()
    
    # Pré-popular itens
    items = []
    for item in invoice.items:
        item_form = InvoiceItemForm(obj=item)
        item_form.product_id.choices = [(p.id, f"{p.sku} - {p.name}") for p in Product.query.all()]
        items.append(item_form)
    
    if form.validate_on_submit():
        try:
            old_values = f"type={invoice.type.value}, status={invoice.status.value}, total={invoice.total_value}"
            
            # Verificar se houve mudança de status que requer processamento de estoque
            old_status = invoice.status
            
            invoice = update_invoice_from_form(invoice, form)
            
            # Processar movimentação de estoque se o status mudou
            if old_status != invoice.status and invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.CANCELLED]:
                process_invoice_inventory(invoice)
            
            new_values = f"type={invoice.type.value}, status={invoice.status.value}, total={invoice.total_value}"
            
            # Registrar log de auditoria
            log = AuditLog(
                user_id=current_user.id,
                action='update',
                table_name='invoices',
                row_id=invoice.id,
                old_values=old_values,
                new_values=new_values,
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Nota fiscal atualizada com sucesso!', 'success')
            return redirect(url_for('invoices.view', id=invoice.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar nota fiscal: {str(e)}', 'danger')
    
    return render_template('invoices/edit.html', form=form, invoice=invoice, items=items)

@invoices_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel(id):
    invoice = Invoice.query.get_or_404(id)
    
    # Verificar se a nota pode ser cancelada
    if invoice.status == InvoiceStatus.CANCELLED:
        flash('Essa nota fiscal já está cancelada.', 'warning')
        return redirect(url_for('invoices.view', id=invoice.id))
    
    if invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.PENDING, InvoiceStatus.ISSUED]:
        flash('Essa nota fiscal não pode ser cancelada no status atual.', 'warning')
        return redirect(url_for('invoices.view', id=invoice.id))
    
    try:
        old_status = invoice.status
        
        invoice.status = InvoiceStatus.CANCELLED
        db.session.commit()
        
        # Registrar log de auditoria
        log = AuditLog(
            user_id=current_user.id,
            action='cancel',
            table_name='invoices',
            row_id=invoice.id,
            old_values=f"status={old_status.value}",
            new_values=f"status={invoice.status.value}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Nota fiscal cancelada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cancelar nota fiscal: {str(e)}', 'danger')
    
    return redirect(url_for('invoices.view', id=invoice.id))

@invoices_bp.route('/<int:id>/export-xml')
@login_required
def export_xml(id):
    invoice = Invoice.query.get_or_404(id)
    
    if invoice.status not in [InvoiceStatus.ISSUED, InvoiceStatus.APPROVED]:
        flash('Essa nota fiscal não pode ser exportada no status atual.', 'warning')
        return redirect(url_for('invoices.view', id=invoice.id))
    
    try:
        xml_content = export_invoice_to_xml(invoice)
        
        # Criar arquivo temporário para download
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xml')
        temp_filename = temp_file.name
        
        with open(temp_filename, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        # Determinar o nome do arquivo
        filename = f"NF_{invoice.invoice_number}_{invoice.series}.xml"
        
        # Registrar log de auditoria
        log = AuditLog(
            user_id=current_user.id,
            action='export',
            table_name='invoices',
            row_id=invoice.id,
            old_values=None,
            new_values=f"Exportado XML: {filename}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return send_file(
            temp_filename,
            as_attachment=True,
            download_name=filename,
            mimetype='application/xml'
        )
    except Exception as e:
        flash(f'Erro ao exportar XML: {str(e)}', 'danger')
        return redirect(url_for('invoices.view', id=invoice.id))

@invoices_bp.route('/import-xml', methods=['GET', 'POST'])
@login_required
def import_xml():
    form = UploadXMLForm()
    
    if form.validate_on_submit():
        try:
            xml_file = form.xml_file.data
            invoice_type = form.invoice_type.data
            
            # Processar o arquivo XML
            invoice = import_invoice_from_xml(xml_file, invoice_type, current_user.id)
            
            # Registrar log de auditoria
            log = AuditLog(
                user_id=current_user.id,
                action='import',
                table_name='invoices',
                row_id=invoice.id,
                new_values=f"Importado XML: {xml_file.filename}, tipo={invoice_type.value}",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Nota fiscal importada com sucesso!', 'success')
            return redirect(url_for('invoices.view', id=invoice.id))
        except Exception as e:
            flash(f'Erro ao importar XML: {str(e)}', 'danger')
    
    return render_template('invoices/import.html', form=form)

@invoices_bp.route('/calculate-taxes', methods=['POST'])
@login_required
def calculate_taxes_endpoint():
    """Endpoint para calcular impostos baseado nos itens da nota"""
    data = request.json
    
    if not data or 'items' not in data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    try:
        items = data['items']
        invoice_type = InvoiceType(data.get('invoice_type', 'OUTBOUND'))
        
        tax_results = calculate_taxes(items, invoice_type)
        
        return jsonify({
            'success': True,
            'taxes': tax_results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@invoices_bp.route('/customers', methods=['GET', 'POST'])
@login_required
def customers():
    form = CustomerForm()
    
    if form.validate_on_submit():
        customer = Customer(
            name=form.name.data,
            document_type=form.document_type.data,
            document=form.document.data,
            state_registration=form.state_registration.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            zip_code=form.zip_code.data,
            phone=form.phone.data,
            email=form.email.data
        )
        
        db.session.add(customer)
        db.session.commit()
        
        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('invoices.customers'))
    
    # Listar clientes
    customers_list = Customer.query.order_by(Customer.name).all()
    
    return render_template('invoices/customers_list.html', form=form, customers=customers_list)

@invoices_bp.route('/suppliers', methods=['GET', 'POST'])
@login_required
def suppliers():
    form = SupplierForm()
    
    if form.validate_on_submit():
        supplier = Supplier(
            name=form.name.data,
            cnpj=form.cnpj.data,
            state_registration=form.state_registration.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            zip_code=form.zip_code.data,
            phone=form.phone.data,
            email=form.email.data,
            contact_name=form.contact_name.data
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        flash('Fornecedor cadastrado com sucesso!', 'success')
        return redirect(url_for('invoices.suppliers'))
    
    # Listar fornecedores
    suppliers_list = Supplier.query.order_by(Supplier.name).all()
    
    return render_template('invoices/suppliers_list.html', form=form, suppliers=suppliers_list)
