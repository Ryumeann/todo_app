from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


application = Flask(__name__)
app = application

# データベースの設定（お店の住所を決めるようなもの）
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# タスクの設計図（お客様の注文票のようなもの）
class Task(db.Model):
    # 注文番号のようなもの。重複しない固有の番号
    id = db.Column(db.Integer, primary_key=True)
    # タスクの内容（注文内容）を保存。最大200文字まで
    content = db.Column(db.String(200), nullable=False)
    # タスクが完了したかどうか（注文が完了したかどうか）を記録
    done = db.Column(db.Boolean, default=False)
    # タスクを作成した日時（注文を受けた時間）を記録
    created_date = db.Column(db.DateTime, default=datetime.utcnow)


# お店をオープンする準備（データベースの初期化）
with app.app_context():
    db.create_all()


# トップページの設定（お店の入口のような場所）
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 新しいタスクを受け取る（お客様から新しい注文を受けるイメージ）
        task_content = request.form['content']
        if task_content.strip():
            new_task = Task(content=task_content)
            # データベースに保存（注文票をキッチンに渡すイメージ）
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for('index'))
    # すべてのタスクを表示（注文一覧を見るイメージ）。新しい順に並べる
    tasks = Task.query.order_by(Task.created_date.desc()).all()
    return render_template('index.html', tasks=tasks)


# タスクを削除する機能（注文をキャンセルするイメージ）
@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))


# タスクを完了にする機能（注文が完成したときにチェックを付けるイメージ）
@app.route('/toggle/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.done = not task.done
    db.session.commit()
    return redirect(url_for('index'))


# タスクを編集する機能（注文内容を変更するイメージ）
@app.route('/edit/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    if request.method == 'POST':
        task = Task.query.get_or_404(task_id)
        new_content = request.form['new_content']
        if new_content.strip():
            task.content = new_content.strip()
            db.session.commit()
    return redirect(url_for('index'))


# プログラムを実行する（お店を開店する）
if __name__ == '__main__':
    app.run(debug=True)
