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