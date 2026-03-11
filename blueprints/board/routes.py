from flask import render_template, request, session, flash, redirect, url_for
from db import get_db_connection
from . import board_bp

# --- 라우트 정의 ---

@board_bp.route('/')
def board_list():
    """검색 기능을 포함한 게시글 목록 표시"""
    if 'loggedin' not in session:
        flash('게시판을 보려면 로그인해야 합니다.', 'error')
        return redirect(url_for('auth.index'))

    search_query = request.args.get('query', '').strip()
    conn = get_db_connection()
    posts = []
    
    try:
        with conn.cursor() as cursor:
            # 유저 테이블과 조인하여 작성자 이름(username)을 가져옴
            sql = ("SELECT b.id, b.title, b.content, b.created_at, b.updated_at, u.username "
                   "FROM board b JOIN users u ON b.user_id = u.id")
            params = []

            if search_query:
                sql += " WHERE b.title LIKE %s OR b.content LIKE %s"
                params.extend([f"%{search_query}%", f"%{search_query}%"])

            sql += " ORDER BY b.created_at DESC"
            cursor.execute(sql, params)
            posts = cursor.fetchall()
    finally:
        conn.close()
    
    return render_template('board_list.html', posts=posts, search_query=search_query)

@board_bp.route('/write', methods=['GET', 'POST'])
def write_post():
    """새 게시글 작성"""
    if 'loggedin' not in session:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        user_id = session.get('id')

        if not title or not content:
            flash('제목과 내용은 비워둘 수 없습니다.', 'error')
            return redirect(url_for('board.write_post'))

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO board (user_id, title, content) VALUES (%s, %s, %s)"
                cursor.execute(sql, (user_id, title, content))
            conn.commit()
            flash('게시글이 작성되었습니다.', 'success')
            return redirect(url_for('board.board_list'))
        finally:
            conn.close()
            
    return render_template('write_post.html')

@board_bp.route('/view/<int:post_id>')
def view_post(post_id):
    """게시글 상세보기 및 댓글 목록"""
    if 'loggedin' not in session:
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 게시글 조회
            cursor.execute("SELECT b.*, u.username FROM board b JOIN users u ON b.user_id = u.id WHERE b.id = %s", (post_id,))
            post = cursor.fetchone()

            if not post:
                flash('존재하지 않는 게시글입니다.', 'error')
                return redirect(url_for('board.board_list'))

            # 댓글 조회
            cursor.execute("SELECT c.*, u.username FROM comments c JOIN users u ON c.user_id = u.id WHERE c.board_id = %s ORDER BY c.created_at ASC", (post_id,))
            comments = cursor.fetchall()
    finally:
        conn.close()
        
    return render_template('view_post.html', post=post, comments=comments)

@board_bp.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    """게시글 수정 (본인 확인 포함)"""
    if 'loggedin' not in session:
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM board WHERE id = %s", (post_id,))
            post = cursor.fetchone()

            if not post or post['user_id'] != session.get('id'):
                flash('수정 권한이 없습니다.', 'error')
                return redirect(url_for('board.view_post', post_id=post_id))

            if request.method == 'POST':
                title = request.form.get('title', '').strip()
                content = request.form.get('content', '').strip()
                cursor.execute("UPDATE board SET title=%s, content=%s WHERE id=%s", (title, content, post_id))
                conn.commit()
                flash('수정되었습니다.', 'success')
                return redirect(url_for('board.view_post', post_id=post_id))
    finally:
        conn.close()
        
    return render_template('edit_post.html', post=post)

@board_bp.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    """게시글 삭제"""
    if 'loggedin' not in session:
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM board WHERE id = %s", (post_id,))
            post = cursor.fetchone()
            if post and post['user_id'] == session.get('id'):
                cursor.execute("DELETE FROM board WHERE id = %s", (post_id,))
                conn.commit()
                flash('삭제되었습니다.', 'success')
            else:
                flash('삭제 권한이 없습니다.', 'error')
    finally:
        conn.close()
    return redirect(url_for('board.board_list'))

@board_bp.route('/comment/add/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    """댓글 등록"""
    if 'loggedin' not in session:
        return redirect(url_for('auth.index'))

    content = request.form.get('content', '').strip()
    if not content:
        return redirect(url_for('board.view_post', post_id=post_id))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO comments (board_id, user_id, content) VALUES (%s, %s, %s)"
            cursor.execute(sql, (post_id, session.get('id'), content))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('board.view_post', post_id=post_id))
