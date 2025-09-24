from flask import Blueprint

bp = Blueprint('character', __name__, url_prefix='/character')

from . import routes
