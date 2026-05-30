from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from app import db
from models import User, UserRole, AuditLog, Invoice, Payment, Product
from forms import LoginForm, RegistrationForm, ChangePasswordForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            
            # Registrar data do último login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Registrar log de auditoria
            log = AuditLog(
                user_id=user.id,
                action='login',
                table_name='users',
                row_id=user.id,
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Nome de usuário ou senha inválidos.', 'danger')
    
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    # Registrar log de auditoria
    log = AuditLog(
        user_id=current_user.id,
        action='logout',
        table_name='users',
        row_id=current_user.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash('Você saiu com sucesso.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # Verificar se o usuário tem permissão de administrador
    if current_user.role != UserRole.ADMIN:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Verificar se o usuário ou email já existe
        if User.query.filter_by(username=form.username.data).first():
            flash('Este nome de usuário já está em uso.', 'danger')
            return render_template('register.html', form=form)
            
        if User.query.filter_by(email=form.email.data).first():
            flash('Este email já está em uso.', 'danger')
            return render_template('register.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        
        # Registrar log de auditoria
        log = AuditLog(
            user_id=current_user.id,
            action='create',
            table_name='users',
            row_id=None,  # Será atualizado após o commit
            new_values=f"username={user.username}, email={user.email}, role={user.role.value}",
            ip_address=request.remote_addr
        )
        
        db.session.add(log)
        db.session.commit()
        
        # Atualizar o row_id do log com o ID do usuário criado
        log.row_id = user.id
        db.session.commit()
        
        flash(f'Usuário {user.username} criado com sucesso!', 'success')
        return redirect(url_for('auth.users_list'))
    
    return render_template('register.html', form=form)

@auth_bp.route('/users')
@login_required
def users_list():
    # Verificar se o usuário tem permissão de administrador
    if current_user.role != UserRole.ADMIN:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    users = User.query.all()
    return render_template('users_list.html', users=users)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Senha atual incorreta.', 'danger')
            return render_template('change_password.html', form=form)
        
        current_user.set_password(form.new_password.data)
        
        # Registrar log de auditoria
        log = AuditLog(
            user_id=current_user.id,
            action='update',
            table_name='users',
            row_id=current_user.id,
            old_values="password=*****",
            new_values="password=*****",
            ip_address=request.remote_addr
        )
        
        db.session.add(log)
        db.session.commit()
        
        flash('Sua senha foi alterada com sucesso.', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('change_password.html', form=form)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'profile':
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip()

            if full_name:
                current_user.full_name = full_name
            if email:
                existing = User.query.filter(User.email == email, User.id != current_user.id).first()
                if existing:
                    flash('Este e-mail já está em uso por outro usuário.', 'danger')
                    return redirect(url_for('auth.profile'))
                current_user.email = email

            db.session.commit()
            log = AuditLog(
                user_id=current_user.id,
                action='update',
                table_name='users',
                row_id=current_user.id,
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            flash('Perfil atualizado com sucesso.', 'success')
            return redirect(url_for('auth.profile'))

        elif form_type == 'password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not current_user.check_password(current_password):
                flash('Senha atual incorreta.', 'danger')
                return redirect(url_for('auth.profile'))
            if len(new_password) < 8:
                flash('A nova senha deve ter pelo menos 8 caracteres.', 'danger')
                return redirect(url_for('auth.profile'))
            if new_password != confirm_password:
                flash('As senhas não coincidem.', 'danger')
                return redirect(url_for('auth.profile'))

            current_user.set_password(new_password)
            log = AuditLog(
                user_id=current_user.id,
                action='update',
                table_name='users',
                row_id=current_user.id,
                old_values='password=*****',
                new_values='password=*****',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            flash('Senha alterada com sucesso.', 'success')
            return redirect(url_for('auth.profile'))

    invoices_count = Invoice.query.filter_by(created_by_id=current_user.id).count()
    payments_count = Payment.query.count()
    products_count = Product.query.count()
    logs_count = AuditLog.query.filter_by(user_id=current_user.id).count()

    stats = {
        'invoices_count': invoices_count,
        'payments_count': payments_count,
        'products_count': products_count,
        'logs_count': logs_count,
    }

    recent_logs = AuditLog.query.filter_by(user_id=current_user.id)\
        .order_by(AuditLog.timestamp.desc()).limit(10).all()

    return render_template('profile.html', stats=stats, recent_logs=recent_logs)
