from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)

    # login info
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    # demograhics
    gender = db.Column(db.String(64), index=True)
    # age, race...

    # TODO: assign groups
    group = db.Column(db.Integer)

    # relationships
    # user --> quizzes
    quizzes = db.relationship('Quiz', backref = 'user')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)

    # quiz information
    # a quiz contains four tasks.
    quiz_name = db.Column(db.String(64))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    finished = db.Column(db.Boolean)

    # relationships
    # quiz --> user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # tasks --> quiz
    tasks = db.relationship('Task', backref = 'quiz')

    def __repr__(self):
        return '<Quiz {}>'.format(self.id)


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    
    # task information
    task_name = db.Column(db.String(120)) # generated at the first time.
    task_type = db.Column(db.String(120)) # Piece Rate, Tournament, Self-Choose, Retro-Choose

    # relationships
    # task --> quiz
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'))
    # anwserRecords --> task
    answer_records =  db.relationship('AnswerRecord', backref = 'task')

    def __repr__(self):
        return '<Task {}>'.format(self.id)


class AnswerRecord(db.Model):
    __tablename__ = 'answer_records'
    id = db.Column(db.Integer, primary_key=True)

    # when a question is randomly generated during the task.
    qid = db.Column(db.Integer)
    created_time = db.Column(db.DateTime)
    a = db.Column(db.Integer)
    b = db.Column(db.Integer)
    c = db.Column(db.Integer)
    d = db.Column(db.Integer)
    e = db.Column(db.Integer)
    correct_ans = db.Column(db.Integer)

    # user action
    answer_time = db.Column(db.DateTime)
    user_ans = db.Column(db.Integer)

    # whether the user_ans is correct or not
    correct =db.Column(db.Boolean)

    # relationships
    # answer_record --> task
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))

    def __repr__(self):
        return '<AnswerRecord {}>'.format(self.id)