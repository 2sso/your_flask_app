import calendar
from datetime import datetime, timedelta
from flask import render_template, request, session, flash, redirect, url_for
from db import get_db_connection
from . import todos_bp

# --- 라우트 정의 ---

@todos_bp.route('/')
def todos_list():
    """To-Do 목록 표시 및 상태/검색어 필터링"""
    if 'loggedin' not in session:
        flash('To-Do List를 보려면 로그인해야 합니다.', 'error')
        return redirect(url_for('auth.index'))

    user_id = session['id']
    status_filter = request.args.get('status', 'all').strip()
    search_query = request.args.get('query', '').strip()

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = ("SELECT id, task, DATE_FORMAT(due_date, '%%Y-%%m-%%d') AS due_date, "
                   "status, created_at FROM todos WHERE user_id = %s")
            params = [user_id]

            if status_filter != 'all':
                sql += " AND status = %s"
                params.append(status_filter)

            if search_query:
                sql += " AND task LIKE %s"
                params.append(f"%{search_query}%")

            sql += " ORDER BY created_at DESC"
            cursor.execute(sql, params)
            todos = cursor.fetchall()
    finally:
        conn.close()

    return render_template('todos_list.html', 
                           todos=todos, 
                           status_filter=status_filter, 
                           search_query=search_query,
                           all_statuses=['미완료', '진행중', '완료', '기간연장'])

@todos_bp.route('/add', methods=['POST'])
def add_todo():
    """새로운 할 일 추가"""
    if 'loggedin' not in session:
        return redirect(url_for('auth.index'))

    task = request.form.get('task', '').strip()
    due_date_str = request.form.get('due_date', '').strip()
    status = request.form.get('status', '미완료')

    if not task:
        flash('할 일 내용을 입력해주세요.', 'error')
        return redirect(url_for('todos.todos_list'))

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('날짜 형식이 올바르지 않습니다.', 'error')
            return redirect(url_for('todos.todos_list'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO todos (user_id, task, due_date, status) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (session['id'], task, due_date, status))
        conn.commit()
        flash('할 일이 추가되었습니다!', 'success')
    finally:
        conn.close()
    return redirect(url_for('todos.todos_list'))

@todos_bp.route('/update_status/<int:todo_id>/<string:new_status>', methods=['POST'])
def update_todo_status(todo_id, new_status):
    """할 일의 상태(완료 여부 등) 변경"""
    if 'loggedin' not in session:
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 본인 확인 후 업데이트
            sql = "UPDATE todos SET status = %s WHERE id = %s AND user_id = %s"
            cursor.execute(sql, (new_status, todo_id, session['id']))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('todos.todos_list'))

@todos_bp.route('/delete/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    """할 일 삭제"""
    if 'loggedin' not in session:
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM todos WHERE id = %s AND user_id = %s", (todo_id, session['id']))
        conn.commit()
        flash('삭제되었습니다.', 'success')
    finally:
        conn.close()
    return redirect(url_for('todos.todos_list'))

@todos_bp.route('/reschedule/<int:todo_id>')
@todos_bp.route('/reschedule/<int:todo_id>/<int:year>/<int:month>')
def reschedule_todo_calendar(todo_id, year=None, month=None):
    """마감일 재조정을 위한 전용 달력 표시"""
    if 'loggedin' not in session:
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, task, status FROM todos WHERE id = %s AND user_id = %s", (todo_id, session['id']))
            todo_item = cursor.fetchone()
    finally:
        conn.close()

    if not todo_item:
        flash('항목을 찾을 수 없습니다.', 'error')
        return redirect(url_for('todos.todos_list'))

    today = datetime.now()
    if year is None: year = today.year
    if month is None: month = today.month

    # 이전/다음 달 계산
    first_day = datetime(year, month, 1)
    prev_m = (first_day - timedelta(days=1)).replace(day=1)
    next_m = (first_day + timedelta(days=31)).replace(day=1)

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    return render_template('todos_reschedule.html',
                           todo_item=todo_item,
                           year=year, month=month,
                           month_name=first_day.strftime('%B'),
                           month_days=month_days,
                           prev_year=prev_m.year, prev_month=prev_m.month,
                           next_year=next_m.year, next_month=next_m.month,
                           today=today)

@todos_bp.route('/set_due_date/<int:todo_id>', methods=['POST'])
def set_new_due_date(todo_id):
    """달력에서 선택한 날짜로 마감일 업데이트"""
    if 'loggedin' not in session:
        return redirect(url_for('auth.index'))

    new_date = request.form.get('new_due_date')
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 상태 로직: 완료 항목을 재조정하면 '미완료'로, 나머지는 '진행중' 혹은 '기간연장' 유지
            cursor.execute("SELECT status FROM todos WHERE id = %s", (todo_id,))
            current = cursor.fetchone()
            new_status = '미완료' if current and current['status'] == '완료' else current['status']
            
            sql = "UPDATE todos SET due_date = %s, status = %s WHERE id = %s AND user_id = %s"
            cursor.execute(sql, (new_date, new_status, todo_id, session['id']))
        conn.commit()
        flash(f'마감일이 {new_date}로 변경되었습니다.', 'success')
    finally:
        conn.close()
    return redirect(url_for('todos.todos_list'))
