from app import app
from flask import render_template, request, redirect, url_for, session, g, flash
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegistrationForm, QuestionForm
from app.models import User, Quiz, Task, AnswerRecord
from app import db
import random
from datetime import date, datetime 


MAX_QID = 5
GROUP_SIZE = 4
TID2TASKTYPE = {
    1: 'Piece Rate',
    2: 'Tournament',
    3: 'Your Choice',
    4: 'Look Back',
}


CLEARLIST = ['qid', 'tid', 'answer_record.id', 'user_id']

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


    g.task = None 
    if 'task.id' in session:
        task = Task.query.filter_by(id=session['task.id']).first()
        g.task = task

    
    # qid is within a task
    g.qid = None
    if 'qid' in session:
        g.qid = session.get('qid', 1)

    # tid is within a quiz
    g.tid = None
    if 'tid' in session:
        g.tid = session.get('tid', 1)

    

@app.route('/')
def home():
    return render_template('index.html', title='EconField')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        
        for i in CLEARLIST: 
            if i in session: session.pop(i)

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
        for i in CLEARLIST: 
            if i in session: session.pop(i)
        return redirect(url_for('home'))
    return render_template('login.html', form=form, title='Login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    print(session)
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, 
                    gender=form.gender.data, 
                    state=form.state.data, 
                    schoolyear=form.schoolyear.data, 
                    email=form.email.data) # fix the error.
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # add group info
        session['user.id'] = user.id
        group = int(user.id - 1 / GROUP_SIZE) + 1
        user.group = group
        db.session.add(user)
        db.session.commit()

        for i in CLEARLIST: 
            if i in session: session.pop(i)

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
    
    
    for i in CLEARLIST: 
        if i in session: session.pop(i)
    
    return redirect(url_for('home'))


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    print(session)
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
        flash('You start a new quiz [{}] now! TID is {}'.format(g.quiz.quiz_name, g.tid))

    # extract tid from session
    if 'tid' not in session:
        session['tid'] = 1

    tid = session['tid'] # exist under a quiz
    return render_template('quiz.html', title='Question {}'.format(g.quiz.quiz_name), tid = tid)


@app.route('/task-start', methods=['GET', 'POST'])
def task_start():
    # print(session)
    flash('You are starting a task now')

    # generate a quiz, and a quiz id
    tid = session['tid']
    task_type = TID2TASKTYPE[tid]
    task_name = 'Q{}T{}:u{}'.format(g.quiz.quiz_name, task_type, g.user.username)
    
    dt = datetime.now()
    task = Task(task_name = task_name, task_type = task_type, quiz = g.quiz, start_time = dt)
    
    db.session.add(task)
    db.session.commit()
    
    g.task = task
    
    session['task.id'] = task.id
    
    if session['tid'] in [1, 2]:
        session['qid'] = 1
    elif session['tid'] in [3, 4]:
        session['qid'] = 0
    else:
        flash('Somehow, you are in trouble')

    if session['tid'] in [1, 2, 3]:
        col = 'rightnum{}'.format(session['tid'])
        print(col)
        session[col] = 0

    if session['tid'] in [3, 4]:
        session['choice{}'.format(session['tid'])] = None

    # print(session)
    return redirect(url_for('question'))


@app.route('/task-end', methods=['GET', 'POST'])
def task_end():
    print(session)

    dt = datetime.now()
    flash('Congrats! You current task is finished!')
    task = g.task 
    task.end_time = dt 
    
    if session['tid'] in [1, 2]:
        task.final_status = TID2TASKTYPE[session['tid']] 

    db.session.add(task)
    db.session.commit()    

    session.pop('task.id')
    # session.pop('answer_record.id')

    if session['tid'] in [1, 2]:
        session['qid'] = 1
    elif session['tid'] in [3, 4]:
        session['qid'] = 0
    else:
        flash('Somehow, you are in trouble')
    
    session['tid'] = session['tid'] + 1

    return redirect(url_for('quiz'))



@app.route('/task3-choice/<choice>', methods=['GET', 'POST'])
def task3_choice(choice):
    # print(session)

    if not g.user:
        return redirect(url_for('login'))

    if not g.quiz:
        flash('No such quiz')
        return redirect(url_for('quiz'))

    if not g.task:
        flash('No such task')
        return redirect(url_for('quiz'))

    assert g.task.task_type == TID2TASKTYPE[3]
    assert session['tid'] == 3
    session['qid'] = 1

    dt = datetime.now()
    
    task = g.task
    task.start_time = dt 
    if choice == 'choice1':
        task.final_status = TID2TASKTYPE[1]
    elif choice == 'choice2':
        task.final_status = TID2TASKTYPE[2]

    db.session.add(task)
    db.session.commit()    

    session['choice{}'.format(session['tid'])] = task.final_status 
    print('choice{}'.format(session['tid']), session['choice{}'.format(session['tid'])])

    # session.pop('quiz.id')
    return redirect(url_for('question'))


@app.route('/quiz-task-end/<choice>', methods=['GET', 'POST'])
def quiz_task_end(choice):
    # print(session)

    if not g.user:
        return redirect(url_for('login'))

    if not g.quiz:
        flash('No such quiz')
        return redirect(url_for('quiz'))

    if not g.task:
        flash('No such task')
        return redirect(url_for('quiz'))

    assert g.task.task_type == TID2TASKTYPE[4]
    assert session['tid'] == 4

    dt = datetime.now()
    
    task = g.task
    task.end_time = dt 
    if choice == 'choice1':
        task.final_status = TID2TASKTYPE[1]
    elif choice == 'choice2':
        task.final_status = TID2TASKTYPE[2]

    session['choice{}'.format(session['tid'])] = task.final_status 
    print('choice{}'.format(session['tid']), session['choice{}'.format(session['tid'])])

    quiz = g.quiz 
    quiz.end_time = dt 
    quiz.finished = True 

    db.session.add(task)
    db.session.add(quiz)
    db.session.commit()    

    # session.pop('quiz.id')
    return redirect(url_for('results'))


@app.route('/results', methods=['GET', 'POST'])
def results():
    if not g.user:
        return redirect(url_for('login'))

    if not g.quiz:
        flash('No such quiz')
        return redirect(url_for('quiz'))

    if not g.task:
        flash('No such task')
        return redirect(url_for('quiz'))

    rightnum1 = session.get('rightnum1', None)
    rightnum2 = session.get('rightnum2', None)
    rightnum3 = session.get('rightnum3', None)
    choice3 = session.get('choice3', None)
    choice4 = session.get('choice4', None)
    
    return render_template('results.html', rightnum1 =rightnum1, rightnum2 = rightnum2, 
                            rightnum3 = rightnum3, choice3 = choice3, choice4 = choice4, MAX_QID = MAX_QID)


@app.route('/question', methods=['GET', 'POST'])
def question():
    # print(session)
    
    if not g.user:
        return redirect(url_for('login'))

    if not g.quiz:
        flash('No such quiz')
        return redirect(url_for('quiz'))

    if not g.task:
        flash('No such task')
        return redirect(url_for('quiz'))

    if 'generate_new_question' not in session:
        session['generate_new_question'] = True 

    if 'qid' not in session:
        session['qid'] = 1

    assert 'tid' in session
    tid = session['tid']
    # answer_record = AnswerRecord.query.filter_by(id = answer_record_id).first()

    form = QuestionForm()
    # flash('Output is {}, {}, {}'.format(form.validate_on_submit(), form.answer, type(form.answer.data)))
    
    if request.method == 'POST' and type(form.answer.data) == int:
        # answer_time
        # answer_record_id = session['answer_record.id']
        # answer_record = AnswerRecord.query.filter_by(id = answer_record_id).first()
        qid = session['qid']
        a, b, c, d, e = session['integers']
        correct_ans = session['correct_ans']
        created_time = session['created_time']

        answer_time = datetime.now()
        
        # user_ans
        # print(request.form['answer']
        # flash('Output is {}'.format(request.form['answer']))
        user_ans = int(request.form['answer'])

        # correct or not
        correct = True if user_ans == correct_ans else False

        session['rightnum{}'.format(session['tid'])] += int(correct)

        print('rightnum{}'.format(session['tid']), session['rightnum{}'.format(session['tid'])])

        # g.task
        answer_record = AnswerRecord(qid = qid, a=a, b=b, c=c, d=d, e=e, correct_ans = correct_ans, 
                                     created_time = created_time, answer_time = answer_time, user_ans = user_ans,
                                     correct = correct, task = g.task)

        db.session.add(answer_record)
        db.session.commit()

        # update qid
        session['qid'] += 1
        session['generate_new_question'] = True
        # print('Currrent QID is {}'.format(session['qid'] ))

        new_qid = session['qid']
        if new_qid <= MAX_QID:
            return redirect(url_for('question'))
        else:
            return redirect(url_for('task_end'))
    
    else:
        # maybe new, maybe refresh
        # don't make it refresh.
        qid = session['qid'] # by default, it is zero.
        
        if session['generate_new_question'] == True or 'answer_record.id' not in session:
            # finish_current_question interpret it as the last question.
            a, b, c, d, e = [random.randint(10,99) for i in range(5)]
            # print(a, b, c, d, e)
            correct_ans = sum([a, b, c, d, e])
            created_time = datetime.now()
            # answer_record = AnswerRecord(qid = qid, a=a, b=b, c=c, d=d, e=e, correct_ans = correct_ans, created_time = created_time)
            # db.session.add(answer_record)
            # db.session.commit()

            session['integers'] = a, b, c, d, e
            session['correct_ans'] = correct_ans
            session['created_time'] = created_time

            # session['answer_record.id'] = answer_record.id

            session['generate_new_question'] = False
        else:
            # keep using the current question
            flash('You are still in this question: {}'.format(qid))
            # answer_record_id = session['answer_record.id']
            # answer_record = AnswerRecord.query.filter_by(id = answer_record_id).first()
            # answer_record.answer_time = datetime.now()
            a, b, c, d, e = session['integers'] # answer_record.a, answer_record.b, answer_record.c, answer_record.d, answer_record.e
            
        return render_template('question.html', 
                                form=form,
                                qid=qid, 
                                a=a, b=b, c=c, d=d, e=e, tid = tid,
                                title='Question {}'.format(qid))

