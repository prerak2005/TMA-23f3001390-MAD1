from flask import Blueprint, render_template
from flask_login import login_required
from app.models import User, Trek, Booking, StaffProfile

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/dashboard')
@login_required
def dashboard():
    '''Admin Dashboard with statistics and management options'''

    # query stats from database
    total_users = User.query.filter_by(role='trekker').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_treks = Trek.query.count()
    total_bookings = Booking.query.count()

    # pending staff approvals
    pending_staff = User.query.filter_by(role='staff', status='pending').count()

    # pending trekk approvals
    # pending_treks = Trek.query.filter_by(status='Pending').count()

    stats = {
        'total_users': total_users,
        'total_staff' : total_staff,
        'total_treks' : total_treks,
        'total_bookings' : total_bookings,
        'pending_staff' : pending_staff
        # 'pending_treks' : pending_treks
    }

    return render_template('admin/dashboard.html', stats=stats)