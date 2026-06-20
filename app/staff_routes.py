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


@staff.route('/trek/<int:trek_id>')
@login_required
def trek_details(trek_id):
    """

    Display trek details including:
    - Trek info (name, location, difficulty, dates, slots)
    - List of registered participants with booking details
    - Action buttons (Update Slots, Change Status, Remove Participant)

    """
    trek = get_trek_or_404(trek_id)
    
    # Get all bookings for this trek (all participants)
    bookings = Booking.query.filter_by(trek_id=trek_id).all()
    
    # Enrich booking data with user details
    participants = []
    for booking in bookings:
        user = User.query.get(booking.user_id)
        participants.append({
            'booking': booking,
            'user': user
        })
    
    return render_template(
        'staff/trek_details.html',
        trek=trek,
        participants=participants,
        participant_count=len(participants)
    )


@staff.route('/trek/<int:trek_id>/update-slots', methods=['POST'])
@login_required
def update_trek_slots(trek_id):
    """
    Update available_slots for a trek.
    
    Validation:
    1. Trek must be assigned to current staff
    2. New available_slots must be >= 0
    3. New available_slots must be <= total_slots
    4. Cannot reduce below already booked count (data integrity)
    
    Process:
    1. Get trek (with auth check)
    2. Get new slot count from form
    3. Validate new_available >= booked_count
    4. Update trek.available_slots
    5. Commit and redirect
    
    """
    trek = get_trek_or_404(trek_id)
    
    # Get new available slots from form
    try:
        new_available = int(request.form.get('available_slots', 0))
    except ValueError:
        flash("Available slots must be a number", "error")
        return redirect(url_for('staff.trek_details', trek_id=trek_id))
    
    # Validate: Not negative
    if new_available < 0:
        flash("Available slots cannot be negative", "error")
        return redirect(url_for('staff.trek_details', trek_id=trek_id))
    
    # Validate: Not more than total slots
    if new_available > trek.total_slots:
        flash(f"Available slots cannot exceed total slots ({trek.total_slots})", "error")
        return redirect(url_for('staff.trek_details', trek_id=trek_id))
    
    # Count current booked participants
    booked_count = Booking.query.filter_by(
        trek_id=trek_id, 
        booking_status='booked'
    ).count()
    
    # Validate: Cannot reduce below booked count
    if new_available < booked_count:
        flash(
            f"Cannot reduce available slots below {booked_count} (current participants). "
            f"Set at least {booked_count}.",
            "error"
        )
        return redirect(url_for('staff.trek_details', trek_id=trek_id))
    
    # All validation passed - update slots
    try:
        trek.available_slots = new_available
        db.session.commit()
        flash(f"Trek slots updated to {new_available}", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating slots: {str(e)}", "error")
    
    return redirect(url_for('staff.trek_details', trek_id=trek_id))    


@staff.route('/trek/<int:trek_id>/update-status', methods=['POST'])
@login_required
def update_trek_status(trek_id):
    '''
    
    Update trek status. Allowed transitions:
    - open → closed
    - closed → completed
    - open → completed (direct)
    
    NOT allowed:
    - pending (admin-only)
    - approved (admin-only)
    - backtracking (closed → open)
    
    Validation:
    1. Trek must be assigned to current staff
    2. New status must be valid enum value
    3. Transition must be allowed 

    '''

    trek = get_trek_or_404(trek_id)
    new_status = request.form.get('status', '').lower()
    
    # Convert current status to lowercase for comparison
    current_status = trek.status.lower()
    
    # Define allowed transitions
    valid_transitions = {
        'open': ['closed', 'completed'],
        'closed': ['completed'],
        'completed': [],
    }
    
    # Check if current status allows transitions
    if current_status not in valid_transitions:
        flash(f"Trek status {trek.status} is not open for staff changes. Admin only.", "error")
        return redirect(url_for('staff.trek_details', trek_id=trek_id))
    
    # Check if new status is valid transition
    if new_status not in valid_transitions[current_status]:
        allowed = ', '.join(valid_transitions[current_status]) if valid_transitions[current_status] else 'None'
        flash(
            f"Invalid status transition: {trek.status} → {new_status}. "
            f"Allowed: {allowed}",
            "error"
        )
        return redirect(url_for('staff.trek_details', trek_id=trek_id))
    
    # Update status
    try:
        trek.status = new_status
        db.session.commit()
        flash(f"Trek status updated to {new_status.title()}", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating status: {str(e)}", "error")
    
    return redirect(url_for('staff.trek_details', trek_id=trek_id))


@staff.route('/trek/<int:trek_id>/remove-participant/<int:booking_id>', methods=['POST'])
@login_required
def remove_participant(trek_id, booking_id):
    """

    Remove a participant (cancel their booking).
    
    Process:
    1. Verify trek belongs to current staff
    2. Find booking
    3. Verify booking belongs to this trek
    4. Set booking_status = 'cancelled'
    5. Return slots to trek (increase available_slots)
    6. Commit and redirect
    
    """
    trek = get_trek_or_404(trek_id)
    booking = Booking.query.get_or_404(booking_id)
    
    # Verify booking belongs to this trek
    if booking.trek_id != trek_id:
        flash("Booking does not belong to this trek", "error")
        return redirect(url_for('staff.trek_details', trek_id=trek_id))
    
    # Get participant name before cancelling
    participant_name = booking.user.name
    
    try:
        # Check if booking is currently active (booked status)
        if booking.booking_status == 'booked':
            # Return slot to trek
            trek.available_slots += 1
        
        # Cancel booking
        booking.booking_status = 'cancelled'
        
        db.session.commit()
        flash(f"Participant {participant_name} removed from trek", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error removing participant: {str(e)}", "error")
    
    return redirect(url_for('staff.trek_details', trek_id=trek_id))