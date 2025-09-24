from flask import Blueprint
from .core import calculate_xp, AWL_WORDS, AWL_DEFINITIONS

bp = Blueprint('vocabulary', __name__, template_folder='templates')

from . import routes