import calendar
from datetime import datetime, timedelta
from flask import render_template, request, session, flash, redirect, url_for
from db import get_db_connection
from . import diary_bp

# --- 라우트 정의 ---

@diary_bp.route('/')
@diary_bp.route('/<int:year>/<int:month>')
def diary_calendar(year=None, month=None):
    """사용자별 월 달력 표시 및 일기 기록 여부 시각화"""
    if 'loggedin' not in session:
        flash('일기장을 보려면 로그인해야 합니다.', 'error')
        return redirect(url_for('auth.index'))

    today = datetime.now()
    if year is None: year = today.year
    if month is None: month = today.month

    # 연도 및 월 유효성 검사
    if not (1 <= month <= 12 and 1900 <= year <= 2100):
        flash('유효하지 않은 날짜입니다.', 'error')
        return redirect(url_for('diary.diary_calendar'))

    # 이전/다음 달 계산
    first_day_of_month = datetime(year, month, 1)
    prev_month_date = (first_day_of_month - timedelta(days=1)).replace(day=1)
    next_month_date = (first_day_of_month + timedelta(days=31)).replace(day=1)

    cal = calendar.Calendar(firstweekday=6)  # 일요일 시작
    month_days = cal.monthdayscalendar(year, month)

    user_id = session['id']
    diary_dates = set()

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 해당 월에 작성된 일기 날짜 목록 조회
            sql = """
                SELECT DATE_FORMAT(entry_date, '%%Y-%%m-%%d') AS date_str 
                FROM diaries 
                WHERE user_id = %s AND YEAR(entry_date) = %s AND MONTH(entry_date) = %s
            """
            cursor.execute(sql, (user_id, year, month))
            for row in cursor.fetchall():
                diary_dates.add(row['date_str'])
    finally:
        conn.close()

    return render_template('diary_calendar.html',
                           year=year, month=month,
                           month_name=first_day_of_month.strftime('%B'),
                           month_days=month_days,
                           diary_dates=diary_dates,
                           prev_year=prev_month_date.year, prev_month=prev_month_date.month,
                           next_year=next_month_date.year, next_month=next_month_date.month,
                           current_day=today.day if today.year == year and today.month == month else None)

@diary_bp.route('/entry/<string:date_str>', methods=['GET', 'POST'])
def diary_entry(date_str):
    """특정 날짜의 일기 작성 및 수정"""
    if 'loggedin' not in session:
        return redirect(url_for('auth.index'))

    user_id = session['id']
    try:
        entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('잘못된 날짜 형식입니다.', 'error')
        return redirect(url_for('diary.diary_calendar'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 기존 일기 존재 여부 확인
            cursor.execute("SELECT id, title, content FROM diaries WHERE user_id = %s AND entry_date = %s", 
                           (user_id, entry_date))
            diary = cursor.fetchone()

            if request.method == 'POST':
                title = request.form.get('title', '').strip()
                content = request.form.get('content', '').strip()

                if not content:
                    flash('내용을 입력해주세요.', 'error')
                    return render_template('diary_entry.html', diary=diary, date_str=date_str)

                if diary: # 수정 (Update)
                    sql = "UPDATE diaries SET title = %s, content = %s WHERE id = %s"
                    cursor.execute(sql, (title, content, diary['id']))
                    flash('일기가 수정되었습니다.', 'success')
                else: # 신규 작성 (Insert)
                    sql = "INSERT INTO diaries (user_id, entry_date, title, content) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, (user_id, entry_date, title, content))
                    flash('일기가 저장되었습니다.', 'success')
                
                conn.commit()
                return redirect(url_for('diary.diary_calendar', year=entry_date.year, month=entry_date.month))

    finally:
        conn.close()

    return render_template('diary_entry.html', diary=diary, date_str=date_str)
