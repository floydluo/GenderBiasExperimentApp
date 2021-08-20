from app import app
from flask import render_template, request, redirect, url_for, session, g, flash
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegistrationForm, QuestionForm
from app.models import User, Quiz, Task, AnswerRecord
from app import db
import random
from datetime import datetime 


MAX_QID = 20


@app.before_request
def before_request():
    g.user = None
    if 'user.id' in session:
        user = User.query.filter_by(id=session['user.id']).first()
        g.user = user
    
    g.quiz = None 
    if 'quiz.id' in session:
        quiz = Quiz.query.filter_by(id=session['quiz.id']).first()
        g.quiz = quiz

    g.current_task_type = None
    if 'current_task_type' in session:
        g.current_task_type = session.get('current_task_type', 1)


    g.task = None 
    if 'task.id' in session:
        task = Task.query.filter_by(id=session['task.id']).first()
        g.task = task

    
    g.qid = None
    if 'qid' in session:
        g.qid = session.get('qid', 1)

    
    

@app.route('/')
def home():
    return render_template('index.html', title='EconField')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            print(form.username.data)
            flash('Sorry You are not in the Database')
            # print('User is not correct: {}'.format(user.username))
            return redirect(url_for('login'))
        # session is shared across different pages
        session['user.id'] = user.id
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
        session['user.id'] = user.id
        return redirect(url_for('home'))
    if g.user:
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route('/logout')
def logout():
    if not g.user:
        return redirect(url_for('login'))
    if g.user:
        session.pop('user.id', None)
        g.user = None
    if g.quiz:
        session.pop('quiz.id', None)
        g.quiz = None
    if g.task:
        session.pop('task.id', None)
        g.task = None
    return redirect(url_for('home'))


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if not g.user:
        return redirect(url_for('login'))

    if g.quiz:
        flash('You are already in a quiz [{}] now!'.format(g.quiz.quiz_name))

    else:
        dt = datetime.now()
        quiz_name = 'Quiz for {} at {}'.format(g.user.username, str(dt).split('.')[0])
        start_time = dt 
        quiz = Quiz(quiz_name = quiz_name, start_time = start_time, user = g.user)

        db.session.add(quiz)
        db.session.commit()

        # start it in the session.
        session['quiz.id'] = quiz.id
        g.quiz= quiz

        flash('You start a new quiz [{}] now!'.format(g.quiz.quiz_name))


        

    return render_template('quiz.html', title='Question {}'.format(g.quiz.quiz_name))


@app.route('/task-start', methods=['GET', 'POST'])
def task_start():
    flash('You are starting a task now')

    # generate a quiz, and a quiz id
    task_type = g.current_task_type
    task_name = 'Q{}T{}:u{}'.format(g.quiz.quiz_name, task_type, g.user.username)
    task = Task(task_name = task_name, task_type = task_type, quiz = quiz)
    g.task = task
    
    session['task.id'] = task.id
    session['question.id'] = 1 # start from 1

    return redirect(url_for('question'))


@app.route('/task-end', methods=['GET', 'POST'])
def task_end():
    flash('Congrats! You current task is finished!')
    # session['task.id'] +=1
    # session['question.id'] = 1 # start from 1

    # clear current task and question information
    # session['task.id'] = None
    session.pop('task.id')
    session.pop('question.id')
    # g.task = None
    # session['question.id'] = None

    

    return redirect(url_for('quiz'))


@app.route('/question', methods=['GET', 'POST'])
def question():
    

    if not g.user:
        return redirect(url_for('login'))

    if not g.quiz:
        return redirect(url_for('quiz'))

    # if not g.task: # TODO
    #     return redirect(url_for('quiz'))

    if 'generate_new_question' not in session:
        session['generate_new_question'] = True 

    if 'qid' not in session:
        session['qid'] = 1
    

    form = QuestionForm()

    flash('Output is {}, {}, {}'.format(form.validate_on_submit(), form.answer, type(form.answer.data)))
    if request.method == 'POST' and type(form.answer.data) == int:
        # answer_time
        answer_record_id = session['answer_record.id']
        answer_record = AnswerRecord.query.filter_by(id = answer_record_id).first()
        answer_record.answer_time = datetime.now()
        
        # user_ans
        # print(request.form['answer']
        # flash('Output is {}'.format(request.form['answer']))
        answer = int(request.form['answer'])
        answer_record.user_ans = answer

        # correct or not
        answer_record.correct = True if answer == answer_record.correct_ans else False

        db.session.add(answer_record)
        db.session.commit()

        # update qid
        session['qid'] += 1
        session['generate_new_question'] = True
        print('Currrent QID is {}'.format(session['qid'] ))

        new_qid = session['qid']
        if new_qid <= MAX_QID:
            return redirect(url_for('question'))
        else:
            return redirect(url_for('task_end'))
    
    else:
        # maybe new, maybe refresh
        # don't make it refresh.
        qid = session['qid'] # by default, it is zero.
        
        if session['generate_new_question'] == True:
            # finish_current_question interpret it as the last question.
            a, b, c, d, e = [random.randint(10,99) for i in range(5)]
            # print(a, b, c, d, e)
            correct_ans = sum([a, b, c, d, e])
            answer_record = AnswerRecord(qid = qid, a=a, b=b, c=c, d=d, e=e, correct_ans = correct_ans, created_time = datetime.now())
            db.session.add(answer_record)
            db.session.commit()

            session['answer_record.id'] = answer_record.id
            session['generate_new_question'] = False
        else:
            # keep using the current question
            flash('You are still in this question: {}'.format(qid))
            answer_record_id = session['answer_record.id']
            answer_record = AnswerRecord.query.filter_by(id = answer_record_id).first()
            # answer_record.answer_time = datetime.now()
            a, b, c, d, e = answer_record.a, answer_record.b, answer_record.c, answer_record.d, answer_record.e
            


        return render_template('question.html', 
                            form=form,
                            qid=qid, 
                            a=a, b=b, c=c, d=d, e=e,
                            title='Question {}'.format(qid))

