import os
from dotenv import load_dotenv, find_dotenv

# .env 파일 로드
load_dotenv(find_dotenv())

class Config:
    """Flask 앱 공통 설정"""
    # 기본 보안 설정
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default-secret-key-1234')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    # 세션 설정
    PERMANENT_SESSION_LIFETIME = 1800  # 30분 (초 단위)

    # 데이터베이스 설정 (pymysql용)
    DB_HOST = os.getenv('DB_HOST', '192.168.0.13')
    DB_USER = os.getenv('DB_USER', 'flask_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'P@ssw0rd')
    DB_NAME = os.getenv('DB_NAME', 'flask_auth_db')
    DB_CHARSET = 'utf8mb4'
    
    # PyMySQL DictCursor 설정을 위한 딕셔너리 변환 메서드
    @classmethod
    def get_db_config(cls):
        import pymysql
        return {
            'host': cls.DB_HOST,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'db': cls.DB_NAME,
            'charset': cls.DB_CHARSET,
            'cursorclass': pymysql.cursors.DictCursor
        }
