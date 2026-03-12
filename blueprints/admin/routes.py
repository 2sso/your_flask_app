import re
import os
import uuid
from flask import render_template, request, session, flash, redirect, url_for, jsonify, current_app
from werkzeug.utils import secure_filename
from db import get_db_connection
from . import admin_bp

# --- 헬퍼 함수 ---
def is_admin():
    """세션에 로그인된 사용자가 관리자인지 확인"""
    return 'username' in session and session['username'] in ['kevin', 'kwangjin']

def allowed_pdf_file(filename):
    """PDF 파일 확장자 검증"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}

# --- 라우트 정의 ---

@admin_bp.route('/')
def admin_dashboard():
    """관리자 메인 대시보드"""
    if not is_admin():
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('auth.index')) # auth 블루프린트의 index로 이동
    return render_template('admin_dashboard.html', username=session['username'])

@admin_bp.route('/upload_image', methods=['POST'])
def upload_image():
    """Summernote 에디터 이미지 업로드 처리"""
    if not is_admin():
        return jsonify({'error': '권한이 없습니다.'}), 403

    if 'file' not in request.files:
        return jsonify({'error': '파일이 없습니다.'}), 400

    file = request.files['file']
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        if extension not in {'png', 'jpg', 'jpeg', 'gif'}:
            return jsonify({'error': '허용되지 않는 형식입니다.'}), 400

        unique_filename = f"{uuid.uuid4()}.{extension}"
        # current_app.root_path를 사용하여 경로 설정
        save_path = os.path.join(current_app.root_path, 'static/uploads', unique_filename)

        try:
            file.save(save_path)
            url = url_for('static', filename=f'uploads/{unique_filename}')
            return jsonify({'url': url})
        except Exception as e:
            current_app.logger.error(f"Image save failed: {e}")
            return jsonify({'error': '서버 저장 오류'}), 500

@admin_bp.route('/content')
def manage_content():
    """콘텐츠 목록 관리"""
    if not is_admin():
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT c.id, c.title, c.content_type, s.name as subject_name
                FROM contents c
                JOIN subjects s ON c.subject_id = s.id
                ORDER BY s.name, c.created_at DESC
            """
            cursor.execute(sql)
            contents = cursor.fetchall()
        return render_template('manage_content.html', contents=contents)
    finally:
        conn.close()

@admin_bp.route('/add_content', methods=['GET', 'POST'])
def add_content():
    """새 콘텐츠 등록"""
    if not is_admin():
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'POST':
                storage_type = request.form.get('storage_type')
                subject_id = request.form.get('subject_id')
                content_type = request.form.get('content_type')
                title = request.form.get('title', '').strip()

                if storage_type == 'editor':
                    body = request.form.get('body', '').strip()
                    sql = "INSERT INTO contents (subject_id, content_type, storage_type, title, body, is_active) VALUES (%s, %s, %s, %s, %s, 0)"
                    cursor.execute(sql, (subject_id, content_type, storage_type, title, body))
                elif storage_type == 'pdf':
                    file = request.files.get('pdf_file')
                    if file and allowed_pdf_file(file.filename):
                        filename = secure_filename(file.filename)
                        unique_filename = f"{uuid.uuid4()}_{filename}"
                        file.save(os.path.join(current_app.root_path, 'static/pdfs', unique_filename))
                        pdf_path = f"pdfs/{unique_filename}"
                        sql = "INSERT INTO contents (subject_id, content_type, storage_type, title, pdf_path, is_active) VALUES (%s, %s, %s, %s, %s, 0)"
                        cursor.execute(sql, (subject_id, content_type, storage_type, title, pdf_path))
                
                conn.commit()
                flash('등록 성공!', 'success')
                return redirect(url_for('admin.manage_content'))

            cursor.execute("SELECT id, name FROM subjects ORDER BY name ASC")
            subjects = cursor.fetchall()
            return render_template('add_content.html', subjects=subjects)
    finally:
        conn.close()

@admin_bp.route('/subjects', methods=['GET', 'POST'])
def manage_subjects():
    """과목 관리"""
    if not is_admin():
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        if request.method == 'POST':
            name = request.form['name'].strip()
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO subjects (name) VALUES (%s)", (name,))
                conn.commit()
            return redirect(url_for('admin.manage_subjects'))

        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM subjects ORDER BY name ASC")
            subjects = cursor.fetchall()
        return render_template('manage_subjects.html', subjects=subjects)
    finally:
        conn.close()

# edit_content, delete_content, edit_subject 등 나머지 라우트들도 
# 위와 동일하게 @admin_bp.route 및 url_for('admin.xxx') 패턴으로 구현하시면 됩니다.
