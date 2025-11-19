from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import logout_user
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
    # Check if already logged in via session
    if session.get('user_id'):
        user = User.query.get(session.get('user_id'))
        if user:
            if user.is_admin:
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
                return redirect(url_for('auth.login'))
            
            # Manual session login
            print(f"DEBUG LOGIN: Setting session for user {user.id}")
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            session.permanent = True
            print(f"DEBUG LOGIN: Session after set = {dict(session)}")
            
            user.update_last_login()
            db.session.commit()
            
            print(f"DEBUG LOGIN: About to redirect to admin dashboard")
            
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
    return redirect(url_for('auth.login'))