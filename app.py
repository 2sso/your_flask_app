from flask import Flask, render_template, session, redirect, url_for
from config import Config
# 블루프린트 임포트 생략

app = Flask(__name__)

# Config 클래스에 정의된 설정들을 Flask 앱에 적용
app.config.from_object(Config)

# 필요한 경우 추가 설정 적용
app.secret_key = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# --- 블루프린트 등록 (Blueprint Registration) ---
# url_prefix를 설정하여 각 기능의 경로를 구분합니다.
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(board_bp, url_prefix='/board')
app.register_blueprint(diary_bp, url_prefix='/diary')
app.register_blueprint(study_bp, url_prefix='/study')
app.register_blueprint(todos_bp, url_prefix='/todos')

# --- 기본 메인 라우트 ---
@app.route('/')
def index():
    """메인 페이지: 로그인 여부에 따라 대시보드 또는 로그인 페이지로 이동"""
    if 'loggedin' in session:
        # 로그인 상태라면 각 기능에 접근할 수 있는 메인 대시보드 표시
        return render_template('index.html', username=session['username'])
    
    # 로그인 상태가 아니라면 auth 블루프린트의 로그인 페이지로 이동
    return redirect(url_for('auth.index'))

# --- 공통 에러 핸들러 ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# --- 앱 실행 ---
if __name__ == '__main__':
    # 디버그 모드: 코드 수정 시 자동 재시작 및 오류 메시지 상세 출력
    app.run(host='0.0.0.0', port=5000, debug=True)
