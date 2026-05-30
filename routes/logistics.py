from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models import (
    ShippingCompany, Route, Shipment, ShipmentTracking, Vehicle, Driver,
    ShippingCompanyType, RouteType, ShipmentStatus, VehicleType
)
from forms import (
    ShippingCompanyForm, RouteForm, ShipmentForm, ShipmentSearchForm,
    TrackingForm, VehicleForm, DriverForm
)
from datetime import datetime, timedelta
import uuid
from sqlalchemy import func

logistics_bp = Blueprint('logistics', __name__, url_prefix='/logistics')


# =============================================
# DASHBOARD LOGÍSTICO
# =============================================

@logistics_bp.route('/')
@login_required
def index():
    """Dashboard principal do módulo logístico"""
    
    # Métricas principais
    total_shipments = Shipment.query.count()
    pending_shipments = Shipment.query.filter_by(status=ShipmentStatus.PENDING).count()
    in_transit_shipments = Shipment.query.filter_by(status=ShipmentStatus.IN_TRANSIT).count()
    delivered_shipments = Shipment.query.filter_by(status=ShipmentStatus.DELIVERED).count()
    
    # Envios recentes
    recent_shipments = Shipment.query.order_by(Shipment.created_date.desc()).limit(10).all()
    
    # Transportadoras ativas
    active_companies = ShippingCompany.query.filter_by(is_active=True).count()
    
    # Veículos ativos
    active_vehicles = Vehicle.query.filter_by(is_active=True).count()
    
    # Motoristas disponíveis
    available_drivers = Driver.query.filter_by(is_active=True, is_available=True).count()
    
    # Envios por status (para gráfico)
    status_data = db.session.query(
        Shipment.status,
        func.count(Shipment.id)
    ).group_by(Shipment.status).all()
    
    # Preparar dados para o gráfico
    status_chart = {
        'labels': [status.value for status, count in status_data],
        'data': [count for status, count in status_data]
    }
    
    return render_template('logistics/dashboard.html',
                         total_shipments=total_shipments,
                         pending_shipments=pending_shipments,
                         in_transit_shipments=in_transit_shipments,
                         delivered_shipments=delivered_shipments,
                         recent_shipments=recent_shipments,
                         active_companies=active_companies,
                         active_vehicles=active_vehicles,
                         available_drivers=available_drivers,
                         status_chart=status_chart)


# =============================================
# TRANSPORTADORAS
# =============================================

@logistics_bp.route('/companies')
@login_required
def companies():
    """Lista de transportadoras"""
    companies = ShippingCompany.query.order_by(ShippingCompany.name).all()
    return render_template('logistics/companies/list.html', companies=companies)


@logistics_bp.route('/companies/create', methods=['GET', 'POST'])
@login_required
def create_company():
    """Criar nova transportadora"""
    form = ShippingCompanyForm()
    
    if form.validate_on_submit():
        company = ShippingCompany(
            name=form.name.data,
            cnpj=form.cnpj.data,
            company_type=ShippingCompanyType[form.company_type.data],
            contact_name=form.contact_name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            zip_code=form.zip_code.data,
            delivery_time_min=form.delivery_time_min.data,
            delivery_time_max=form.delivery_time_max.data,
            weight_limit=form.weight_limit.data,
            volume_limit=form.volume_limit.data,
            price_per_kg=form.price_per_kg.data,
            price_per_km=form.price_per_km.data,
            minimum_price=form.minimum_price.data,
            api_token=form.api_token.data,
            tracking_url=form.tracking_url.data,
            notes=form.notes.data
        )
        
        db.session.add(company)
        db.session.commit()
        
        flash('Transportadora cadastrada com sucesso!', 'success')
        return redirect(url_for('logistics.companies'))
    
    return render_template('logistics/companies/form.html', form=form, title='Nova Transportadora')


@logistics_bp.route('/companies/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_company(id):
    """Editar transportadora"""
    company = ShippingCompany.query.get_or_404(id)
    form = ShippingCompanyForm(obj=company)
    
    if form.validate_on_submit():
        company.name = form.name.data
        company.cnpj = form.cnpj.data
        company.company_type = ShippingCompanyType[form.company_type.data]
        company.contact_name = form.contact_name.data
        company.email = form.email.data
        company.phone = form.phone.data
        company.address = form.address.data
        company.city = form.city.data
        company.state = form.state.data
        company.zip_code = form.zip_code.data
        company.delivery_time_min = form.delivery_time_min.data
        company.delivery_time_max = form.delivery_time_max.data
        company.weight_limit = form.weight_limit.data
        company.volume_limit = form.volume_limit.data
        company.price_per_kg = form.price_per_kg.data
        company.price_per_km = form.price_per_km.data
        company.minimum_price = form.minimum_price.data
        company.api_token = form.api_token.data
        company.tracking_url = form.tracking_url.data
        company.notes = form.notes.data
        company.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Transportadora atualizada com sucesso!', 'success')
        return redirect(url_for('logistics.companies'))
    
    return render_template('logistics/companies/form.html', form=form, company=company, title='Editar Transportadora')


# =============================================
# ROTAS
# =============================================

@logistics_bp.route('/routes')
@login_required
def routes():
    """Lista de rotas"""
    routes = Route.query.order_by(Route.name).all()
    return render_template('logistics/routes/list.html', routes=routes)


@logistics_bp.route('/routes/create', methods=['GET', 'POST'])
@login_required
def create_route():
    """Criar nova rota"""
    form = RouteForm()
    
    if form.validate_on_submit():
        route = Route(
            name=form.name.data,
            origin_zip=form.origin_zip.data,
            destination_zip=form.destination_zip.data,
            origin_city=form.origin_city.data,
            origin_state=form.origin_state.data,
            destination_city=form.destination_city.data,
            destination_state=form.destination_state.data,
            distance_km=form.distance_km.data,
            estimated_time_hours=form.estimated_time_hours.data,
            route_type=RouteType[form.route_type.data],
            base_cost=form.base_cost.data,
            fuel_cost_per_km=form.fuel_cost_per_km.data,
            toll_cost=form.toll_cost.data,
            notes=form.notes.data
        )
        
        db.session.add(route)
        db.session.commit()
        
        flash('Rota cadastrada com sucesso!', 'success')
        return redirect(url_for('logistics.routes'))
    
    return render_template('logistics/routes/form.html', form=form, title='Nova Rota')


@logistics_bp.route('/routes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_route(id):
    """Editar rota"""
    route = Route.query.get_or_404(id)
    form = RouteForm(obj=route)
    
    if form.validate_on_submit():
        route.name = form.name.data
        route.origin_zip = form.origin_zip.data
        route.destination_zip = form.destination_zip.data
        route.origin_city = form.origin_city.data
        route.origin_state = form.origin_state.data
        route.destination_city = form.destination_city.data
        route.destination_state = form.destination_state.data
        route.distance_km = form.distance_km.data
        route.estimated_time_hours = form.estimated_time_hours.data
        route.route_type = RouteType[form.route_type.data]
        route.base_cost = form.base_cost.data
        route.fuel_cost_per_km = form.fuel_cost_per_km.data
        route.toll_cost = form.toll_cost.data
        route.notes = form.notes.data
        route.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Rota atualizada com sucesso!', 'success')
        return redirect(url_for('logistics.routes'))
    
    return render_template('logistics/routes/form.html', form=form, route=route, title='Editar Rota')


# =============================================
# ENVIOS
# =============================================

@logistics_bp.route('/shipments', methods=['GET', 'POST'])
@login_required
def shipments():
    """Lista de envios com filtros"""
    form = ShipmentSearchForm()
    form.populate_select_fields()
    
    query = Shipment.query
    
    # Aplicar filtros se o formulário foi submetido
    if request.method == 'POST' and form.validate_on_submit():
        if form.tracking_code.data:
            query = query.filter(Shipment.tracking_code.ilike(f'%{form.tracking_code.data}%'))
        
        if form.status.data:
            query = query.filter(Shipment.status == ShipmentStatus[form.status.data])
        
        if form.shipping_company_id.data and form.shipping_company_id.data != '':
            query = query.filter(Shipment.shipping_company_id == int(form.shipping_company_id.data))
        
        if form.start_date.data:
            query = query.filter(Shipment.created_date >= form.start_date.data)
        
        if form.end_date.data:
            end_date = datetime.combine(form.end_date.data, datetime.max.time())
            query = query.filter(Shipment.created_date <= end_date)
        
        if form.recipient_name.data:
            query = query.filter(Shipment.recipient_name.ilike(f'%{form.recipient_name.data}%'))
    
    shipments = query.order_by(Shipment.created_date.desc()).all()
    
    return render_template('logistics/shipments/list.html', shipments=shipments, form=form)


@logistics_bp.route('/shipments/create', methods=['GET', 'POST'])
@login_required
def create_shipment():
    """Criar novo envio"""
    form = ShipmentForm()
    form.populate_select_fields()
    
    if form.validate_on_submit():
        # Gerar código de rastreamento único
        tracking_code = f'ENV{datetime.now().strftime("%Y%m%d")}{str(uuid.uuid4())[:8].upper()}'
        
        shipment = Shipment(
            tracking_code=tracking_code,
            invoice_id=form.invoice_id.data if form.invoice_id.data else None,
            shipping_company_id=form.shipping_company_id.data,
            route_id=form.route_id.data if form.route_id.data else None,
            sender_name=form.sender_name.data,
            sender_address=form.sender_address.data,
            sender_city=form.sender_city.data,
            sender_state=form.sender_state.data,
            sender_zip=form.sender_zip.data,
            sender_phone=form.sender_phone.data,
            recipient_name=form.recipient_name.data,
            recipient_address=form.recipient_address.data,
            recipient_city=form.recipient_city.data,
            recipient_state=form.recipient_state.data,
            recipient_zip=form.recipient_zip.data,
            recipient_phone=form.recipient_phone.data,
            recipient_email=form.recipient_email.data,
            total_weight=form.total_weight.data,
            total_volume=form.total_volume.data,
            declared_value=form.declared_value.data,
            package_count=form.package_count.data,
            delivery_instructions=form.delivery_instructions.data,
            notes=form.notes.data,
            created_by_id=current_user.id
        )
        
        # Calcular frete automaticamente se há rota e transportadora
        if shipment.route and shipment.shipping_company:
            shipment.freight_cost = shipment.calculate_freight()
            shipment.total_cost = shipment.freight_cost
        
        db.session.add(shipment)
        db.session.commit()
        
        # Criar primeiro evento de tracking
        tracking_event = ShipmentTracking(
            shipment_id=shipment.id,
            status=ShipmentStatus.PENDING,
            description='Envio criado no sistema',
            registered_by_id=current_user.id
        )
        db.session.add(tracking_event)
        db.session.commit()
        
        flash('Envio criado com sucesso!', 'success')
        return redirect(url_for('logistics.view_shipment', id=shipment.id))
    
    return render_template('logistics/shipments/form.html', form=form, title='Novo Envio')


@logistics_bp.route('/shipments/<int:id>')
@login_required
def view_shipment(id):
    """Visualizar detalhes do envio"""
    shipment = Shipment.query.get_or_404(id)
    tracking_events = ShipmentTracking.query.filter_by(shipment_id=id).order_by(ShipmentTracking.timestamp.desc()).all()
    
    return render_template('logistics/shipments/view.html', shipment=shipment, tracking_events=tracking_events)


@logistics_bp.route('/shipments/<int:id>/track', methods=['GET', 'POST'])
@login_required
def track_shipment(id):
    """Adicionar evento de rastreamento"""
    shipment = Shipment.query.get_or_404(id)
    form = TrackingForm()
    
    if form.validate_on_submit():
        tracking_event = ShipmentTracking(
            shipment_id=shipment.id,
            status=ShipmentStatus[form.status.data],
            location=form.location.data,
            description=form.description.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            temperature=form.temperature.data,
            humidity=form.humidity.data,
            registered_by_id=current_user.id
        )
        
        # Atualizar status do envio
        shipment.status = ShipmentStatus[form.status.data]
        
        # Se foi entregue, registrar data de entrega
        if shipment.status == ShipmentStatus.DELIVERED:
            shipment.delivered_date = datetime.utcnow()
        
        db.session.add(tracking_event)
        db.session.commit()
        
        flash('Evento de rastreamento adicionado!', 'success')
        return redirect(url_for('logistics.view_shipment', id=shipment.id))
    
    return render_template('logistics/shipments/track.html', shipment=shipment, form=form)


# =============================================
# VEÍCULOS
# =============================================

@logistics_bp.route('/vehicles')
@login_required
def vehicles():
    """Lista de veículos"""
    vehicles = Vehicle.query.order_by(Vehicle.plate).all()
    return render_template('logistics/vehicles/list.html', vehicles=vehicles)


@logistics_bp.route('/vehicles/create', methods=['GET', 'POST'])
@login_required
def create_vehicle():
    """Criar novo veículo"""
    form = VehicleForm()
    
    if form.validate_on_submit():
        vehicle = Vehicle(
            plate=form.plate.data,
            vehicle_type=VehicleType[form.vehicle_type.data],
            brand=form.brand.data,
            model=form.model.data,
            year=form.year.data,
            color=form.color.data,
            max_weight=form.max_weight.data,
            max_volume=form.max_volume.data,
            fuel_consumption=form.fuel_consumption.data,
            license_plate_expiry=form.license_plate_expiry.data,
            insurance_expiry=form.insurance_expiry.data,
            inspection_expiry=form.inspection_expiry.data,
            daily_cost=form.daily_cost.data,
            km_cost=form.km_cost.data,
            notes=form.notes.data
        )
        
        db.session.add(vehicle)
        db.session.commit()
        
        flash('Veículo cadastrado com sucesso!', 'success')
        return redirect(url_for('logistics.vehicles'))
    
    return render_template('logistics/vehicles/form.html', form=form, title='Novo Veículo')


# =============================================
# MOTORISTAS
# =============================================

@logistics_bp.route('/drivers')
@login_required
def drivers():
    """Lista de motoristas"""
    drivers = Driver.query.order_by(Driver.name).all()
    return render_template('logistics/drivers/list.html', drivers=drivers)


@logistics_bp.route('/drivers/create', methods=['GET', 'POST'])
@login_required
def create_driver():
    """Criar novo motorista"""
    form = DriverForm()
    
    if form.validate_on_submit():
        driver = Driver(
            name=form.name.data,
            cpf=form.cpf.data,
            license_number=form.license_number.data,
            license_category=form.license_category.data,
            license_expiry=form.license_expiry.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            zip_code=form.zip_code.data,
            hire_date=form.hire_date.data,
            notes=form.notes.data
        )
        
        db.session.add(driver)
        db.session.commit()
        
        flash('Motorista cadastrado com sucesso!', 'success')
        return redirect(url_for('logistics.drivers'))
    
    return render_template('logistics/drivers/form.html', form=form, title='Novo Motorista')


# =============================================
# API ENDPOINTS
# =============================================

@logistics_bp.route('/api/tracking/<tracking_code>')
def api_tracking(tracking_code):
    """API pública para rastreamento"""
    shipment = Shipment.query.filter_by(tracking_code=tracking_code).first()
    
    if not shipment:
        return jsonify({'error': 'Código de rastreamento não encontrado'}), 404
    
    tracking_events = ShipmentTracking.query.filter_by(shipment_id=shipment.id).order_by(ShipmentTracking.timestamp.desc()).all()
    
    events_data = []
    for event in tracking_events:
        events_data.append({
            'status': event.status.value,
            'location': event.location,
            'description': event.description,
            'timestamp': event.timestamp.isoformat(),
            'latitude': float(event.latitude) if event.latitude else None,
            'longitude': float(event.longitude) if event.longitude else None
        })
    
    return jsonify({
        'tracking_code': shipment.tracking_code,
        'status': shipment.status.value,
        'recipient_name': shipment.recipient_name,
        'recipient_city': shipment.recipient_city,
        'recipient_state': shipment.recipient_state,
        'created_date': shipment.created_date.isoformat(),
        'delivered_date': shipment.delivered_date.isoformat() if shipment.delivered_date else None,
        'shipping_company': shipment.shipping_company.name if shipment.shipping_company else None,
        'events': events_data
    })


@logistics_bp.route('/api/calculate-freight', methods=['POST'])
@login_required
def api_calculate_freight():
    """API para calcular frete"""
    data = request.get_json()
    
    shipping_company_id = data.get('shipping_company_id')
    route_id = data.get('route_id')
    weight = data.get('weight', 0)
    
    if not shipping_company_id or not route_id:
        return jsonify({'error': 'Transportadora e rota são obrigatórios'}), 400
    
    shipping_company = ShippingCompany.query.get(shipping_company_id)
    route = Route.query.get(route_id)
    
    if not shipping_company or not route:
        return jsonify({'error': 'Transportadora ou rota não encontrada'}), 404
    
    # Calcular frete
    base_cost = float(route.total_cost())
    weight_cost = float(shipping_company.price_per_kg or 0) * float(weight)
    distance_cost = float(shipping_company.price_per_km or 0) * float(route.distance_km or 0)
    
    total = base_cost + weight_cost + distance_cost
    minimum = float(shipping_company.minimum_price or 0)
    
    freight_cost = max(total, minimum)
    
    return jsonify({
        'freight_cost': freight_cost,
        'base_cost': base_cost,
        'weight_cost': weight_cost,
        'distance_cost': distance_cost,
        'minimum_price': minimum,
        'details': {
            'route_distance': float(route.distance_km or 0),
            'estimated_time': float(route.estimated_time_hours or 0),
            'delivery_time_min': shipping_company.delivery_time_min,
            'delivery_time_max': shipping_company.delivery_time_max
        }
    })