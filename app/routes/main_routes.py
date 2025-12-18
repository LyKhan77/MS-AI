"""
Main HTML page routes
Renders dashboard, settings, and other web pages
"""

from flask import Blueprint, render_template

bp = Blueprint('main', __name__)


@bp.route('/')
@bp.route('/dashboard')
def dashboard():
    """Main dashboard page with video feed and counting controls"""
    return render_template('dashboard.html')


@bp.route('/analysis')
def analysis():
    """Defect analysis page"""
    return render_template('analysis.html')


@bp.route('/settings')
def settings():
    """Settings and configuration page"""
    return render_template('settings.html')


@bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')
