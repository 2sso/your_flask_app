from flask import Blueprint

# todos 블루프린트 생성
todos_bp = Blueprint('todos', __name__, template_folder='templates/todos')

from . import routes
