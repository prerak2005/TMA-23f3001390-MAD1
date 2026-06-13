from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import Trek, Booking, User, StaffProfile
from datetime import datetime

staff = Blueprint('staff', __name__, url_prefix='/staff')

# AUHTORIZATION LAYER(Ensuring staff can access the trekk that are only assigned to them)
def get_trek_or_404(trek_id):
    '''

    Get trek if it exsits and is assigned to current_user(staff)
    returns 404 if trek doesn't exist or not assigned to this staff

    '''

    trek = Trek.query.get_or_404(trek_id)
    if trek.assigned_staff_id != current_user.id:
        abort(404)
    return trek

@staff.route('/dashboard')
@login_required
def dashboard():
    '''

    Staff Dashboard showing all treks assigned to this staff member.

    '''
    # check if user is staff
    if current_user.role != 'staff':
        abort(403)

    # get staff profile to check approval status
    staff_profile = StaffProfile.query.filter_by(user_id=current_user.id).first()
    if not staff_profile or staff_profile.status != 'approved':
        flash("You must be approved by admin before accessing staff features", "warning")
        return redirect(url_for('auth.login'))
    
    # get all treks assigned to this staff
    assigned_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).all()

    # trek stats
    trek_data = []
    for trek in assigned_treks:
        participant_count = Booking.query.filter_by(
            trek_id=trek.id,
            booking_status='booked'
        ).count()
        trek_data.append({
            'trek': trek,
            'participant_count': participant_count,
            'available_slots': trek.available_slots
        })

    # calculate stats
    total_treks = len(assigned_treks)
    open_treks = sum(1 for t in assigned_treks if t.status == 'open')
    closed_treks = sum(1 for t in assigned_treks if t.status == 'closed')
    total_participants = sum(data['participant_count'] for data in trek_data)
    
    return render_template(
        'staff/dashboard.html',
        trek_data=trek_data,
        total_treks=total_treks,
        open_treks=open_treks,
        closed_treks=closed_treks,
        total_participants=total_participants
        )