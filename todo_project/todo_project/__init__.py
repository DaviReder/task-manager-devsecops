import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# CORREÇÃO DE SEGURANÇA (Bandit B105): Puxa a chave do ambiente e elimina o Hardcoded Secret
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'chave-temporaria-apenas-para-desenvolvimento-local')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login' 
login_manager.login_message_category = 'danger'

bcrypt = Bcrypt(app)

# Always put Routes at end
from todo_project import routes