from flask import Blueprint

bp = Blueprint('persona', __name__, url_prefix='/persona')

from . import routes
