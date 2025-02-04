# 必要なモジュールのインポート
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from pathlib import Path
import os

# Flaskアプリケーションの設定
application = Flask(__name__)
app = application

# ユーザーセッション用の秘密鍵の生成と読み込み
def generate_secret_key():
    try:
        key_file = Path('instance/secret_key.txt')
        key_file.parent.mkdir(exist_ok=True)
        
        if not key_file.exists():
            secret_key = secrets.token_urlsafe(32)
            key_file.write_text(secret_key)
            return secret_key
        
        return key_file.read_text()
    except Exception as e:
        # ファイル操作に失敗した場合のフォールバック
        return secrets.token_urlsafe(32)

# データベースの設定
app.config['SECRET_KEY'] = generate_secret_key()  # ユーザーのセッション用の秘密鍵をFlaskに設定
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "todo.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# データベースとログインマネージャーの初期化
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# instanceディレクトリの作成
os.makedirs('instance', exist_ok=True)

# データベースモデルの定義
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# データベースの初期化
with app.app_context():
    db.create_all()

# ユーザー認証関連の関数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 新規ユーザー登録
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        if not username or not password:
            flash('ユーザー名とパスワードを入力してください')
            return redirect(url_for('register'))
        
        # ユーザー名の重複チェック
        if User.query.filter_by(username=username).first():
            flash('このユーザー名は既に使用されています')
            return redirect(url_for('register'))
        
        # 新規ユーザーの作成
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# ユーザーログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        if not username or not password:
            flash('ユーザー名とパスワードを入力してください')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('ユーザー名またはパスワードが間違っています')
    return render_template('login.html')

# ログアウト
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# タスク管理関連の関数
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        task_content = request.form['content'].strip()
        if task_content:
            new_task = Task(content=task_content, user_id=current_user.id)
            db.session.add(new_task)
            db.session.commit()
        else:
            flash('タスクの内容を入力してください')
        return redirect(url_for('index'))
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_date.desc()).all()
    return render_template('index.html', tasks=tasks)

# タスク削除
@app.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('他のユーザーのタスクは削除できません')
        return redirect(url_for('index'))
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

# タスクのチェック判定
@app.route('/toggle/<int:task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('他のユーザーのタスクは変更できません')
        return redirect(url_for('index'))
    task.done = not task.done
    db.session.commit()
    return redirect(url_for('index'))

# タスクを編集
@app.route('/edit/<int:task_id>', methods=['POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('他のユーザーのタスクは編集できません')
        return redirect(url_for('index'))
    if request.method == 'POST':
        new_content = request.form['new_content'].strip()
        if new_content:
            task.content = new_content
            db.session.commit()
        else:
            flash('タスクの内容を入力してください')
    return redirect(url_for('index'))

# アプリケーションの実行
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
