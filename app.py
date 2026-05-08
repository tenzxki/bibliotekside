from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt 
from db_conn import get_connection
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('supersecretkey')
bcrypt = Bcrypt(app)

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('role') == 'admin':
        return redirect(url_for('borrowings'))
    else:
        return redirect(url_for('browse'))






