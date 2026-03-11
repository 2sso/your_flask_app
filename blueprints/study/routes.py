from flask import render_template, request, session, flash, redirect, url_for, current_app
from db import get_db_connection
from . import study_bp

# --- 헬퍼 함수 ---
def is_admin():
    """세션에 로그인된 사용자가 관리자인지 확인"""
    return 'username' in session and session['username'] in ['kevin', 'kwangjin']

# --- 라우트 정의 ---

@study_bp.route('/')
def study_list():
    """전체 학습 과목 목록 표시"""
    if 'loggedin' not in session:
        flash('학습 콘텐츠를 보려면 로그인해야 합니다.', 'error')
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM subjects ORDER BY name ASC")
            subjects = cursor.fetchall()
        return render_template('study_list.html', subjects=subjects)
    finally:
        conn.close()

@study_bp.route('/<int:subject_id>')
def subject_detail(subject_id):
    """특정 과목의 이론/실습 콘텐츠 목록 표시"""
    if 'loggedin' not in session:
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 과목 정보 확인
            cursor.execute("SELECT id, name FROM subjects WHERE id = %s", (subject_id,))
            subject = cursor.fetchone()

            if not subject:
                flash('존재하지 않는 과목입니다.', 'error')
                return redirect(url_for('study.study_list'))

            # 이론 콘텐츠 조회
            cursor.execute("SELECT id, title, created_at, is_active FROM contents WHERE subject_id = %s AND content_type = '이론' ORDER BY created_at ASC", (subject_id,))
            theory_contents = cursor.fetchall()

            # 실습 콘텐츠 조회
            cursor.execute("SELECT id, title, created_at, is_active FROM contents WHERE subject_id = %s AND content_type = '실습' ORDER BY created_at ASC", (subject_id,))
            lab_contents = cursor.fetchall()

        return render_template('subject_detail.html', 
                               subject=subject, 
                               theory_contents=theory_contents, 
                               lab_contents=lab_contents)
    finally:
        conn.close()

@study_bp.route('/content/<int:content_id>')
def view_content(content_id):
    """콘텐츠 상세 내용 표시 (PDF 또는 에디터 본문)"""
    if 'loggedin' not in session:
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT c.*, s.name as subject_name 
                FROM contents c 
                JOIN subjects s ON c.subject_id = s.id 
                WHERE c.id = %s
            """
            cursor.execute(sql, (content_id,))
            content = cursor.fetchone()

            if not content:
                flash('존재하지 않는 콘텐츠입니다.', 'error')
                return redirect(url_for('study.study_list'))

            # 접근 제어: 관리자가 아니고 비활성화된 콘텐츠인 경우
            if not is_admin() and not content['is_active']:
                flash('아직 활성화되지 않은 콘텐츠입니다.', 'error')
                return redirect(url_for('study.subject_detail', subject_id=content['subject_id']))

        return render_template('view_content.html', content=content)
    finally:
        conn.close()

@study_bp.route('/content/toggle_status/<int:content_id>', methods=['POST'])
def toggle_content_status(content_id):
    """콘텐츠 활성화 상태 토글 (관리자 전용)"""
    if not is_admin():
        flash('이 작업을 수행할 권한이 없습니다.', 'error')
        return redirect(request.referrer or url_for('study.study_list'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 리다이렉트용 subject_id 조회
            cursor.execute("SELECT subject_id FROM contents WHERE id = %s", (content_id,))
            content = cursor.fetchone()
            if not content:
                flash('존재하지 않는 콘텐츠입니다.', 'error')
                return redirect(url_for('study.study_list'))

            # 상태 반전 (1->0, 0->1)
            cursor.execute("UPDATE contents SET is_active = NOT is_active WHERE id = %s", (content_id,))
            conn.commit()
            flash('콘텐츠 상태가 변경되었습니다.', 'success')
            return redirect(url_for('study.subject_detail', subject_id=content['subject_id']))
    finally:
        conn.close()
