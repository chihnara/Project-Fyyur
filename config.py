import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
DB_USER = 'postgres'
DB_PWD = 'postgres'
DB_HOST = 'localhost'
DB_NAME = 'fyyur'
DB_PORT = '5432'

SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
SQLALCHEMY_TRACK_MODIFICATIONS = False
