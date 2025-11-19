from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import logout_user
from models import db
from models.user import User
from forms import LoginForm, RegistrationForm
import secrets

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
    form = LoginFormNoCSRF()
    
    if form.validate_on_submit():
        # Find user by email (case-insensitive)
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        # Check if user exists and password is correct
        if user and user.check_password(form.password.data):
            # Check if account is active
            if not user.is_active:
                return redirect(url_for('auth.login'))
            
            # Generate auth token
            auth_token = secrets.token_urlsafe(32)
            
            # Store in session AS BACKUP
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            session['auth_token'] = auth_token
            session.permanent = True
            
            user.update_last_login()
            db.session.commit()
            
            # Redirect with cookies
            if user.is_admin:
                response = redirect(url_for('admin.dashboard'))
            else:
                response = redirect(url_for('dashboard.index'))
            
            # Set authentication cookies
            response.set_cookie('auth_token', auth_token, max_age=3600, httponly=False, samesite=None)
            response.set_cookie('user_id', str(user.id), max_age=3600, httponly=False, samesite=None)
            response.set_cookie('is_admin', str(user.is_admin), max_age=3600, httponly=False, samesite=None)
            
            return response
        else:
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('auth/login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    # Redirect if already logged in
    if session.get('user_id'):
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
        
        return redirect(url_for('auth.login', registered='true'))
    
    return render_template('auth/register.html', form=form)


@bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    logout_user()
    response = redirect(url_for('auth.login'))
    response.set_cookie('auth_token', '', max_age=0)
    response.set_cookie('user_id', '', max_age=0)
    response.set_cookie('is_admin', '', max_age=0)
    return response