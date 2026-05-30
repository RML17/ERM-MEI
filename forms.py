from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (
    StringField, PasswordField, BooleanField, SelectField, TextAreaField,
    DecimalField, IntegerField, DateField, FormField, FieldList, Form,
    MultipleFileField, HiddenField, SubmitField
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, Optional, 
    ValidationError, NumberRange
)
from datetime import date

from models import (
    UserRole, InvoiceType, InvoiceStatus, PaymentMethod, PaymentStatus,
    ShippingCompanyType, RouteType, ShipmentStatus, VehicleType,
    User, Customer, Supplier, Product
)


class LoginForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')


class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    full_name = StringField('Nome Completo', validators=[DataRequired(), Length(max=100)])
    role = SelectField('Função', choices=[(role.name, role.value) for role in UserRole])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Senha Atual', validators=[DataRequired()])
    new_password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=8)])
    confirm_new_password = PasswordField('Confirmar Nova Senha', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Alterar Senha')


class InvoiceItemForm(Form):
    product_id = SelectField('Produto', coerce=int, validators=[DataRequired()])
    quantity = DecimalField('Quantidade', places=3, validators=[DataRequired(), NumberRange(min=0.001)])
    unit_price = DecimalField('Preço Unitário', places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    discount = DecimalField('Desconto', places=2, default=0.0, validators=[Optional(), NumberRange(min=0.0)])
    cfop = StringField('CFOP', validators=[Optional(), Length(max=4)])


class InvoiceForm(FlaskForm):
    invoice_number = StringField('Número da Nota', validators=[DataRequired(), Length(max=20)])
    series = StringField('Série', validators=[DataRequired(), Length(max=3)])
    type = SelectField('Tipo', choices=[(t.name, t.value) for t in InvoiceType], validators=[DataRequired()])
    status = SelectField('Status', choices=[(s.name, s.value) for s in InvoiceStatus], validators=[DataRequired()])
    issue_date = DateField('Data de Emissão', validators=[DataRequired()], default=date.today)
    operation_date = DateField('Data de Operação', validators=[DataRequired()], default=date.today)
    entity_id = SelectField('Cliente/Fornecedor', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Observações', validators=[Optional()])
    items = FieldList(FormField(InvoiceItemForm), min_entries=1)
    submit = SubmitField('Salvar Nota Fiscal')
    
    def populate_select_fields(self):
        """Preenche as opções dos campos de seleção com dados do banco"""
        # Preencher produtos para os itens
        products = Product.query.order_by(Product.name).all()
        product_choices = [(p.id, f"{p.name} - {p.sku}") for p in products]
        
        # Aplicar as escolhas para todos os itens
        for item_form in self.items:
            item_form.product_id.choices = product_choices
        
        # Dependendo do tipo de nota, mostrar clientes ou fornecedores
        if self.type.data == InvoiceType.OUTBOUND.name:
            customers = Customer.query.order_by(Customer.name).all()
            self.entity_id.choices = [(c.id, c.name) for c in customers]
            self.entity_id.label.text = 'Cliente'
        else:
            suppliers = Supplier.query.order_by(Supplier.name).all()
            self.entity_id.choices = [(s.id, s.name) for s in suppliers]
            self.entity_id.label.text = 'Fornecedor'


class InvoiceSearchForm(FlaskForm):
    invoice_number = StringField('Número da Nota', validators=[Optional()])
    type = SelectField('Tipo', choices=[('', 'Todos')] + [(t.name, t.value) for t in InvoiceType], validators=[Optional()])
    status = SelectField('Status', choices=[('', 'Todos')] + [(s.name, s.value) for s in InvoiceStatus], validators=[Optional()])
    start_date = DateField('Data Inicial', validators=[Optional()])
    end_date = DateField('Data Final', validators=[Optional()])
    submit = SubmitField('Buscar')


class UploadXMLForm(FlaskForm):
    xml_file = FileField('Arquivo XML', validators=[
        FileRequired(),
        FileAllowed(['xml'], 'Apenas arquivos XML são permitidos')
    ])
    invoice_type = SelectField('Tipo de Nota', choices=[(t.name, t.value) for t in InvoiceType], validators=[DataRequired()])
    submit = SubmitField('Importar XML')


class CustomerForm(FlaskForm):
    name = StringField('Nome/Razão Social', validators=[DataRequired(), Length(max=100)])
    document_type = SelectField('Tipo de Documento', choices=[('CPF', 'CPF'), ('CNPJ', 'CNPJ')], validators=[DataRequired()])
    document = StringField('CPF/CNPJ', validators=[DataRequired(), Length(max=18)])
    state_registration = StringField('Inscrição Estadual', validators=[Optional(), Length(max=20)])
    address = StringField('Endereço', validators=[Optional(), Length(max=200)])
    city = StringField('Cidade', validators=[Optional(), Length(max=100)])
    state = StringField('UF', validators=[Optional(), Length(max=2)])
    zip_code = StringField('CEP', validators=[Optional(), Length(max=9)])
    phone = StringField('Telefone', validators=[Optional(), Length(max=15)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    submit = SubmitField('Cadastrar Cliente')


class SupplierForm(FlaskForm):
    name = StringField('Razão Social', validators=[DataRequired(), Length(max=100)])
    cnpj = StringField('CNPJ', validators=[DataRequired(), Length(max=18)])
    state_registration = StringField('Inscrição Estadual', validators=[Optional(), Length(max=20)])
    address = StringField('Endereço', validators=[Optional(), Length(max=200)])
    city = StringField('Cidade', validators=[Optional(), Length(max=100)])
    state = StringField('UF', validators=[Optional(), Length(max=2)])
    zip_code = StringField('CEP', validators=[Optional(), Length(max=9)])
    phone = StringField('Telefone', validators=[Optional(), Length(max=15)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    contact_name = StringField('Nome do Contato', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Cadastrar Fornecedor')


class ProductForm(FlaskForm):
    sku = StringField('SKU', validators=[DataRequired(), Length(max=20)])
    name = StringField('Nome do Produto', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descrição', validators=[Optional()])
    purchase_price = DecimalField('Preço de Compra', places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    sale_price = DecimalField('Preço de Venda', places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    min_stock = IntegerField('Estoque Mínimo', default=0, validators=[Optional(), NumberRange(min=0)])
    ncm = StringField('NCM', validators=[Optional(), Length(max=8)])
    weight = DecimalField('Peso (kg)', places=3, validators=[Optional(), NumberRange(min=0.001)])
    submit = SubmitField('Salvar Produto')


class ProductSearchForm(FlaskForm):
    sku = StringField('SKU', validators=[Optional()])
    name = StringField('Nome do Produto', validators=[Optional()])
    submit = SubmitField('Buscar')


class InventoryMovementForm(FlaskForm):
    product_id = SelectField('Produto', coerce=int, validators=[DataRequired()])
    movement_type = SelectField('Tipo de Movimento', choices=[('entrada', 'Entrada'), ('saída', 'Saída')], validators=[DataRequired()])
    quantity = DecimalField('Quantidade', places=3, validators=[DataRequired(), NumberRange(min=0.001)])
    unit_cost = DecimalField('Custo Unitário', places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    notes = TextAreaField('Observações', validators=[Optional()])
    submit = SubmitField('Registrar Movimento')


class PaymentForm(FlaskForm):
    invoice_id = SelectField('Nota Fiscal', coerce=int, validators=[Optional()])
    payment_method = SelectField('Método de Pagamento', choices=[(m.name, m.value) for m in PaymentMethod], validators=[DataRequired()])
    due_date = DateField('Data de Vencimento', validators=[DataRequired()], default=date.today)
    amount = DecimalField('Valor', places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    document_number = StringField('Número do Documento', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Observações', validators=[Optional()])
    submit = SubmitField('Registrar Pagamento')


class PaymentSearchForm(FlaskForm):
    invoice_number = StringField('Número da Nota', validators=[Optional()])
    payment_method = SelectField('Método de Pagamento', choices=[('', 'Todos')] + [(m.name, m.value) for m in PaymentMethod], validators=[Optional()])
    status = SelectField('Status', choices=[('', 'Todos')] + [(s.name, s.value) for s in PaymentStatus], validators=[Optional()])
    start_due_date = DateField('Vencimento Inicial', validators=[Optional()])
    end_due_date = DateField('Vencimento Final', validators=[Optional()])
    submit = SubmitField('Buscar')


class ReportForm(FlaskForm):
    report_type = SelectField('Tipo de Relatório', choices=[
        ('invoices', 'Notas Fiscais'),
        ('users', 'Usuários'),
        ('inventory', 'Estoque'),
        ('financial', 'Financeiro')
    ], validators=[DataRequired()])
    format_type = SelectField('Formato', choices=[
        ('excel', 'Excel'),
        ('word', 'Word')
    ], validators=[DataRequired()])
    start_date = DateField('Data Inicial', validators=[Optional()], default=date.today)
    end_date = DateField('Data Final', validators=[Optional()], default=date.today)
    invoice_type = SelectField('Tipo de Nota', choices=[('', 'Todos')] + [(t.name, t.value) for t in InvoiceType], validators=[Optional()])
    invoice_status = SelectField('Status da Nota', choices=[('', 'Todos')] + [(s.name, s.value) for s in InvoiceStatus], validators=[Optional()])
    include_items = BooleanField('Incluir Itens', default=False)
    submit = SubmitField('Gerar Relatório')


class UserSearchForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[Optional()])
    email = StringField('Email', validators=[Optional()])
    role = SelectField('Função', choices=[('', 'Todas')] + [(role.name, role.value) for role in UserRole], validators=[Optional()])
    submit = SubmitField('Buscar')


# =============================================
# FORMULÁRIOS DO MÓDULO LOGÍSTICO
# =============================================

class ShippingCompanyForm(FlaskForm):
    name = StringField('Nome da Empresa', validators=[DataRequired(), Length(max=100)])
    cnpj = StringField('CNPJ', validators=[Optional(), Length(max=18)])
    company_type = SelectField('Tipo de Empresa', choices=[(t.name, t.value) for t in ShippingCompanyType], validators=[DataRequired()])
    contact_name = StringField('Nome do Contato', validators=[Optional(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    phone = StringField('Telefone', validators=[Optional(), Length(max=15)])
    address = StringField('Endereço', validators=[Optional(), Length(max=200)])
    city = StringField('Cidade', validators=[Optional(), Length(max=100)])
    state = StringField('UF', validators=[Optional(), Length(max=2)])
    zip_code = StringField('CEP', validators=[Optional(), Length(max=9)])
    
    # Configurações de serviço
    delivery_time_min = IntegerField('Prazo Mínimo (dias úteis)', validators=[Optional(), NumberRange(min=1)])
    delivery_time_max = IntegerField('Prazo Máximo (dias úteis)', validators=[Optional(), NumberRange(min=1)])
    weight_limit = DecimalField('Limite de Peso (kg)', places=3, validators=[Optional(), NumberRange(min=0.001)])
    volume_limit = DecimalField('Limite de Volume (m³)', places=3, validators=[Optional(), NumberRange(min=0.001)])
    
    # Preços
    price_per_kg = DecimalField('Preço por Kg', places=2, validators=[Optional(), NumberRange(min=0.01)])
    price_per_km = DecimalField('Preço por Km', places=2, validators=[Optional(), NumberRange(min=0.01)])
    minimum_price = DecimalField('Preço Mínimo', places=2, validators=[Optional(), NumberRange(min=0.01)])
    
    # Configurações
    api_token = StringField('Token da API', validators=[Optional(), Length(max=255)])
    tracking_url = StringField('URL de Rastreamento', validators=[Optional(), Length(max=255)])
    notes = TextAreaField('Observações', validators=[Optional()])
    
    submit = SubmitField('Salvar Transportadora')


class RouteForm(FlaskForm):
    name = StringField('Nome da Rota', validators=[DataRequired(), Length(max=100)])
    origin_zip = StringField('CEP Origem', validators=[DataRequired(), Length(max=9)])
    destination_zip = StringField('CEP Destino', validators=[DataRequired(), Length(max=9)])
    origin_city = StringField('Cidade Origem', validators=[Optional(), Length(max=100)])
    origin_state = StringField('UF Origem', validators=[Optional(), Length(max=2)])
    destination_city = StringField('Cidade Destino', validators=[Optional(), Length(max=100)])
    destination_state = StringField('UF Destino', validators=[Optional(), Length(max=2)])
    
    distance_km = DecimalField('Distância (km)', places=2, validators=[Optional(), NumberRange(min=0.01)])
    estimated_time_hours = DecimalField('Tempo Estimado (horas)', places=2, validators=[Optional(), NumberRange(min=0.01)])
    route_type = SelectField('Tipo de Rota', choices=[(t.name, t.value) for t in RouteType], validators=[DataRequired()])
    
    # Custos
    base_cost = DecimalField('Custo Base', places=2, validators=[Optional(), NumberRange(min=0.01)])
    fuel_cost_per_km = DecimalField('Custo Combustível por Km', places=4, validators=[Optional(), NumberRange(min=0.0001)])
    toll_cost = DecimalField('Custo Pedágio', places=2, validators=[Optional(), NumberRange(min=0.01)])
    
    notes = TextAreaField('Observações', validators=[Optional()])
    submit = SubmitField('Salvar Rota')


class ShipmentForm(FlaskForm):
    invoice_id = SelectField('Nota Fiscal', coerce=int, validators=[Optional()])
    shipping_company_id = SelectField('Transportadora', coerce=int, validators=[DataRequired()])
    route_id = SelectField('Rota', coerce=int, validators=[Optional()])
    
    # Remetente
    sender_name = StringField('Nome do Remetente', validators=[DataRequired(), Length(max=100)])
    sender_address = StringField('Endereço do Remetente', validators=[DataRequired(), Length(max=200)])
    sender_city = StringField('Cidade do Remetente', validators=[DataRequired(), Length(max=100)])
    sender_state = StringField('UF do Remetente', validators=[DataRequired(), Length(max=2)])
    sender_zip = StringField('CEP do Remetente', validators=[DataRequired(), Length(max=9)])
    sender_phone = StringField('Telefone do Remetente', validators=[Optional(), Length(max=15)])
    
    # Destinatário
    recipient_name = StringField('Nome do Destinatário', validators=[DataRequired(), Length(max=100)])
    recipient_address = StringField('Endereço do Destinatário', validators=[DataRequired(), Length(max=200)])
    recipient_city = StringField('Cidade do Destinatário', validators=[DataRequired(), Length(max=100)])
    recipient_state = StringField('UF do Destinatário', validators=[DataRequired(), Length(max=2)])
    recipient_zip = StringField('CEP do Destinatário', validators=[DataRequired(), Length(max=9)])
    recipient_phone = StringField('Telefone do Destinatário', validators=[Optional(), Length(max=15)])
    recipient_email = StringField('Email do Destinatário', validators=[Optional(), Email(), Length(max=120)])
    
    # Carga
    total_weight = DecimalField('Peso Total (kg)', places=3, validators=[DataRequired(), NumberRange(min=0.001)])
    total_volume = DecimalField('Volume Total (m³)', places=3, validators=[Optional(), NumberRange(min=0.001)])
    declared_value = DecimalField('Valor Declarado', places=2, validators=[Optional(), NumberRange(min=0.01)])
    package_count = IntegerField('Quantidade de Volumes', default=1, validators=[DataRequired(), NumberRange(min=1)])
    
    # Instruções e observações
    delivery_instructions = TextAreaField('Instruções de Entrega', validators=[Optional()])
    notes = TextAreaField('Observações', validators=[Optional()])
    
    submit = SubmitField('Criar Envio')
    
    def populate_select_fields(self):
        """Preenche as opções dos campos de seleção com dados do banco"""
        from models import Invoice, ShippingCompany, Route
        
        # Notas fiscais
        invoices = Invoice.query.filter_by(type=InvoiceType.OUTBOUND).all()
        self.invoice_id.choices = [('', 'Selecione uma nota fiscal')] + [(i.id, f'NF {i.invoice_number} - {i.entity.name}') for i in invoices]
        
        # Transportadoras
        companies = ShippingCompany.query.filter_by(is_active=True).all()
        self.shipping_company_id.choices = [('', 'Selecione uma transportadora')] + [(c.id, c.name) for c in companies]
        
        # Rotas
        routes = Route.query.filter_by(is_active=True).all()
        self.route_id.choices = [('', 'Selecione uma rota')] + [(r.id, r.name) for r in routes]


class ShipmentSearchForm(FlaskForm):
    tracking_code = StringField('Código de Rastreamento', validators=[Optional()])
    status = SelectField('Status', choices=[('', 'Todos')] + [(s.name, s.value) for s in ShipmentStatus], validators=[Optional()])
    shipping_company_id = SelectField('Transportadora', validators=[Optional()])
    start_date = DateField('Data Inicial', validators=[Optional()])
    end_date = DateField('Data Final', validators=[Optional()])
    recipient_name = StringField('Nome do Destinatário', validators=[Optional()])
    submit = SubmitField('Buscar')
    
    def populate_select_fields(self):
        """Preenche as opções dos campos de seleção com dados do banco"""
        from models import ShippingCompany
        
        companies = ShippingCompany.query.filter_by(is_active=True).all()
        self.shipping_company_id.choices = [('', 'Todas')] + [(str(c.id), c.name) for c in companies]


class TrackingForm(FlaskForm):
    status = SelectField('Status', choices=[(s.name, s.value) for s in ShipmentStatus], validators=[DataRequired()])
    location = StringField('Localização', validators=[Optional(), Length(max=200)])
    description = StringField('Descrição', validators=[DataRequired(), Length(max=500)])
    latitude = DecimalField('Latitude', places=8, validators=[Optional()])
    longitude = DecimalField('Longitude', places=8, validators=[Optional()])
    temperature = DecimalField('Temperatura (°C)', places=2, validators=[Optional()])
    humidity = DecimalField('Umidade (%)', places=2, validators=[Optional()])
    submit = SubmitField('Registrar Evento')


class VehicleForm(FlaskForm):
    plate = StringField('Placa', validators=[DataRequired(), Length(max=8)])
    vehicle_type = SelectField('Tipo de Veículo', choices=[(t.name, t.value) for t in VehicleType], validators=[DataRequired()])
    brand = StringField('Marca', validators=[Optional(), Length(max=50)])
    model = StringField('Modelo', validators=[Optional(), Length(max=50)])
    year = IntegerField('Ano', validators=[Optional(), NumberRange(min=1900, max=2030)])
    color = StringField('Cor', validators=[Optional(), Length(max=30)])
    
    # Capacidades
    max_weight = DecimalField('Peso Máximo (kg)', places=3, validators=[Optional(), NumberRange(min=0.001)])
    max_volume = DecimalField('Volume Máximo (m³)', places=3, validators=[Optional(), NumberRange(min=0.001)])
    fuel_consumption = DecimalField('Consumo (km/l)', places=2, validators=[Optional(), NumberRange(min=0.1)])
    
    # Documentação
    license_plate_expiry = DateField('Vencimento da Licença', validators=[Optional()])
    insurance_expiry = DateField('Vencimento do Seguro', validators=[Optional()])
    inspection_expiry = DateField('Vencimento da Vistoria', validators=[Optional()])
    
    # Custos
    daily_cost = DecimalField('Custo Diário', places=2, validators=[Optional(), NumberRange(min=0.01)])
    km_cost = DecimalField('Custo por Km', places=4, validators=[Optional(), NumberRange(min=0.0001)])
    
    notes = TextAreaField('Observações', validators=[Optional()])
    submit = SubmitField('Salvar Veículo')


class DriverForm(FlaskForm):
    name = StringField('Nome Completo', validators=[DataRequired(), Length(max=100)])
    cpf = StringField('CPF', validators=[DataRequired(), Length(max=14)])
    license_number = StringField('Número da CNH', validators=[DataRequired(), Length(max=20)])
    license_category = StringField('Categoria da CNH', validators=[DataRequired(), Length(max=10)])
    license_expiry = DateField('Vencimento da CNH', validators=[DataRequired()])
    
    phone = StringField('Telefone', validators=[Optional(), Length(max=15)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    address = StringField('Endereço', validators=[Optional(), Length(max=200)])
    city = StringField('Cidade', validators=[Optional(), Length(max=100)])
    state = StringField('UF', validators=[Optional(), Length(max=2)])
    zip_code = StringField('CEP', validators=[Optional(), Length(max=9)])
    
    hire_date = DateField('Data de Contratação', validators=[Optional()])
    notes = TextAreaField('Observações', validators=[Optional()])
    
    submit = SubmitField('Salvar Motorista')
