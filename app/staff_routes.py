from flask import Blueprint, render_template
from flask_login import login_required

staff = Blueprint('staff', __name__, url_prefix='/staff')

@staff.route('/dashboard')
@login_required
def dashboard():
    return render_template('staff/dashboard.html')