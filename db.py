import pymysql
from config import Config

def get_db_connection():
    """Config 클래스의 설정을 사용하여 DB 연결을 반환합니다."""
    try:
        # Config에 정의한 딕셔너리를 언패킹(**)하여 전달
        conn = pymysql.connect(**Config.get_db_config())
        return conn
    except pymysql.Error as e:
        print(f"DEBUG: 데이터베이스 연결 실패: {e}")
        raise e
