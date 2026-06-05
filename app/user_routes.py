from flask import Blueprint, render_template
from flask_login import login_required

user = Blueprint('user', __name__, url_prefix='/user')

@user.route('/dashboard')
@login_required
def dashboard():
    return render_template('user/dashboard.html')