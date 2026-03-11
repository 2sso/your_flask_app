from flask import Blueprint

# diary 블루프린트 생성
diary_bp = Blueprint('diary', __name__, template_folder='templates/diary')

from . import routes
