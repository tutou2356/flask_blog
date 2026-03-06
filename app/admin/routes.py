from flask import render_template

from . import admin_bp, admin_required
from ..models import Visit


@admin_bp.route('/admin/visits')
@admin_required
def admin_visits():
    visits = Visit.query.order_by(Visit.id.desc()).limit(200).all()
    return render_template('visits.html', visits=visits)
