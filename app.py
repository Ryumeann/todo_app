#道具箱を持ってくる
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

#道具箱を開いて準備する
app = Flask(__name__)

#データベースの設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'#データベースの場所を指定
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False#変更追跡機能のONまたはOFF
db = SQLAlchemy(app)

#タスクモデルの定義
class Task(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  content = db.Column(db.String(200), nullable=False)
  done = db.Column(db.Boolean, default=False)
  created_date = db.Column(db.DateTime, default=datetime.utcnow)
  
#データベースの作成
with app.app_context():
     db.create_all()  

#トップページの入り口とタスク追加機能を作る
@app.route('/', methods=['GET','POST'])
def index():
  if request.method == 'POST':
     task_content = request.form['content']
     if task_content.strip():#空白のタスクは追加しない
       #タスクをデータベースに追加
        new_task = Task(content=task_content)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('index')) 
      
  tasks = Task.query.order_by(Task.created_date.desc()).all()
  return render_template('index.html', tasks=tasks)


#削除機能のための新しい入り口を作る
@app.route('/delete/<int:task_id>', methods=['POST'])#Flaskは関数名からURLを生成
def delete_task(task_id):
  task = Task.query.get_or_404(task_id)#idを使って削除するタスクを検索
  db.session.delete(task)#データベースから削除
  db.session.commit()#データベースに変更を保存
  return redirect(url_for('index'))


#完了機能のための新しい入り口を作る 
@app.route('/toggle/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    # idを使ってトグルするタスクを検索
    task = Task.query.get_or_404(task_id)
    # 完了状態を反転（True→False、False→True）
    task.done = not task.done
    # 変更を保存
    db.session.commit()
    return redirect(url_for('index'))
  
#タスク編集機能
@app.route('/edit/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    if request.method == 'POST':
        task = Task.query.get_or_404(task_id)
        new_content = request.form['new_content']
        
        if new_content.strip():
           #タスク内容を更新
           task.content = new_content.strip()
           #変更を保存
           db.session.commit()
    return redirect(url_for('index'))
    
  

#お店を開く準備(サーバー起動)
if __name__ == '__main__':
    app.run(debug=True)