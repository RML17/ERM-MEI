from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models import Employee, Department, Position, Attendance, Leave, Payroll, Performance
from services.hr_service import hr_service, calculate_employee_payroll, get_employee_performance
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

hr_bp = Blueprint('hr', __name__, url_prefix='/hr')


@hr_bp.route('/')
@login_required
def index():
    """Dashboard principal do RH"""
    
    # Estatísticas gerais
    total_employees = Employee.query.filter_by(status='active').count()
    total_departments = Department.query.count()
    pending_leaves = Leave.query.filter_by(status='pending').count()
    
    # Funcionários por departamento
    dept_stats = db.session.query(
        Department.name,
        db.func.count(Employee.id).label('employee_count')
    ).outerjoin(Employee, Department.id == Employee.department_id).group_by(Department.name).all()
    
    # Aniversariantes do mês
    current_month = date.today().month
    birthdays = Employee.query.filter(
        db.extract('month', Employee.birth_date) == current_month,
        Employee.status == 'active'
    ).all()
    
    # Admissões recentes (últimos 30 dias)
    recent_hires = Employee.query.filter(
        Employee.hire_date >= date.today() - timedelta(days=30),
        Employee.status == 'active'
    ).order_by(Employee.hire_date.desc()).limit(5).all()
    
    return render_template('hr/dashboard.html',
                         total_employees=total_employees,
                         total_departments=total_departments,
                         pending_leaves=pending_leaves,
                         dept_stats=dept_stats,
                         birthdays=birthdays,
                         recent_hires=recent_hires)


@hr_bp.route('/employees')
@login_required
def employees():
    """Lista de funcionários"""
    page = request.args.get('page', 1, type=int)
    department_id = request.args.get('department')
    status = request.args.get('status', 'active')
    
    query = Employee.query
    
    if department_id:
        query = query.filter_by(department_id=department_id)
    
    if status:
        query = query.filter_by(status=status)
    
    employees = query.order_by(Employee.first_name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    departments = Department.query.all()
    
    return render_template('hr/employees/list.html',
                         employees=employees,
                         departments=departments,
                         selected_department=department_id,
                         selected_status=status)


@hr_bp.route('/employees/<int:employee_id>')
@login_required
def employee_detail(employee_id):
    """Detalhes do funcionário"""
    employee = Employee.query.get_or_404(employee_id)
    
    # Últimas presenças
    recent_attendance = Attendance.query.filter_by(employee_id=employee_id)\
        .order_by(Attendance.date.desc()).limit(10).all()
    
    # Férias pendentes e aprovadas
    leaves = Leave.query.filter_by(employee_id=employee_id)\
        .order_by(Leave.start_date.desc()).limit(5).all()
    
    # Última avaliação
    last_evaluation = Performance.query.filter_by(employee_id=employee_id)\
        .order_by(Performance.evaluation_date.desc()).first()
    
    return render_template('hr/employees/detail.html',
                         employee=employee,
                         recent_attendance=recent_attendance,
                         leaves=leaves,
                         last_evaluation=last_evaluation)


@hr_bp.route('/payroll')
@login_required
def payroll():
    """Gestão de folha de pagamento"""
    
    # Períodos de folha recentes
    recent_payrolls = db.session.query(
        Payroll.period_start,
        Payroll.period_end,
        db.func.count(Payroll.id).label('employee_count'),
        db.func.sum(Payroll.gross_salary).label('total_gross'),
        db.func.sum(Payroll.net_salary).label('total_net')
    ).group_by(
        Payroll.period_start, Payroll.period_end
    ).order_by(Payroll.period_start.desc()).limit(6).all()
    
    return render_template('hr/payroll/index.html',
                         recent_payrolls=recent_payrolls)


@hr_bp.route('/payroll/calculate', methods=['GET', 'POST'])
@login_required
def calculate_payroll():
    """Calculadora de folha de pagamento"""
    
    if request.method == 'POST':
        try:
            employee_id = int(request.form.get('employee_id'))
            period_start = datetime.strptime(request.form.get('period_start'), '%Y-%m-%d').date()
            period_end = datetime.strptime(request.form.get('period_end'), '%Y-%m-%d').date()
            overtime_hours = Decimal(request.form.get('overtime_hours', '0'))
            bonus = Decimal(request.form.get('bonus', '0'))
            
            # Calcular folha
            calculation = calculate_employee_payroll(
                employee_id, period_start, period_end,
                overtime_hours=overtime_hours,
                bonus=bonus
            )
            
            return render_template('hr/payroll/calculation_result.html',
                                 calculation=calculation)
            
        except Exception as e:
            flash(f'Erro ao calcular folha: {str(e)}', 'error')
    
    employees = Employee.query.filter_by(status='active').order_by(Employee.first_name).all()
    
    return render_template('hr/payroll/calculate.html',
                         employees=employees)


@hr_bp.route('/api/payroll/batch', methods=['POST'])
@login_required
def api_payroll_batch():
    """API para cálculo de folha em lote"""
    try:
        data = request.get_json()
        
        period_start = datetime.strptime(data.get('period_start'), '%Y-%m-%d').date()
        period_end = datetime.strptime(data.get('period_end'), '%Y-%m-%d').date()
        department_id = data.get('department_id')
        
        results = hr_service.create_payroll_batch(period_start, period_end, department_id)
        
        # Converter Decimal para float para JSON
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [decimal_to_float(item) for item in obj]
            return obj
        
        return jsonify(decimal_to_float(results))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@hr_bp.route('/attendance')
@login_required
def attendance():
    """Gestão de ponto eletrônico"""
    
    today = date.today()
    
    # Presenças de hoje
    today_attendance = db.session.query(
        Employee.first_name,
        Employee.last_name,
        Attendance.clock_in,
        Attendance.clock_out,
        Attendance.is_late,
        Attendance.regular_hours
    ).join(Attendance).filter(
        Attendance.date == today,
        Employee.status == 'active'
    ).all()
    
    # Estatísticas do mês
    month_start = today.replace(day=1)
    attendance_stats = db.session.query(
        db.func.count(Attendance.id).label('total_records'),
        db.func.sum(db.cast(Attendance.is_late == True, db.Integer)).label('late_count'),
        db.func.sum(db.cast(Attendance.is_absent == True, db.Integer)).label('absent_count')
    ).filter(Attendance.date >= month_start).first()
    
    return render_template('hr/attendance/index.html',
                         today_attendance=today_attendance,
                         attendance_stats=attendance_stats)


@hr_bp.route('/leaves')
@login_required
def leaves():
    """Gestão de férias e licenças"""
    
    # Solicitações pendentes
    pending_leaves = Leave.query.filter_by(status='pending')\
        .order_by(Leave.created_at.desc()).all()
    
    # Férias programadas para os próximos 30 dias
    upcoming_leaves = Leave.query.filter(
        Leave.status == 'approved',
        Leave.start_date <= date.today() + timedelta(days=30),
        Leave.start_date >= date.today()
    ).order_by(Leave.start_date).all()
    
    return render_template('hr/leaves/index.html',
                         pending_leaves=pending_leaves,
                         upcoming_leaves=upcoming_leaves)


@hr_bp.route('/leaves/<int:leave_id>/approve', methods=['POST'])
@login_required
def approve_leave(leave_id):
    """Aprovar solicitação de férias"""
    leave = Leave.query.get_or_404(leave_id)
    
    try:
        leave.status = 'approved'
        leave.approved_by = current_user.id
        leave.approved_at = datetime.utcnow()
        leave.approval_notes = request.form.get('notes', '')
        leave.days_approved = int(request.form.get('days_approved', leave.days_requested))
        
        db.session.commit()
        flash('Solicitação aprovada com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao aprovar solicitação: {str(e)}', 'error')
    
    return redirect(url_for('hr.leaves'))


@hr_bp.route('/performance')
@login_required
def performance():
    """Gestão de avaliações de desempenho"""
    
    # Avaliações pendentes
    pending_evaluations = Performance.query.filter_by(status='draft')\
        .order_by(Performance.created_at.desc()).limit(10).all()
    
    # Últimas avaliações concluídas
    completed_evaluations = Performance.query.filter_by(status='completed')\
        .order_by(Performance.evaluation_date.desc()).limit(10).all()
    
    return render_template('hr/performance/index.html',
                         pending_evaluations=pending_evaluations,
                         completed_evaluations=completed_evaluations)


@hr_bp.route('/api/employee/<int:employee_id>/performance')
@login_required
def api_employee_performance(employee_id):
    """API para métricas de performance do funcionário"""
    try:
        period_months = int(request.args.get('period', 6))
        performance_data = get_employee_performance(employee_id, period_months)
        
        # Converter Decimal para float
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [decimal_to_float(item) for item in obj]
            return obj
        
        return jsonify(decimal_to_float(performance_data))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@hr_bp.route('/api/employee/<int:employee_id>/vacation')
@login_required
def api_employee_vacation(employee_id):
    """API para saldo de férias do funcionário"""
    try:
        vacation_data = hr_service.calculate_vacation_days(employee_id)
        
        return jsonify(vacation_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@hr_bp.route('/departments', methods=['GET', 'POST'])
@login_required
def departments():
    """Gestão de departamentos"""
    
    # Lista de departamentos para exibição na página
    try:
        departments = Department.query.all()
        employees = Employee.query.filter_by(status='active').all()
    except Exception as e:
        departments = []
        employees = []
        print(f"Erro ao consultar departamentos: {str(e)}")
    
    return render_template('hr/departments/index.html',
                         departments=departments,
                         employees=employees)


@hr_bp.route('/reports')
@login_required
def reports():
    """Relatórios de RH"""
    
    # Estatísticas para relatórios
    total_employees = Employee.query.filter_by(status='active').count()
    
    # Distribuição por gênero
    gender_stats = db.session.query(
        Employee.gender,
        db.func.count(Employee.id).label('count')
    ).filter_by(status='active').group_by(Employee.gender).all()
    
    # Distribuição por faixa etária
    today = date.today()
    age_stats = []
    for age_range in ['18-25', '26-35', '36-45', '46-55', '56+']:
        if age_range == '18-25':
            count = Employee.query.filter(
                Employee.birth_date >= today.replace(year=today.year-25),
                Employee.birth_date <= today.replace(year=today.year-18),
                Employee.status == 'active'
            ).count()
        elif age_range == '26-35':
            count = Employee.query.filter(
                Employee.birth_date >= today.replace(year=today.year-35),
                Employee.birth_date < today.replace(year=today.year-25),
                Employee.status == 'active'
            ).count()
        # ... mais ranges de idade
        else:
            count = 0
        
        age_stats.append({'range': age_range, 'count': count})
    
    return render_template('hr/reports/index.html',
                         total_employees=total_employees,
                         gender_stats=gender_stats,
                         age_stats=age_stats)