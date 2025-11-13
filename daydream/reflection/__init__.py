from flask import Blueprint

bp = Blueprint('reflection', __name__, url_prefix='/api/reflection')

from . import routes
