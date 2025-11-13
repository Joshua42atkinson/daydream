from flask import Blueprint

bp = Blueprint('mentor', __name__, url_prefix='/api/mentor')

from . import routes
