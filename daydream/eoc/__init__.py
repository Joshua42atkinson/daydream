from flask import Blueprint

bp = Blueprint('eoc', __name__, url_prefix='/eoc')

from . import routes
