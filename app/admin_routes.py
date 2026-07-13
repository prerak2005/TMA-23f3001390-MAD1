from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import User, Trek, Booking, StaffProfile, complete_active_bookings_for_trek
from app import db
from datetime import datetime, timezone

admin = Blueprint('admin', __name__, url_prefix='/admin')

# Admin trek lifecycle — each stage may only move forward (no skipping or backtracking)
ADMIN_TREK_TRANSITIONS = {
    'Pending': ['Approved'],
    'Approved': ['Open'],
    'Open': ['Closed', 'Completed'],
    'Closed': ['Completed'],
    'Completed': [],
}

_TREK_STATUS_TITLE = {
    'pending': 'Pending',
    'approved': 'Approved',
    'open': 'Open',
    'closed': 'Closed',
    'completed': 'Completed',
}


def _normalize_trek_status(status):
    """Match Title Case stored by seeds/admin even if legacy rows differ in casing."""
    if not status:
        return status
    return _TREK_STATUS_TITLE.get(status.lower(), status)


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
    pending_staff = StaffProfile.query.filter_by(status='pending').count()

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


@admin.route('/trekk/create', methods=['GET', 'POST'])
@login_required
def create_trek():
    '''Create New trekk'''

    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            location = request.form.get('location', '').strip()
            difficulty = request.form.get('difficulty', '').strip()
            duration = request.form.get('duration', '').strip()
            total_slots = request.form.get('total_slots', '').strip()
            start_date = request.form.get('start_date', '').strip()
            end_date = request.form.get('end_date', '').strip()

            # Validation
            if not all([name, location, difficulty, duration, total_slots, start_date, end_date]):
                flash('All fields are required.', 'danger')
                return redirect(url_for('admin.create_trek'))
            
            # Validate numeric fields
            try:
                duration = float(duration)
                total_slots = int(total_slots)
            except ValueError:
                flash('Duration must be a number and Total Slots must be an integer.', 'danger')
                return redirect(url_for('admin.create_trek'))
            
            # Validate difficulty
            valid_difficulties = ['Easy', 'Moderate', 'Hard', 'Extreme']
            if difficulty not in valid_difficulties:
                flash(f'Difficulty must be one of: {", ".join(valid_difficulties)}', 'danger')
                return redirect(url_for('admin.create_trek'))
            
            # Parse dates
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
                return redirect(url_for('admin.create_trek'))
            
            # Validate date logic
            if start_date >= end_date:
                flash('Start date must be before end date.', 'danger')
                return redirect(url_for('admin.create_trek'))
            
            # Create new trek
            new_trek = Trek(
                name=name,
                location=location,
                difficulty=difficulty,
                duration=duration,
                total_slots=total_slots,
                available_slots=total_slots,  # Initially all slots are available
                status='Pending',  # New treks start as pending approval, admin approves later
                start_date=start_date,
                end_date=end_date
            )

            db.session.add(new_trek)
            db.session.commit()

            flash(f'Trek "{name}" created successfully!', 'success')
            return redirect(url_for('admin.manage_treks'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating trek: {str(e)}', 'danger')
            return redirect(url_for('admin.create_trek'))
    
    # Get request shows form
    return render_template('admin/create_trek.html')


@admin.route('/treks')
@login_required
def manage_treks():
    '''View all treks with options to approve, edit, or delete'''

    search_query = request.args.get('search', '').strip()

    if search_query:
        # Search by name or location(case-insensitive)
        treks = Trek.query.filter(
            db.or_(
                Trek.name.ilike(f'%{search_query}%'),
                Trek.location.ilike(f'%{search_query}%')
            )
        ).all()
        search_message = f'Found {len(treks)} trek(s) matching "{search_query}"'
    else:
        # Get all treks, sorted by creation date(newest first)
        treks = Trek.query.order_by(Trek.created_at.desc()).all()
        search_message = None

    return render_template(
        'admin/manage_treks.html',
        treks=treks,
        search_query=search_query,
        search_message=search_message
    )


@admin.route('/trek/<int:trek_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_trek(trek_id):
    '''Edit an exsisting trek'''

    trek = Trek.query.get_or_404(trek_id)

    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            location = request.form.get('location', '').strip()
            difficulty = request.form.get('difficulty', '').strip()
            duration = request.form.get('duration', '').strip()
            total_slots = request.form.get('total_slots', '').strip()
            start_date = request.form.get('start_date', '').strip()
            end_date = request.form.get('end_date', '').strip()

            # Validation
            if not all([name, location, difficulty, duration, total_slots, start_date, end_date]):
                flash('All fields are required.', 'danger')
                return redirect(url_for('admin.edit_trek', trek_id=trek_id))
            
            # Validate numeric fields
            try:
                duration = float(duration)
                total_slots = int(total_slots)
            except ValueError:
                flash('Duration must be a number and Total Slots must be an integer.', 'danger')
                return redirect(url_for('admin.edit_trek', trek_id=trek_id))
            
            # Validate difficulty
            valid_difficulties = ['Easy', 'Moderate', 'Hard', 'Extreme']
            if difficulty not in valid_difficulties:
                flash(f'Difficulty must be one of: {", ".join(valid_difficulties)}', 'danger')
                return redirect(url_for('admin.edit_trek', trek_id=trek_id))
            
            # Parse dates
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
                return redirect(url_for('admin.edit_trek', trek_id=trek_id))
            
            # Validate date logic
            if start_date >= end_date:
                flash('Start date must be before end date.', 'danger')
                return redirect(url_for('admin.edit_trek', trek_id=trek_id))
            
            # Validate total_slots doesn't go below available_slots already booked
            booked_slots = trek.total_slots - trek.available_slots
            if total_slots < booked_slots:
                flash(f'Cannot reduce slots to {total_slots}. Already {booked_slots} slot(s) booked!', 'danger')
                return redirect(url_for('admin.edit_trek', trek_id=trek_id))
            
            # Update trek 
            trek.name = name
            trek.location = location
            trek.difficulty = difficulty
            trek.duration = duration
            trek.start_date = start_date
            trek.end_date = end_date

            # Adjust available_slots if total_slots changed
            slots_difference = total_slots - trek.total_slots
            trek.total_slots = total_slots
            trek.available_slots += slots_difference  # Increase or decrease available slots based on total_slots change

            db.session.commit()

            flash(f'Trek "{name}" updated successfully!', 'success')
            return redirect(url_for('admin.manage_treks'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating trek: {str(e)}', 'danger')
            return redirect(url_for('admin.edit_trek', trek_id=trek_id))
        
    # GET request - show form with existing data
    return render_template('admin/edit_trek.html', trek=trek)


@admin.route('/trek/<int:trek_id>/delete-confirm', methods=['GET', 'POST'])
@login_required
def delete_trek_confirm(trek_id):
    '''show confirmation page before deleting trek'''

    trek = Trek.query.get_or_404(trek_id)

    if request.method == 'POST':

        try:
            # check if trek has active booking
            active_bookings = Booking.query.filter_by(trek_id=trek_id).count()

            if active_bookings > 0:
                flash(f'Cannot delete trek with {active_bookings} active booking(s)!', 'danger')
                return redirect(url_for('admin.manage_treks'))
            
            #delete trek
            db.session.delete(trek)
            db.session.commit()

            flash(f'Trek "{trek.name}" deleted successfully!', 'success')
            return redirect(url_for('admin.manage_treks'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting trek: {str(e)}', 'danger')
            return redirect(url_for('admin.manage_treks'))
        
    # GET request - show confirmation page
    return render_template('admin/delete_trek_confirm.html', trek=trek)


@admin.route('/trek/<int:trek_id>/status/<new_status>', methods=['POST'])
@login_required
def update_trek_status(trek_id, new_status):
    '''

    Update Trek Status (Pending -> Approved -> Open -> Closed -> Completed)
    
    '''

    trek = Trek.query.get_or_404(trek_id)

    valid_responses = ['Pending', 'Approved', 'Open', 'Closed', 'Completed']

    if new_status not in valid_responses:
        flash('Invalid Status!', 'danger')
        return redirect(url_for('admin.manage_treks'))

    current_status = _normalize_trek_status(trek.status)
    allowed_next = ADMIN_TREK_TRANSITIONS.get(current_status, [])
    if new_status not in allowed_next:
        allowed_label = ', '.join(allowed_next) if allowed_next else 'None (final state)'
        flash(
            f'Invalid status transition: {current_status} → {new_status}. Allowed: {allowed_label}',
            'danger'
        )
        return redirect(url_for('admin.manage_treks'))
    
    try:
        trek.status = new_status
        # Trek completion closes out every still-active booking for this trek
        if new_status == 'Completed':
            complete_active_bookings_for_trek(trek_id)
        db.session.commit()
        flash(f'Trek "{trek.name}" status changed to {new_status}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating status: {str(e)}', 'danger')

    return redirect(url_for('admin.manage_treks'))


# STAFF MANAGEMENT ROUTES
@admin.route('/staff/pending')
@login_required
def view_pending_staff():
    '''
    Display staff members pending approval.
 
    We query StaffProfile where status='pending', then get the linked User
    for display info (name, email, contact).

    '''
    # Get all StaffProfiles where approval is still pending
    pending_profiles = StaffProfile.query.filter_by(status='pending').all()
 
    return render_template('admin/pending_staff.html', pending_profiles=pending_profiles)


@admin.route('/staff/approve/<int:user_id>', methods=['POST'])
@login_required
def approve_staff(user_id):
    '''
    Approve a pending staff member.
 
    Process:
    1. Get staff user by ID (404 if not found)
    2. Get their StaffProfile
    3. Check StaffProfile.status is 'pending' (safety check)
    4. Set StaffProfile.status = 'approved'
    5. Set StaffProfile.approved_by_admin = True
    6. Update StaffProfile.updated_at timestamp
    7. Commit and redirect with success message
 
    Note: User.status stays 'active' — we never touch it here.
    The login check will use StaffProfile.status to allow/block staff login.
    '''
    staff_user = User.query.get_or_404(user_id)
    staff_profile = StaffProfile.query.filter_by(user_id=user_id).first()
 
    # Safety check — profile must exist and be pending
    if not staff_profile or staff_profile.status != 'pending':
        flash(f'{staff_user.name} is not pending approval.', 'warning')
        return redirect(url_for('admin.view_pending_staff'))
 
    # Update StaffProfile only
    staff_profile.status = 'approved'
    staff_profile.approved_by_admin = True
    staff_profile.updated_at = datetime.now(timezone.utc)
 
    try:
        db.session.commit()
        flash(f'{staff_user.name} has been approved as Trek Staff!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving staff: {str(e)}', 'danger')
 
    return redirect(url_for('admin.view_pending_staff'))


@admin.route('/staff/reject/<int:user_id>', methods=['POST'])
@login_required
def reject_staff(user_id):
    '''
    Reject a pending staff member.
 
    Process:
    1. Get staff user by ID (404 if not found)
    2. Get their StaffProfile
    3. Check StaffProfile.status is 'pending' (safety check)
    4. Set StaffProfile.status = 'rejected'
    5. Update StaffProfile.updated_at timestamp
    6. Commit and redirect with info message
 
    '''
    staff_user = User.query.get_or_404(user_id)
    staff_profile = StaffProfile.query.filter_by(user_id=user_id).first()
 
    # Safety check — profile must exist and be pending
    if not staff_profile or staff_profile.status != 'pending':
        flash(f'{staff_user.name} is not pending approval.', 'warning')
        return redirect(url_for('admin.view_pending_staff'))
 
    # Update StaffProfile only 
    staff_profile.status = 'rejected'
    staff_profile.updated_at = datetime.now(timezone.utc)
 
    try:
        db.session.commit()
        flash(f'{staff_user.name} application has been rejected.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting staff: {str(e)}', 'danger')
 
    return redirect(url_for('admin.view_pending_staff'))


@admin.route('/staff/all')
@login_required
def view_all_staff():
    '''
    Display all staff members regardless of approval status.
 
    We query all StaffProfiles and join with User data for display.
    Groups shown: approved, pending, rejected — all in one table with badges.

    '''
    all_profiles = StaffProfile.query.all()
 
    return render_template('admin/view_all_staff.html', all_profiles=all_profiles)


# USER MANAGEMENT ROUTES
@admin.route('/users')
@login_required
def manage_users():
    '''
    View all users and manage their status
    '''

    search_query = request.args.get('search', '').strip()

    if search_query:
        users = User.query.filter_by(role='trekker').filter(
            db.or_(
                User.name.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        ).all()
        search_message = f'Found {len(users)} user(s) matching "{search_query}"'
    else:
        users = User.query.filter_by(role='trekker').order_by(User.created_at.desc()).all()
        search_message = None

    return render_template(
        'admin/manage_users.html',
        users=users,
        search_query=search_query,
        search_message=search_message
    )


@admin.route('/user/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    '''

    Toggle user status (Active -> BLacklisted/BLacklisted -> Active)
    
    '''

    user = User.query.get_or_404(user_id)

    if user.role == 'admin':
        flash('Cannot modify admin users!', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    try:
        if user.status == 'active':
            user.status = 'blacklisted'
            action = 'blacklisted'
        else:
            user.status = 'active'
            action = 'activated'

        db.session.commit()
        flash(f'User "{user.name}" {action} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user: {str(e)}', 'danger')

    return redirect(url_for('admin.manage_users'))


@admin.route('/bookings')
@login_required
def manage_bookings():
    '''
    
    View all bookings
    
    '''

    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    
    stats = {
        'total_bookings': len(bookings),
        'pending_bookings': sum(1 for b in bookings if b.booking_status == 'Booked'),
        'completed_bookings': sum(1 for b in bookings if b.booking_status == 'Completed'),
        'cancelled_bookings': sum(1 for b in bookings if b.booking_status == 'Cancelled')
    }
    
    return render_template('admin/manage_bookings.html', bookings=bookings, stats=stats)


@admin.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    '''
    
    Cancel a booking
    
    '''

    booking = Booking.query.get_or_404(booking_id)
    
    if booking.booking_status == 'Cancelled':
        flash('This booking is already cancelled!', 'warning')
        return redirect(url_for('admin.manage_bookings'))

    if booking.booking_status != 'Booked':
        flash(f'Cannot cancel a {booking.booking_status} booking.', 'warning')
        return redirect(url_for('admin.manage_bookings'))
    
    try:
        booking.booking_status = 'Cancelled'
        
        # Only Booked reservations consumed a slot — Completed/Cancelled must not refund again
        trek = Trek.query.get(booking.trek_id)
        trek.available_slots += 1
        
        db.session.commit()
        flash(f'Booking cancelled successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling booking: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_bookings'))