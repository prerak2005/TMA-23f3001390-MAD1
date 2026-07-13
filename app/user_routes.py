from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import Trek, Booking, User, StaffProfile
from datetime import datetime, timezone

user = Blueprint('user', __name__, url_prefix='/user')

@user.route('/dashboard')
@login_required
def dashboard():
    today = datetime.now(timezone.utc).date()

    # Active reservations only — Cancelled/Completed stay in booking_history, not the dashboard cards
    user_bookings = Booking.query.filter_by(
        user_id=current_user.id,
        booking_status='Booked'
    ).order_by(Booking.booking_date.desc()).all()

    # Treks the trekker is booked on that have not started yet
    upcoming_treks = sum(
        1 for booking in user_bookings
        if booking.trek.start_date and booking.trek.start_date > today
    )

    return render_template(
        'user/dashboard.html',
        user_bookings=user_bookings,
        upcoming_treks=upcoming_treks
    )


@user.route('/treks', methods=['GET'])
@login_required
def trek_listing():
    '''
    Display all open treks available for booking.

    Process:
    1. Query all treks with status='Open'
    2. Apply search filter by trek name (case insensitive)
    3. Sort by start_date
    4. Pass to template for display

    '''

    search_query = request.args.get('search', '').strip()

    query = Trek.query.filter(Trek.status.ilike('Open'))

    if search_query:
        query = query.filter(Trek.name.ilike(f'%{search_query}%'))

    treks = query.order_by(Trek.start_date.asc()).all()

    return render_template(
        'user/trek_listing.html',
        treks=treks,
        search_query=search_query
    )


@user.route('/booking-history', methods=['GET'])
@login_required
def booking_history():
    """
    Show all user's bookings (booked and cancelled).
    
    Process:
    1. Get all bookings for current user
    2. Sort by booking_date (newest first)
    3. Include trek info for display
    """
    
    # Get all user's bookings (any status)
    all_bookings = Booking.query.filter_by(
        user_id=current_user.id
    ).order_by(Booking.booking_date.desc()).all()
    
    return render_template(
        'user/booking_history.html',
        all_bookings=all_bookings,
        now=datetime.now(timezone.utc)
    )


@user.route('/trek/<int:id>', methods=['GET'])
@login_required
def trek_details(id):
    """
    Display detailed information for a specific trek.
    
    Process:
    1. Query trek by ID (404 if not found)
    2. Check if trek is Open
    3. Count current participants
    4. Calculate slots remaining
    5. Pass all info to template
    
    """
    
    # Get trek or show 404
    trek = Trek.query.get_or_404(id)
    
    # Only Booked rows count as current participants — Cancelled/Completed remain in booking_history
    active_bookings = Booking.query.filter_by(
        trek_id=id,
        booking_status='Booked'
    ).all()
    participant_count = len(active_bookings)
    
    # Check if current user already booked this trek
    user_booking = Booking.query.filter_by(
        user_id=current_user.id,
        trek_id=id,
        booking_status='Booked'
    ).first()
    
    return render_template(
        'user/trek_details.html',
        trek=trek,
        participant_count=participant_count,
        active_participants=active_bookings,
        user_booking=user_booking
    )


@user.route('/book-trek/<int:trek_id>', methods=['POST'])
@login_required
def book_trek(trek_id):
    '''
    
    Book a trek with comprehensive validation

    process:
    1. check trek exits
    2. check trek status
    3. check user hasn't booked this trek already
    4. check slots available 
    5. check trek start_date is in future
    6. create booking record
    7. decrement available slots by 1
    8. commit and redirect to confirmation
        
    '''

    trek = Trek.query.get(trek_id)
    # validation 1
    if not trek:
        flash("Trek not found!", "danger")
        return redirect(url_for('user.trek_listing'))
    
    # validation 2
    if trek.status.lower() != 'open':
        flash(f"This trek is currently {trek.status} and not accepting bookings","danger")
        return redirect(url_for('user.trek_details', id=trek_id))
    
    # validation 3
    if trek.available_slots <= 0:
        flash("No slots available for this trek! All slots booked", "danger")
        return redirect(url_for('user.trek_details', id=trek_id))
    
    # validation 4
    existing_booking = Booking.query.filter_by(
        user_id=current_user.id,
        trek_id=trek_id,
        booking_status='Booked'
    ).first()
    if existing_booking:
        flash("You already booked this trek! You cannot book the same trek twice.", "warning")
        return redirect(url_for('user.trek_details', id=trek_id))
    

    # validation 5
    today = datetime.now(timezone.utc).date()  # Convert to date for comparison
    if trek.start_date <= today:
        flash("This trek has already started. You cannot book it.", "danger")
        return redirect(url_for('user.trek_listing'))
    

    try:
        # create booking
        new_booking = Booking(
            user_id=current_user.id,
            trek_id=trek_id,
            booking_date=datetime.now(timezone.utc),
            booking_status='Booked',
            payment_status='Pending'
        )

        # decrement available slot by 1
        trek.available_slots -= 1

        # commit 
        db.session.add(new_booking)
        db.session.commit()

        flash(f"Successfully booked '{trek.name}'! Your trek starts on {trek.start_date.strftime('%d %b %Y')}.", "success")

        return redirect(url_for('user.booking_confirmation', booking_id=new_booking.id))
    
    except Exception as e:
        db.session.rollback()
        flash(f"Error booking trek: {str(e)}", "danger")
        return redirect(url_for('user.trek_details', id=trek_id))


@user.route('/booking-confirmation/<int:booking_id>', methods=['GET'])
@login_required
def booking_confirmation(booking_id):
    """
    Display booking confirmation page.
    
    Process:
    1. get booking by id 
    2. verify booking belongs to current user 
    3. display confirmation with trek details

    """
    
    booking = Booking.query.get_or_404(booking_id)
    
    # Security: Ensure user can only see their own bookings
    if booking.user_id != current_user.id:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('user.dashboard'))
    
    return render_template(
        'user/booking_confirmation.html',
        booking=booking
    )


@user.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """
    Cancel a booking and refund the slot.
    
    Process:
    1. Get booking by id
    2. Verify booking belongs to current user 
    3. Check if trek hasn't started yet
    4. Update booking_status to 'Cancelled'
    5. Increment available_slots by 1 
    6. Commit and redirect with success message
    
    """
    
    from datetime import datetime, timezone
    
    # Get booking or 404
    booking = Booking.query.get_or_404(booking_id)
    
    # SECURITY
    if booking.user_id != current_user.id:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('user.dashboard'))
    
    # VALIDATION 1
    if booking.booking_status != 'Booked':
        flash(f"Cannot cancel a {booking.booking_status} booking.", "warning")
        return redirect(url_for('user.booking_history'))
    
    # VALIDATION 2
    today = datetime.now(timezone.utc).date()
    if booking.trek.start_date <= today:
        flash("Cannot cancel a trek that has already started.", "danger")
        return redirect(url_for('user.booking_history'))
    
    try:
        # UPDATE BOOKING STATUS
        booking.booking_status = 'Cancelled'
        
        # REFUND THE SLOT
        booking.trek.available_slots += 1
        
        # COMMIT
        db.session.commit()
        
        # SUCCESS MESSAGE
        flash(f"Successfully cancelled booking for '{booking.trek.name}'. Slot has been refunded.", "success")
        
        return redirect(url_for('user.booking_history'))
    
    except Exception as e:
        db.session.rollback()
        flash(f"Error cancelling booking: {str(e)}", "danger")
        return redirect(url_for('user.booking_history'))