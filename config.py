import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tma-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///tma.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False