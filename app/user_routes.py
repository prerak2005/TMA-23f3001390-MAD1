from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import Trek, Booking, User, StaffProfile
from datetime import datetime

user = Blueprint('user', __name__, url_prefix='/user')

@user.route('/dashboard')
@login_required
def dashboard():
    return render_template('user/dashboard.html')


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
        all_bookings=all_bookings
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
    
    # Get all bookings for this trek (for participant count)
    bookings = Booking.query.filter_by(trek_id=id).all()
    participant_count = len(bookings)
    
    # Check if current user already booked this trek
    user_booking = Booking.query.filter_by(
        user_id=current_user.id,
        trek_id=id
    ).first()
    
    return render_template(
        'user/trek_details.html',
        trek=trek,
        participant_count=participant_count,
        user_booking=user_booking
    )