import re
import os
from flask import render_template, request, session, flash, redirect, url_for, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection  # 공통 db 파일에서 가져옴
from . import auth_bp

# --- 헬퍼 함수 ---
def is_password_strong(password):
    """암호 복잡도 규칙(8자 이상, 대/소문자, 숫자, 특수문자 조합) 검증"""
    if len(password) < 8:
        return False
    rules = [
        any(c.isupper() for c in password),
        any(c.islower() for c in password),
        any(c.isdigit() for c in password),
        any(c in "!@#$%^&*()_+=:;\"'><.,?/[]}{" for c in password)
    ]
    return sum(rules) == 4

def is_valid_phone_number(phone_number):
    """대한민국 핸드폰 번호 형식 검증"""
    pattern = re.compile(r'^(010\d{8}|01[1,6-9]\d{7,8})$')
    return pattern.match(phone_number)

def is_admin():
    """관리자 권한 확인"""
    return 'username' in session and session['username'] in ['kevin', 'kwangjin']

# --- 라우트 정의 ---

@auth_bp.route('/')
def index():
    if 'loggedin' in session:
        return render_template('main_logged_in.html')
    return render_template('default.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    username = request.form['username'].strip()
    phone_number = request.form['phone_number'].strip()
    password = request.form['password'].strip()

    if not all([username, phone_number, password]):
        flash('모든 필드를 입력해주세요.', 'error')
        return redirect(url_for('auth.index'))

    if not is_valid_phone_number(phone_number):
        flash('올바른 핸드폰 번호 형식이 아닙니다.', 'error')
        return redirect(url_for('auth.index'))

    if not is_password_strong(password):
        flash('비밀번호 복잡도 규정을 준수하세요.', 'error')
        return redirect(url_for('auth.index'))

    hashed_password = generate_password_hash(password)
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 중복 체크
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash('이미 존재하는 아이디입니다.', 'error')
                return redirect(url_for('auth.index'))

            sql = "INSERT INTO users (username, phone_number, password) VALUES (%s, %s, %s)"
            cursor.execute(sql, (username, phone_number, hashed_password))
        conn.commit()
        flash('회원가입 성공!', 'success')
    except Exception:
        flash('서버 오류가 발생했습니다.', 'error')
    finally:
        conn.close()
    return redirect(url_for('auth.index'))

@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form['username'].strip()
    password = request.form['password'].strip()

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                session.update({
                    'loggedin': True,
                    'id': user['id'],
                    'username': user['username']
                })
                flash(f'{user["username"]}님 환영합니다!', 'success')
            else:
                flash('로그인 정보가 올바르지 않습니다.', 'error')
    finally:
        conn.close()
    return redirect(url_for('auth.index'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('로그아웃되었습니다.', 'success')
    return redirect(url_for('auth.index'))

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username'].strip()
        phone_number = request.form['phone_number'].strip()

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE username=%s AND phone_number=%s", 
                               (username, phone_number))
                if cursor.fetchone():
                    session['phone_to_reset'] = phone_number
                    return redirect(url_for('auth.reset_password'))
                flash('일치하는 정보가 없습니다.', 'error')
        finally:
            conn.close()
    return render_template('forgot_password.html')

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'phone_to_reset' not in session:
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_pw = request.form['new_password'].strip()
        if is_password_strong(new_pw):
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE users SET password=%s WHERE phone_number=%s",
                                   (generate_password_hash(new_pw), session['phone_to_reset']))
                conn.commit()
                session.pop('phone_to_reset', None)
                flash('비밀번호가 변경되었습니다.', 'success')
                return redirect(url_for('auth.index'))
            finally:
                conn.close()
        flash('비밀번호 규정을 확인하세요.', 'error')
    return render_template('reset_password.html')
