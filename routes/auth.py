from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from models import db
from models.user import User
from forms import LoginForm, RegistrationForm

# Disable CSRF for testing
class LoginFormNoCSRF(LoginForm):
    class Meta:
        csrf = False

class RegistrationFormNoCSRF(RegistrationForm):
    class Meta:
        csrf = False

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    # Redirect if already logged in
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('dashboard.index'))
    
    form = LoginFormNoCSRF()
    
    if form.validate_on_submit():
        # Find user by email (case-insensitive)
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        # Check if user exists and password is correct
        if user and user.check_password(form.password.data):
            # Check if account is active
            if not user.is_active:
                flash('Your account has been suspended. Please contact support.', 'error')
                return redirect(url_for('auth.login'))
            
            # Login user
            login_user(user, remember=form.remember_me.data)
            user.update_last_login()
            
            flash(f'Welcome back, {user.email}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            # Redirect based on role
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('auth/login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationFormNoCSRF()
    
    if form.validate_on_submit():
        # Create new user
        user = User(
            email=form.email.data.lower(),
            is_active=True
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)


@bp.route('/logout')
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))