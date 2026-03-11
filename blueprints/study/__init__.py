from flask import Blueprint

# diary 블루프린트 생성
diary_bp = Blueprint('study', __name__, template_folder='templates/study')

from . import routes
