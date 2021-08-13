from app import app
from flask import render_template, request, redirect, url_for, session, g, flash
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegistrationForm, QuestionForm
from app.models import User, Quiz, Task, AnswerRecord
from app import db
import random
from datetime import datetime 



@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        g.user = user

@app.route('/')
def home():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            return redirect(url_for('login'))
        # session is shared across different pages
        session['user_id'] = user.id
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
        # return redirect(url_for('home'))
    if g.user:
        return redirect(url_for('home'))
    return render_template('login.html', form=form, title='Login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data) # fix the error.
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('home'))
    if g.user:
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)



# TODO: add question id
@app.route('/question<int:qid>', methods=['GET', 'POST'])
def question(qid):
    form = QuestionForm()

    if not g.user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # answer_time
        answer_record_id = session['answer_record_id']
        answer_record = AnswerRecord.query.filter_by(id = answer_record_id).first()
        answer_record.answer_time = datetime.now()
        
        # user_ans
        answer = int(request.form['answer'])
        answer_record.user_ans = answer

        # correct or not
        answer_record.correct = True if answer == answer_record.correct_ans else False

        db.session.add(answer_record)
        db.session.commit()

        return redirect(url_for('question', qid=(qid+1)))
    
    a, b, c, d, e = [random.randint(10,99) for i in range(5)]
    print(a, b, c, d, e)
    correct_ans = sum([a, b, c, d, e])
    answer_record = AnswerRecord(qid = qid, a=a, b=b, c=c, d=d, e=e, correct_ans = correct_ans, created_time = datetime.now())


    db.session.add(answer_record)
    db.session.commit()

    session['answer_record_id'] = answer_record.id


    # quiz = session.get('quiz')
    # if not quiz:
    #     quiz = Quiz(quiz_name = 'Quiz-Try')
    #     session['quiz'] = quiz

    # task = session.get('task')
    # if not task:
    #     task = Task(task_name = 'Task-Try')
    #     session['task'] = task

    return render_template('question.html', 
                           form=form,
                           qid=qid, 
                           a=a, b=b, c=c, d=d, e=e,
                           title='Question {}'.format(qid))


@app.route('/score')
def score():
    if not g.user:
        return redirect(url_for('login'))
    g.user.marks = session['marks']
    # db.session.commit()
    return render_template('score.html', title='Final Score')

@app.route('/logout')
def logout():
    if not g.user:
        return redirect(url_for('login'))
    session.pop('user_id', None)
    session.pop('marks', None)
    return redirect(url_for('home'))