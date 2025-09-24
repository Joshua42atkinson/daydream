from flask import Blueprint

bp = Blueprint('journal', __name__, url_prefix='/journal')

from . import routes
