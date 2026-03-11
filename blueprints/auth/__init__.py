from flask import Blueprint

# auth 블루프린트 생성 (템플릿 폴더 경로 지정)
auth_bp = Blueprint('auth', __name__, template_folder='templates/auth')

from . import routes
