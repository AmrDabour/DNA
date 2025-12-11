"""
Static Pages Routes - Privacy Policy, Terms of Use, Contact
"""
from flask import Blueprint, render_template

pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/privacy-policy')
def privacy_policy():
    """Render the Privacy Policy page"""
    return render_template('privacy_policy.html')


@pages_bp.route('/terms-of-use')
def terms_of_use():
    """Render the Terms of Use page"""
    return render_template('terms_of_use.html')


@pages_bp.route('/contact')
def contact():
    """Render the Contact page"""
    return render_template('contact.html')




