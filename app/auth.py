from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, StaffProfile

auth = Blueprint('auth', __name__)


@auth.route('/')
def index():
    if current_user.is_authenticated:
        return redirect_by_role(current_user.role)
    return redirect(url_for('auth.login'))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_by_role(current_user.role)

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))

        if user.status == 'blacklisted':
            flash('Your account has been blacklisted. Contact admin.', 'danger')
            return redirect(url_for('auth.login'))

        # Staff must be approved by admin
        if user.role == 'staff':
            profile = StaffProfile.query.filter_by(user_id=user.id).first()
            if not profile or not profile.approved_by_admin:
                flash('Your staff account is pending admin approval.', 'warning')
                return redirect(url_for('auth.login'))

        login_user(user)
        return redirect_by_role(user.role)

    return render_template('login.html')


@auth.route('/register/trekker', methods=['GET', 'POST'])
def register_trekker():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register_trekker'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register_trekker'))

        new_user = User(
            name=name,
            email=email,
            contact_number=request.form.get('contact_number'),
            whatsapp_number=request.form.get('whatsapp_number'),
            password=generate_password_hash(password),
            role='trekker',
            status='active'
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register_trekker.html')


@auth.route('/register/staff', methods=['GET', 'POST'])
def register_staff():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        contact_number = request.form.get('contact_number')
        whatsapp_number = request.form.get('whatsapp_number')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        specialization = request.form.get('specialization')
        experience = request.form.get('experience')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register_staff'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register_staff'))

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role='staff',
            status='active'
        )
        db.session.add(new_user)
        db.session.flush()  # Get the new user's ID before committing

        staff_profile = StaffProfile(
            user_id=new_user.id,
            specialization=specialization,
            experience=int(experience),
            status='Inactive',
            approved_by_admin=False
        )
        db.session.add(staff_profile)
        db.session.commit()
        flash('Staff registration submitted! Await admin approval.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register_staff.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))


def redirect_by_role(role):
    if role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif role == 'staff':
        return redirect(url_for('staff.dashboard'))
    else:
        return redirect(url_for('user.dashboard'))