from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import enum


class UserRole(enum.Enum):
    ADMIN = 'Administrador'
    MANAGER = 'Gerente'
    ACCOUNTANT = 'Contador'
    INVENTORY = 'Estoquista'
    SALES = 'Vendas'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.SALES)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    state_registration = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(9))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    document_type = db.Column(db.String(4), nullable=False)  # CPF ou CNPJ
    document = db.Column(db.String(18), unique=True, nullable=False)
    state_registration = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(9))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relação com invoices
    invoices = db.relationship('Invoice', backref='customer', lazy='dynamic')


class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    state_registration = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(9))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(120))
    contact_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relação com invoices
    invoices = db.relationship('Invoice', backref='supplier', lazy='dynamic')


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    purchase_price = db.Column(db.Numeric(10, 2), nullable=False)
    sale_price = db.Column(db.Numeric(10, 2), nullable=False)
    min_stock = db.Column(db.Integer, default=0)
    ncm = db.Column(db.String(8))  # Código NCM para classificação fiscal
    weight = db.Column(db.Numeric(10, 3))  # Peso em kg
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relações
    inventory_entries = db.relationship('InventoryEntry', backref='product', lazy='dynamic')
    invoice_items = db.relationship('InvoiceItem', backref='product', lazy='dynamic')
    
    def current_stock(self):
        """Calcula o estoque atual baseado nas entradas e saídas"""
        from services.inventory_service import get_current_stock
        return get_current_stock(self.id)


class InvoiceType(enum.Enum):
    INBOUND = 'Entrada'  # Nota de entrada
    OUTBOUND = 'Saída'  # Nota de saída


class InvoiceStatus(enum.Enum):
    DRAFT = 'Rascunho'
    PENDING = 'Pendente'
    ISSUED = 'Emitida'
    CANCELLED = 'Cancelada'
    APPROVED = 'Aprovada'


class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), nullable=False)
    series = db.Column(db.String(3), nullable=False)
    type = db.Column(db.Enum(InvoiceType), nullable=False)
    status = db.Column(db.Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    issue_date = db.Column(db.Date, nullable=False)
    operation_date = db.Column(db.Date, nullable=False)
    total_value = db.Column(db.Numeric(10, 2), nullable=False)
    total_products = db.Column(db.Numeric(10, 2), nullable=False)
    total_tax = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text)
    xml_path = db.Column(db.String(255))  # Caminho para o arquivo XML
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relações
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.relationship('User', backref='created_invoices')
    
    items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')
    taxes = db.relationship('InvoiceTax', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='invoice', lazy='dynamic')


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    cfop = db.Column(db.String(4))  # Código Fiscal de Operações e Prestações
    ncm = db.Column(db.String(8))  # Classificação fiscal do produto


class TaxType(enum.Enum):
    ICMS = 'ICMS'
    IPI = 'IPI'
    PIS = 'PIS'
    COFINS = 'COFINS'
    ISS = 'ISS'
    OUTROS = 'Outros'


class InvoiceTax(db.Model):
    __tablename__ = 'invoice_taxes'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    tax_type = db.Column(db.Enum(TaxType), nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False)  # em percentual
    tax_base = db.Column(db.Numeric(10, 2), nullable=False)  # base de cálculo
    tax_value = db.Column(db.Numeric(10, 2), nullable=False)  # valor do imposto
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class InventoryEntry(db.Model):
    __tablename__ = 'inventory_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    invoice_item_id = db.Column(db.Integer, db.ForeignKey('invoice_items.id'))
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=False)
    entry_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    remaining_quantity = db.Column(db.Numeric(10, 3), nullable=False)  # Para controle FIFO
    notes = db.Column(db.Text)
    
    invoice_item = db.relationship('InvoiceItem')


class InventoryMovement(db.Model):
    __tablename__ = 'inventory_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    invoice_item_id = db.Column(db.Integer, db.ForeignKey('invoice_items.id'))
    inventory_entry_id = db.Column(db.Integer, db.ForeignKey('inventory_entries.id'))
    movement_type = db.Column(db.String(10), nullable=False)  # 'entrada' ou 'saída'
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=False)
    movement_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notes = db.Column(db.Text)
    
    product = db.relationship('Product')
    invoice_item = db.relationship('InvoiceItem')
    inventory_entry = db.relationship('InventoryEntry')


class PaymentMethod(enum.Enum):
    BOLETO = 'Boleto'
    DEPOSITO = 'Depósito'
    TRANSFERENCIA = 'Transferência'
    CARTAO = 'Cartão'
    DINHEIRO = 'Dinheiro'
    PIX = 'PIX'
    CHEQUE = 'Cheque'


class PaymentStatus(enum.Enum):
    PENDING = 'Pendente'
    PAID = 'Pago'
    OVERDUE = 'Vencido'
    CANCELLED = 'Cancelado'
    PARTIAL = 'Parcial'


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING)
    due_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    paid_amount = db.Column(db.Numeric(10, 2), default=0)
    payment_date = db.Column(db.Date)
    transaction_id = db.Column(db.String(100))
    document_number = db.Column(db.String(100))  # Número do boleto, cheque, etc.
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Quem registrou o pagamento
    registered_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    registered_by = db.relationship('User')


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)
    table_name = db.Column(db.String(50), nullable=False)
    row_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)
    new_values = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')


# =============================================
# MÓDULO LOGÍSTICO
# =============================================

class ShippingCompanyType(enum.Enum):
    CORREIOS = 'Correios'
    TRANSPORTADORA = 'Transportadora'
    MOTOBOY = 'Motoboy'
    FROTA_PROPRIA = 'Frota Própria'
    AEREA = 'Aérea'
    MARITIMA = 'Marítima'


class ShippingCompany(db.Model):
    __tablename__ = 'shipping_companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(18), unique=True)
    company_type = db.Column(db.Enum(ShippingCompanyType), nullable=False)
    contact_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(15))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(9))
    
    # Configurações de serviço
    delivery_time_min = db.Column(db.Integer)  # dias úteis mínimo
    delivery_time_max = db.Column(db.Integer)  # dias úteis máximo
    weight_limit = db.Column(db.Numeric(10, 3))  # kg
    volume_limit = db.Column(db.Numeric(10, 3))  # m³
    coverage_area = db.Column(db.Text)  # JSON com áreas de cobertura
    
    # Preços base
    price_per_kg = db.Column(db.Numeric(10, 2))
    price_per_km = db.Column(db.Numeric(10, 2))
    minimum_price = db.Column(db.Numeric(10, 2))
    
    # Configurações
    is_active = db.Column(db.Boolean, default=True)
    api_token = db.Column(db.String(255))  # Para integração com APIs
    tracking_url = db.Column(db.String(255))
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ShippingCompany {self.name}>'


class RouteType(enum.Enum):
    LOCAL = 'Local'
    ESTADUAL = 'Estadual'
    NACIONAL = 'Nacional'
    INTERNACIONAL = 'Internacional'


class Route(db.Model):
    __tablename__ = 'routes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    origin_zip = db.Column(db.String(9), nullable=False)
    destination_zip = db.Column(db.String(9), nullable=False)
    origin_city = db.Column(db.String(100))
    origin_state = db.Column(db.String(2))
    destination_city = db.Column(db.String(100))
    destination_state = db.Column(db.String(2))
    
    distance_km = db.Column(db.Numeric(10, 2))
    estimated_time_hours = db.Column(db.Numeric(5, 2))
    route_type = db.Column(db.Enum(RouteType), nullable=False)
    
    # Custo base da rota
    base_cost = db.Column(db.Numeric(10, 2))
    fuel_cost_per_km = db.Column(db.Numeric(10, 4))
    toll_cost = db.Column(db.Numeric(10, 2))
    
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def total_cost(self):
        """Calcula o custo total da rota"""
        base = float(self.base_cost or 0)
        fuel = float(self.fuel_cost_per_km or 0) * float(self.distance_km or 0)
        toll = float(self.toll_cost or 0)
        return base + fuel + toll
    
    def __repr__(self):
        return f'<Route {self.name}>'


class ShipmentStatus(enum.Enum):
    PENDING = 'Pendente'
    CONFIRMED = 'Confirmado'
    PICKED_UP = 'Coletado'
    IN_TRANSIT = 'Em Trânsito'
    OUT_FOR_DELIVERY = 'Saiu para Entrega'
    DELIVERED = 'Entregue'
    RETURNED = 'Devolvido'
    CANCELLED = 'Cancelado'


class Shipment(db.Model):
    __tablename__ = 'shipments'
    
    id = db.Column(db.Integer, primary_key=True)
    tracking_code = db.Column(db.String(50), unique=True, nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    shipping_company_id = db.Column(db.Integer, db.ForeignKey('shipping_companies.id'))
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'))
    
    # Informações do remetente
    sender_name = db.Column(db.String(100), nullable=False)
    sender_address = db.Column(db.String(200), nullable=False)
    sender_city = db.Column(db.String(100), nullable=False)
    sender_state = db.Column(db.String(2), nullable=False)
    sender_zip = db.Column(db.String(9), nullable=False)
    sender_phone = db.Column(db.String(15))
    
    # Informações do destinatário
    recipient_name = db.Column(db.String(100), nullable=False)
    recipient_address = db.Column(db.String(200), nullable=False)
    recipient_city = db.Column(db.String(100), nullable=False)
    recipient_state = db.Column(db.String(2), nullable=False)
    recipient_zip = db.Column(db.String(9), nullable=False)
    recipient_phone = db.Column(db.String(15))
    recipient_email = db.Column(db.String(120))
    
    # Informações da carga
    total_weight = db.Column(db.Numeric(10, 3), nullable=False)  # kg
    total_volume = db.Column(db.Numeric(10, 3))  # m³
    declared_value = db.Column(db.Numeric(10, 2))
    package_count = db.Column(db.Integer, default=1)
    
    # Status e datas
    status = db.Column(db.Enum(ShipmentStatus), default=ShipmentStatus.PENDING)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    pickup_date = db.Column(db.DateTime)
    estimated_delivery = db.Column(db.DateTime)
    delivered_date = db.Column(db.DateTime)
    
    # Custos
    freight_cost = db.Column(db.Numeric(10, 2))
    insurance_cost = db.Column(db.Numeric(10, 2))
    additional_fees = db.Column(db.Numeric(10, 2))
    total_cost = db.Column(db.Numeric(10, 2))
    
    # Observações e informações extras
    delivery_instructions = db.Column(db.Text)
    notes = db.Column(db.Text)
    external_tracking_code = db.Column(db.String(100))  # Código da transportadora
    
    # Quem criou o envio
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.relationship('User')
    
    # Relacionamentos
    invoice = db.relationship('Invoice', backref='shipments')
    shipping_company = db.relationship('ShippingCompany', backref='shipments')
    route = db.relationship('Route', backref='shipments')
    
    def calculate_freight(self):
        """Calcula o frete baseado no peso, distância e transportadora"""
        if not self.shipping_company or not self.route:
            return 0
            
        base_cost = float(self.route.total_cost())
        weight_cost = float(self.shipping_company.price_per_kg or 0) * float(self.total_weight)
        distance_cost = float(self.shipping_company.price_per_km or 0) * float(self.route.distance_km or 0)
        
        total = base_cost + weight_cost + distance_cost
        minimum = float(self.shipping_company.minimum_price or 0)
        
        return max(total, minimum)
    
    def __repr__(self):
        return f'<Shipment {self.tracking_code}>'


class ShipmentTracking(db.Model):
    __tablename__ = 'shipment_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id'), nullable=False)
    status = db.Column(db.Enum(ShipmentStatus), nullable=False)
    location = db.Column(db.String(200))
    description = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Informações adicionais
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    temperature = db.Column(db.Numeric(5, 2))  # Para cargas sensíveis
    humidity = db.Column(db.Numeric(5, 2))
    
    # Quem registrou o evento
    registered_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    registered_by = db.relationship('User')
    
    shipment = db.relationship('Shipment', backref='tracking_events')
    
    def __repr__(self):
        return f'<ShipmentTracking {self.shipment_id} - {self.status.value}>'


class VehicleType(enum.Enum):
    MOTO = 'Motocicleta'
    CARRO = 'Carro'
    VAN = 'Van'
    CAMINHAO_PEQUENO = 'Caminhão Pequeno'
    CAMINHAO_MEDIO = 'Caminhão Médio'
    CAMINHAO_GRANDE = 'Caminhão Grande'
    BITREM = 'Bitrem'
    CARRETA = 'Carreta'


class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(8), unique=True, nullable=False)
    vehicle_type = db.Column(db.Enum(VehicleType), nullable=False)
    brand = db.Column(db.String(50))
    model = db.Column(db.String(50))
    year = db.Column(db.Integer)
    color = db.Column(db.String(30))
    
    # Capacidades
    max_weight = db.Column(db.Numeric(10, 3))  # kg
    max_volume = db.Column(db.Numeric(10, 3))  # m³
    fuel_consumption = db.Column(db.Numeric(5, 2))  # km/l
    
    # Status e documentação
    is_active = db.Column(db.Boolean, default=True)
    license_plate_expiry = db.Column(db.Date)
    insurance_expiry = db.Column(db.Date)
    inspection_expiry = db.Column(db.Date)
    
    # Custos operacionais
    daily_cost = db.Column(db.Numeric(10, 2))
    km_cost = db.Column(db.Numeric(10, 4))
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Vehicle {self.plate}>'


class Driver(db.Model):
    __tablename__ = 'drivers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    license_number = db.Column(db.String(20), unique=True, nullable=False)
    license_category = db.Column(db.String(10), nullable=False)
    license_expiry = db.Column(db.Date, nullable=False)
    
    phone = db.Column(db.String(15))
    email = db.Column(db.String(120))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(9))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_available = db.Column(db.Boolean, default=True)
    
    # Avaliação
    rating = db.Column(db.Numeric(3, 2))  # 0.00 a 5.00
    total_deliveries = db.Column(db.Integer, default=0)
    
    hire_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Driver {self.name}>'


# ============================================================================
# MÓDULO DE RECURSOS HUMANOS
# ============================================================================

class Department(db.Model):
    __tablename__ = 'hr_departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    manager_id = db.Column(db.Integer, db.ForeignKey('hr_employees.id'))
    budget = db.Column(db.Numeric(12, 2), default=0)
    cost_center = db.Column(db.String(50))
    
    # Relacionamentos explícitos para evitar ambiguidade
    employees = db.relationship('Employee', 
                               primaryjoin="Employee.department_id == Department.id",
                               backref=db.backref('department_rel', uselist=False),
                               lazy=True)
    manager = db.relationship('Employee', 
                             primaryjoin="Department.manager_id == Employee.id",
                             backref='managed_departments')
    
    # Auditoria
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))


class Position(db.Model):
    __tablename__ = 'hr_positions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    department_id = db.Column(db.Integer, db.ForeignKey('hr_departments.id'), nullable=False)
    level = db.Column(db.String(50))  # Junior, Pleno, Senior, etc.
    min_salary = db.Column(db.Numeric(10, 2))
    max_salary = db.Column(db.Numeric(10, 2))
    requirements = db.Column(db.Text)
    
    # Relacionamentos
    employees = db.relationship('Employee', backref='position', lazy=True)
    
    # Auditoria
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Employee(db.Model):
    __tablename__ = 'hr_employees'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_number = db.Column(db.String(20), unique=True, nullable=False)
    
    # Dados pessoais
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    birth_date = db.Column(db.Date)
    gender = db.Column(db.String(10))
    marital_status = db.Column(db.String(20))
    
    # Documentos
    cpf = db.Column(db.String(14), unique=True)
    rg = db.Column(db.String(20))
    pis_pasep = db.Column(db.String(15))
    ctps_number = db.Column(db.String(20))
    ctps_series = db.Column(db.String(10))
    
    # Endereço
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(10))
    country = db.Column(db.String(50), default='Brasil')
    
    # Dados profissionais
    department_id = db.Column(db.Integer, db.ForeignKey('hr_departments.id'))
    position_id = db.Column(db.Integer, db.ForeignKey('hr_positions.id'))
    hire_date = db.Column(db.Date, nullable=False)
    termination_date = db.Column(db.Date)
    employment_type = db.Column(db.String(20), default='CLT')  # CLT, PJ, Freelancer, etc.
    status = db.Column(db.String(20), default='active')  # active, inactive, on_leave, terminated
    
    # Salário e benefícios
    base_salary = db.Column(db.Numeric(10, 2), nullable=False)
    commission_rate = db.Column(db.Numeric(5, 4), default=0)  # Percentual
    overtime_rate = db.Column(db.Numeric(5, 2), default=1.5)  # Multiplicador
    
    # Supervisor
    supervisor_id = db.Column(db.Integer, db.ForeignKey('hr_employees.id'))
    supervisor = db.relationship('Employee', remote_side=[id], backref='subordinates')
    
    # Dados bancários
    bank_name = db.Column(db.String(100))
    bank_branch = db.Column(db.String(10))
    account_number = db.Column(db.String(20))
    account_type = db.Column(db.String(20))  # Corrente, Poupança
    
    # Relacionamentos
    attendances = db.relationship('Attendance', backref='employee', lazy=True)
    leaves = db.relationship('Leave', backref='employee', lazy=True, 
                           foreign_keys='Leave.employee_id')
    payrolls = db.relationship('Payroll', backref='employee', lazy=True)
    evaluations = db.relationship('Performance', backref='employee', lazy=True,
                                foreign_keys='Performance.employee_id')
    
    # Auditoria
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<Employee {self.employee_number}: {self.full_name}>'


class Attendance(db.Model):
    __tablename__ = 'hr_attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('hr_employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    
    # Horários
    clock_in = db.Column(db.DateTime)
    lunch_out = db.Column(db.DateTime)
    lunch_in = db.Column(db.DateTime)
    clock_out = db.Column(db.DateTime)
    
    # Horas trabalhadas
    regular_hours = db.Column(db.Numeric(4, 2), default=0)
    overtime_hours = db.Column(db.Numeric(4, 2), default=0)
    break_hours = db.Column(db.Numeric(4, 2), default=0)
    
    # Status
    is_late = db.Column(db.Boolean, default=False)
    is_absent = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    
    # Auditoria
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Leave(db.Model):
    __tablename__ = 'hr_leaves'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('hr_employees.id'), nullable=False)
    leave_type = db.Column(db.String(20), nullable=False)  # vacation, sick_leave, maternity, etc.
    
    # Datas
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    
    # Detalhes
    days_requested = db.Column(db.Integer, nullable=False)
    days_approved = db.Column(db.Integer)
    reason = db.Column(db.Text)
    medical_certificate = db.Column(db.Boolean, default=False)
    
    # Aprovação
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    approved_by = db.Column(db.Integer, db.ForeignKey('hr_employees.id'))
    approved_at = db.Column(db.DateTime)
    approval_notes = db.Column(db.Text)
    
    # Relacionamentos
    approver = db.relationship('Employee', foreign_keys=[approved_by], backref='leaves_approved')
    
    # Auditoria
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Payroll(db.Model):
    __tablename__ = 'hr_payroll'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('hr_employees.id'), nullable=False)
    
    # Período
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    pay_date = db.Column(db.Date)
    
    # Valores base
    base_salary = db.Column(db.Numeric(10, 2), nullable=False)
    hours_worked = db.Column(db.Numeric(6, 2), default=0)
    overtime_hours = db.Column(db.Numeric(6, 2), default=0)
    
    # Proventos
    salary_amount = db.Column(db.Numeric(10, 2), default=0)
    overtime_amount = db.Column(db.Numeric(10, 2), default=0)
    commission_amount = db.Column(db.Numeric(10, 2), default=0)
    bonus_amount = db.Column(db.Numeric(10, 2), default=0)
    vacation_amount = db.Column(db.Numeric(10, 2), default=0)
    thirteenth_salary = db.Column(db.Numeric(10, 2), default=0)
    
    # Descontos
    inss_discount = db.Column(db.Numeric(10, 2), default=0)
    irrf_discount = db.Column(db.Numeric(10, 2), default=0)
    fgts_discount = db.Column(db.Numeric(10, 2), default=0)
    health_insurance = db.Column(db.Numeric(10, 2), default=0)
    dental_insurance = db.Column(db.Numeric(10, 2), default=0)
    meal_voucher_discount = db.Column(db.Numeric(10, 2), default=0)
    transport_voucher_discount = db.Column(db.Numeric(10, 2), default=0)
    other_discounts = db.Column(db.Numeric(10, 2), default=0)
    
    # Benefícios
    meal_voucher = db.Column(db.Numeric(10, 2), default=0)
    transport_voucher = db.Column(db.Numeric(10, 2), default=0)
    family_allowance = db.Column(db.Numeric(10, 2), default=0)
    other_benefits = db.Column(db.Numeric(10, 2), default=0)
    
    # Totais
    gross_salary = db.Column(db.Numeric(10, 2), nullable=False)
    total_discounts = db.Column(db.Numeric(10, 2), nullable=False)
    net_salary = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='draft')  # draft, approved, paid
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    
    # Auditoria
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))


class Performance(db.Model):
    __tablename__ = 'hr_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('hr_employees.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('hr_employees.id'), nullable=False)
    
    # Período da avaliação
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    evaluation_date = db.Column(db.Date, nullable=False)
    
    # Critérios de avaliação (escala 1-5)
    productivity_score = db.Column(db.Integer)
    quality_score = db.Column(db.Integer)
    teamwork_score = db.Column(db.Integer)
    communication_score = db.Column(db.Integer)
    leadership_score = db.Column(db.Integer)
    innovation_score = db.Column(db.Integer)
    punctuality_score = db.Column(db.Integer)
    
    # Comentários
    strengths = db.Column(db.Text)
    areas_for_improvement = db.Column(db.Text)
    goals_next_period = db.Column(db.Text)
    employee_comments = db.Column(db.Text)
    evaluator_comments = db.Column(db.Text)
    
    # Score geral
    overall_score = db.Column(db.Numeric(3, 2))  # Média ponderada
    recommendation = db.Column(db.String(50))  # promotion, raise, training, etc.
    
    # Status
    status = db.Column(db.String(20), default='draft')  # draft, completed, reviewed
    
    # Relacionamentos
    evaluator = db.relationship('Employee', foreign_keys=[evaluator_id], backref='evaluations_given')
    
    # Auditoria
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
