from flask import Blueprint

# admin 블루프린트 생성
admin_bp = Blueprint('admin', __name__, template_folder='templates/admin')

from . import routes
