import os
from flask import Flask, session, redirect, url_for, render_template
from config import Config  # DB_CONFIG 대신 전체 설정을 담은 Config 클래스 권장

def create_app():
    app = Flask(__name__)
    
    # 1. 공통 설정 적용 (Secret Key 등이 없으면 세션/로그인이 안 됩니다!)
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY 

    # 2. 환경 변수에서 서비스 이름 가져오기
    service_name = os.getenv('SERVICE_NAME', 'auth')
    print(f"--- Starting {service_name} Service ---")

    # 3. 서비스별 Blueprint 동적 등록
    # [주의] __init__.py에 정의했다면 .routes 생략 가능 (구조에 따라 맞춤)
    if service_name == 'auth':
        from blueprints.auth.routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        
    elif service_name == 'admin':
        from blueprints.admin.routes import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        
    elif service_name == 'board':
        from blueprints.board.routes import board_bp
        app.register_blueprint(board_bp, url_prefix='/board')
        
    elif service_name == 'diary':
        from blueprints.diary.routes import diary_bp
        app.register_blueprint(diary_bp, url_prefix='/diary')
        
    elif service_name == 'todos':
        from blueprints.todos.routes import todos_bp
        app.register_blueprint(todos_bp, url_prefix='/todos')
        
    elif service_name == 'study':
        from blueprints.study.routes import study_bp
        app.register_blueprint(study_bp, url_prefix='/study')

    # 4. 루트 경로 설정 (매우 중요!)
    # 각 컨테이너가 '/' 접속 시 어디로 보낼지 결정합니다.
    @app.route('/')
    def index():
        if 'loggedin' in session:
            # 로그인 상태면 메인(index.html)을 보여주거나 각 서비스 메인으로 이동
            return render_template('index.html', username=session.get('username'))
        
        # 로그인 안 되어 있으면 auth 서비스의 index(로그인창)로 이동
        # MSA 환경에서는 외부 도메인이나 Ingress 주소로 리다이렉트가 필요할 수 있습니다.
        return redirect(url_for(f'{service_name}.index'))

    return app

if __name__ == "__main__":
    app = create_app()
    # 쿠버네티스 환경이므로 debug 모드는 꺼두는 것이 보안상 좋습니다.
    app.run(host='0.0.0.0', port=5000)
