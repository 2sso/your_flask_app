from flask import Blueprint

# admin 블루프린트 생성
admin_bp = Blueprint('board', __name__, template_folder='templates/board')

from . import routes
