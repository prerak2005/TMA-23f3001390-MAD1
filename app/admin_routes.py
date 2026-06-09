from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import User, Trek, Booking, StaffProfile
from app import db
from datetime import datetime

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