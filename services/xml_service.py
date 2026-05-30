import xml.etree.ElementTree as ET
from lxml import etree
from datetime import datetime
import tempfile
import os
from decimal import Decimal

from app import db
from models import (
    Invoice, InvoiceItem, InvoiceTax, InvoiceType, InvoiceStatus,
    Customer, Supplier, Product, TaxType
)


def import_invoice_from_xml(xml_file, invoice_type, user_id):
    """
    Importa uma nota fiscal a partir de um arquivo XML
    
    Args:
        xml_file: Arquivo XML enviado pelo usuário
        invoice_type: Tipo de nota fiscal (entrada ou saída)
        user_id: ID do usuário que está importando
    
    Returns:
        Objeto Invoice criado
    """
    try:
        # Ler o arquivo XML
        xml_content = xml_file.read().decode('utf-8')
        
        # Extrair dados do XML
        root = etree.fromstring(xml_content)
        
        # Processar conforme o tipo de XML (NF-e, CT-e, etc)
        if 'NFe' in xml_content:
            invoice = _process_nfe_xml(root, invoice_type, user_id)
        elif 'CTe' in xml_content:
            invoice = _process_cte_xml(root, invoice_type, user_id)
        else:
            raise ValueError("Formato de XML não reconhecido")
        
        # Salvar o caminho do XML se necessário
        if invoice.id:
            temp_dir = tempfile.gettempdir()
            xml_filename = f"invoice_{invoice.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xml"
            xml_path = os.path.join(temp_dir, xml_filename)
            
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            invoice.xml_path = xml_path
            db.session.commit()
        
        return invoice
    
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Erro ao processar o XML: {str(e)}")


def export_invoice_to_xml(invoice):
    """
    Exporta uma nota fiscal para XML
    
    Args:
        invoice: Objeto Invoice a ser exportado
    
    Returns:
        String contendo o XML gerado
    """
    try:
        # Criar estrutura básica do XML
        root = ET.Element("NFe", xmlns="http://www.portalfiscal.inf.br/nfe")
        
        # Informações da nota
        inf_nfe = ET.SubElement(root, "infNFe", Id=f"NFe{invoice.invoice_number}{invoice.series}")
        
        # Identificação
        ide = ET.SubElement(inf_nfe, "ide")
        ET.SubElement(ide, "cUF").text = "35"  # Código do estado (SP)
        ET.SubElement(ide, "cNF").text = invoice.invoice_number
        ET.SubElement(ide, "natOp").text = "Venda" if invoice.type == InvoiceType.OUTBOUND else "Compra"
        ET.SubElement(ide, "serie").text = invoice.series
        ET.SubElement(ide, "nNF").text = invoice.invoice_number
        ET.SubElement(ide, "dhEmi").text = invoice.issue_date.strftime('%Y-%m-%dT%H:%M:%S-03:00')
        ET.SubElement(ide, "dhSaiEnt").text = invoice.operation_date.strftime('%Y-%m-%dT%H:%M:%S-03:00')
        
        # Emitente (empresa)
        emit = ET.SubElement(inf_nfe, "emit")
        # Teria que buscar os dados da empresa aqui
        ET.SubElement(emit, "CNPJ").text = "00000000000000"  # Exemplo
        ET.SubElement(emit, "xNome").text = "Empresa Exemplo"
        
        # Destinatário (cliente) ou remetente (fornecedor)
        if invoice.type == InvoiceType.OUTBOUND and invoice.customer:
            dest = ET.SubElement(inf_nfe, "dest")
            if invoice.customer.document_type == "CNPJ":
                ET.SubElement(dest, "CNPJ").text = invoice.customer.document
            else:
                ET.SubElement(dest, "CPF").text = invoice.customer.document
            ET.SubElement(dest, "xNome").text = invoice.customer.name
        elif invoice.type == InvoiceType.INBOUND and invoice.supplier:
            dest = ET.SubElement(inf_nfe, "emit")
            ET.SubElement(dest, "CNPJ").text = invoice.supplier.cnpj
            ET.SubElement(dest, "xNome").text = invoice.supplier.name
        
        # Itens
        for idx, item in enumerate(invoice.items, 1):
            det = ET.SubElement(inf_nfe, "det", nItem=str(idx))
            
            # Produto
            prod = ET.SubElement(det, "prod")
            ET.SubElement(prod, "cProd").text = item.product.sku if item.product else ""
            ET.SubElement(prod, "xProd").text = item.product.name if item.product else ""
            ET.SubElement(prod, "NCM").text = item.ncm or ""
            ET.SubElement(prod, "CFOP").text = item.cfop or "5102"
            ET.SubElement(prod, "uCom").text = "UN"
            ET.SubElement(prod, "qCom").text = str(float(item.quantity))
            ET.SubElement(prod, "vUnCom").text = f"{float(item.unit_price):.2f}"
            ET.SubElement(prod, "vProd").text = f"{float(item.total):.2f}"
            
            # Impostos
            imposto = ET.SubElement(det, "imposto")
            
            # ICMS
            icms = ET.SubElement(imposto, "ICMS")
            for tax in invoice.taxes:
                if tax.tax_type == TaxType.ICMS:
                    icms_item = ET.SubElement(icms, "ICMS00")
                    ET.SubElement(icms_item, "orig").text = "0"
                    ET.SubElement(icms_item, "CST").text = "00"
                    ET.SubElement(icms_item, "modBC").text = "0"
                    ET.SubElement(icms_item, "vBC").text = f"{float(tax.tax_base):.2f}"
                    ET.SubElement(icms_item, "pICMS").text = f"{float(tax.tax_rate) * 100:.2f}"
                    ET.SubElement(icms_item, "vICMS").text = f"{float(tax.tax_value):.2f}"
                    break
            
            # PIS
            pis = ET.SubElement(imposto, "PIS")
            for tax in invoice.taxes:
                if tax.tax_type == TaxType.PIS:
                    pis_item = ET.SubElement(pis, "PISAliq")
                    ET.SubElement(pis_item, "CST").text = "01"
                    ET.SubElement(pis_item, "vBC").text = f"{float(tax.tax_base):.2f}"
                    ET.SubElement(pis_item, "pPIS").text = f"{float(tax.tax_rate) * 100:.2f}"
                    ET.SubElement(pis_item, "vPIS").text = f"{float(tax.tax_value):.2f}"
                    break
            
            # COFINS
            cofins = ET.SubElement(imposto, "COFINS")
            for tax in invoice.taxes:
                if tax.tax_type == TaxType.COFINS:
                    cofins_item = ET.SubElement(cofins, "COFINSAliq")
                    ET.SubElement(cofins_item, "CST").text = "01"
                    ET.SubElement(cofins_item, "vBC").text = f"{float(tax.tax_base):.2f}"
                    ET.SubElement(cofins_item, "pCOFINS").text = f"{float(tax.tax_rate) * 100:.2f}"
                    ET.SubElement(cofins_item, "vCOFINS").text = f"{float(tax.tax_value):.2f}"
                    break
        
        # Totais
        total = ET.SubElement(inf_nfe, "total")
        icms_total = ET.SubElement(total, "ICMSTot")
        ET.SubElement(icms_total, "vBC").text = f"{sum(float(t.tax_base) for t in invoice.taxes if t.tax_type == TaxType.ICMS):.2f}"
        ET.SubElement(icms_total, "vICMS").text = f"{sum(float(t.tax_value) for t in invoice.taxes if t.tax_type == TaxType.ICMS):.2f}"
        ET.SubElement(icms_total, "vProd").text = f"{float(invoice.total_products):.2f}"
        ET.SubElement(icms_total, "vNF").text = f"{float(invoice.total_value):.2f}"
        
        # Transformar em string XML
        xml_string = ET.tostring(root, encoding='unicode')
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
        
        return f"{xml_declaration}\n{xml_string}"
    
    except Exception as e:
        raise ValueError(f"Erro ao gerar o XML: {str(e)}")


def _process_nfe_xml(root, invoice_type, user_id):
    """
    Processa um XML de NF-e
    
    Args:
        root: Elemento raiz do XML
        invoice_type: Tipo de nota fiscal
        user_id: ID do usuário
    
    Returns:
        Objeto Invoice criado
    """
    # Definir namespace
    ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
    
    # Extrair informações da nota
    inf_nfe = root.find('.//nfe:infNFe', ns)
    
    if inf_nfe is None:
        raise ValueError("Estrutura de XML inválida: infNFe não encontrado")
    
    # Identificação da nota
    ide = inf_nfe.find('.//nfe:ide', ns)
    
    if ide is None:
        raise ValueError("Estrutura de XML inválida: ide não encontrado")
    
    invoice_number = ide.findtext('.//nfe:nNF', namespaces=ns)
    series = ide.findtext('.//nfe:serie', namespaces=ns)
    
    # Datas
    emission_date_str = ide.findtext('.//nfe:dhEmi', namespaces=ns)
    if emission_date_str:
        issue_date = datetime.fromisoformat(emission_date_str.replace('Z', '+00:00').replace('-03:00', '+00:00'))
    else:
        issue_date = datetime.now()
    
    operation_date_str = ide.findtext('.//nfe:dhSaiEnt', namespaces=ns) or emission_date_str
    if operation_date_str:
        operation_date = datetime.fromisoformat(operation_date_str.replace('Z', '+00:00').replace('-03:00', '+00:00'))
    else:
        operation_date = issue_date
    
    # Cliente ou fornecedor
    entity_id = None
    
    if invoice_type == InvoiceType.OUTBOUND:
        # Se for nota de saída, procurar destinatário
        dest = inf_nfe.find('.//nfe:dest', ns)
        
        if dest is not None:
            document = dest.findtext('.//nfe:CNPJ', namespaces=ns) or dest.findtext('.//nfe:CPF', namespaces=ns)
            name = dest.findtext('.//nfe:xNome', namespaces=ns)
            
            # Verificar se cliente existe
            if document:
                customer = Customer.query.filter_by(document=document).first()
                
                if not customer:
                    # Criar novo cliente
                    document_type = 'CNPJ' if len(document) > 11 else 'CPF'
                    customer = Customer(
                        name=name,
                        document_type=document_type,
                        document=document
                    )
                    db.session.add(customer)
                    db.session.flush()
                
                entity_id = customer.id
    else:
        # Se for nota de entrada, procurar emitente
        emit = inf_nfe.find('.//nfe:emit', ns)
        
        if emit is not None:
            cnpj = emit.findtext('.//nfe:CNPJ', namespaces=ns)
            name = emit.findtext('.//nfe:xNome', namespaces=ns)
            
            # Verificar se fornecedor existe
            if cnpj:
                supplier = Supplier.query.filter_by(cnpj=cnpj).first()
                
                if not supplier:
                    # Criar novo fornecedor
                    supplier = Supplier(
                        name=name,
                        cnpj=cnpj
                    )
                    db.session.add(supplier)
                    db.session.flush()
                
                entity_id = supplier.id
    
    # Criar a nota fiscal
    invoice = Invoice(
        invoice_number=invoice_number,
        series=series,
        type=invoice_type,
        status=InvoiceStatus.PENDING,
        issue_date=issue_date.date(),
        operation_date=operation_date.date(),
        total_value=Decimal('0.00'),  # Será calculado
        total_products=Decimal('0.00'),  # Será calculado
        total_tax=Decimal('0.00'),  # Será calculado
        notes=f"Importado de XML em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        created_by_id=user_id
    )
    
    # Associar cliente ou fornecedor
    if invoice_type == InvoiceType.OUTBOUND:
        invoice.customer_id = entity_id
    else:
        invoice.supplier_id = entity_id
    
    db.session.add(invoice)
    db.session.flush()  # Para obter o ID da nota
    
    # Processar itens
    items = inf_nfe.findall('.//nfe:det', ns)
    total_products = Decimal('0.00')
    
    for item_xml in items:
        # Informações do produto
        prod = item_xml.find('.//nfe:prod', ns)
        
        if prod is None:
            continue
        
        sku = prod.findtext('.//nfe:cProd', namespaces=ns)
        name = prod.findtext('.//nfe:xProd', namespaces=ns)
        ncm = prod.findtext('.//nfe:NCM', namespaces=ns)
        cfop = prod.findtext('.//nfe:CFOP', namespaces=ns)
        quantity = Decimal(prod.findtext('.//nfe:qCom', namespaces=ns) or '0')
        unit_price = Decimal(prod.findtext('.//nfe:vUnCom', namespaces=ns) or '0')
        total = Decimal(prod.findtext('.//nfe:vProd', namespaces=ns) or '0')
        
        # Verificar se produto existe
        product = None
        if sku:
            product = Product.query.filter_by(sku=sku).first()
            
            if not product:
                # Criar novo produto
                product = Product(
                    sku=sku,
                    name=name,
                    ncm=ncm,
                    purchase_price=unit_price,
                    sale_price=unit_price * Decimal('1.3')  # Markup de 30%
                )
                db.session.add(product)
                db.session.flush()
        
        # Criar item da nota
        item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=product.id if product else None,
            quantity=quantity,
            unit_price=unit_price,
            discount=Decimal('0.00'),
            total=total,
            cfop=cfop,
            ncm=ncm
        )
        
        db.session.add(item)
        total_products += total
    
    # Processar impostos
    tax_totals = inf_nfe.find('.//nfe:ICMSTot', ns)
    
    if tax_totals is not None:
        # ICMS
        icms_base = Decimal(tax_totals.findtext('.//nfe:vBC', namespaces=ns) or '0')
        icms_value = Decimal(tax_totals.findtext('.//nfe:vICMS', namespaces=ns) or '0')
        
        if icms_value > 0:
            icms_rate = (icms_value / icms_base) if icms_base > 0 else Decimal('0.18')
            
            icms_tax = InvoiceTax(
                invoice_id=invoice.id,
                tax_type=TaxType.ICMS,
                tax_rate=icms_rate,
                tax_base=icms_base,
                tax_value=icms_value
            )
            db.session.add(icms_tax)
        
        # PIS
        pis_base = Decimal(tax_totals.findtext('.//nfe:vPIS', namespaces=ns) or '0')
        pis_value = Decimal(tax_totals.findtext('.//nfe:vPIS', namespaces=ns) or '0')
        
        if pis_value > 0:
            pis_rate = Decimal('0.0165')  # Alíquota padrão
            
            pis_tax = InvoiceTax(
                invoice_id=invoice.id,
                tax_type=TaxType.PIS,
                tax_rate=pis_rate,
                tax_base=total_products,
                tax_value=pis_value
            )
            db.session.add(pis_tax)
        
        # COFINS
        cofins_base = Decimal(tax_totals.findtext('.//nfe:vCOFINS', namespaces=ns) or '0')
        cofins_value = Decimal(tax_totals.findtext('.//nfe:vCOFINS', namespaces=ns) or '0')
        
        if cofins_value > 0:
            cofins_rate = Decimal('0.076')  # Alíquota padrão
            
            cofins_tax = InvoiceTax(
                invoice_id=invoice.id,
                tax_type=TaxType.COFINS,
                tax_rate=cofins_rate,
                tax_base=total_products,
                tax_value=cofins_value
            )
            db.session.add(cofins_tax)
    
    # Atualizar totais da nota
    total_tax = sum(float(t.tax_value) for t in invoice.taxes)
    total_value = float(total_products) + total_tax
    
    invoice.total_products = total_products
    invoice.total_tax = Decimal(str(total_tax))
    invoice.total_value = Decimal(str(total_value))
    
    db.session.commit()
    
    return invoice


def _process_cte_xml(root, invoice_type, user_id):
    """
    Processa um XML de CT-e (conhecimento de transporte)
    
    Args:
        root: Elemento raiz do XML
        invoice_type: Tipo de nota fiscal
        user_id: ID do usuário
    
    Returns:
        Objeto Invoice criado
    """
    # Implementação similar ao _process_nfe_xml, mas adaptada para CT-e
    # Por simplicidade, vamos apenas criar uma nota fiscal básica
    
    # Definir namespace
    ns = {'cte': 'http://www.portalfiscal.inf.br/cte'}
    
    # Extrair informações do CT-e
    inf_cte = root.find('.//cte:infCte', ns)
    
    if inf_cte is None:
        raise ValueError("Estrutura de XML inválida: infCte não encontrado")
    
    # Identificação do CT-e
    ide = inf_cte.find('.//cte:ide', ns)
    
    if ide is None:
        raise ValueError("Estrutura de XML inválida: ide não encontrado")
    
    invoice_number = ide.findtext('.//cte:nCT', namespaces=ns)
    series = ide.findtext('.//cte:serie', namespaces=ns)
    
    # Datas
    emission_date_str = ide.findtext('.//cte:dhEmi', namespaces=ns)
    if emission_date_str:
        issue_date = datetime.fromisoformat(emission_date_str.replace('Z', '+00:00').replace('-03:00', '+00:00'))
    else:
        issue_date = datetime.now()
    
    operation_date = issue_date
    
    # Criar a nota fiscal simplificada
    invoice = Invoice(
        invoice_number=invoice_number,
        series=series,
        type=invoice_type,
        status=InvoiceStatus.PENDING,
        issue_date=issue_date.date(),
        operation_date=operation_date.date(),
        total_value=Decimal('0.00'),  # Será calculado
        total_products=Decimal('0.00'),  # Será calculado
        total_tax=Decimal('0.00'),  # Será calculado
        notes=f"Importado de CT-e em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        created_by_id=user_id
    )
    
    db.session.add(invoice)
    db.session.commit()
    
    return invoice
