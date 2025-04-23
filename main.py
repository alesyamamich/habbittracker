from flask import Flask, render_template, request, url_for, send_from_directory, flash, redirect, jsonify
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, login_user, logout_user, LoginManager
from flask_migrate import Migrate


basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    email = StringField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class User(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True, nullable=False)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True, nullable=False)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_authenticated(self):
        return True

    def get_id(self):
        return str(self.id)

    def is_active(self):
        return(True)

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    colored_cells = db.Column(db.String(500), nullable=True)


with app.app_context():
    db.create_all()


@app.route('/')
def index():
  return render_template("index.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Пользователь с таким логином уже существует. Пожалуйста, выберите другой логин.')
            return redirect(url_for('register'))
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Вы успешно зарегистрированы!')
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Неверный логин или пароль!')
            return redirect(url_for('login'))
        else:
            flash('Вы успешно вошли в аккаунт')
            login_user(user)
            return redirect(url_for('personal'))
    return render_template('login.html', title='Вход', form=form)


@app.route('/personal', methods=['GET', 'POST'])
def personal():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if request.method == 'POST':
        habit_id = request.form.get('habit_id')
        if habit_id:
            habit = Habit.query.get(habit_id)
            if habit:
                habit.name = request.form.get('habit_name')
                habit.description = request.form.get('habit_description')
                habit.colored_cells = request.form.get('colored_cells')
                db.session.commit()
        else:
            habit_name = request.form.get('habit_name')
            habit_description = request.form.get('habit_description')
            colored_cells = request.form.get('colored_cells', '0' * 84)
            new_habit = Habit(name=habit_name, description=habit_description, colored_cells=colored_cells)
            db.session.add(new_habit)
            db.session.commit()

    habits = Habit.query.all()
    return render_template('personal.html', habits=habits)


@app.route('/delete_habit/<int:habit_id>', methods=['POST'])
def delete_habit(habit_id):
    habit = Habit.query.get(habit_id)
    if habit:
        db.session.delete(habit)
        db.session.commit()
    return redirect(url_for('personal'))


@app.route('/update_habit/<int:habit_id>', methods=['POST'])
def update_habit(habit_id):
    habit = Habit.query.get(habit_id)
    if habit is None:
        return jsonify({'error': 'Habit not found'}), 404

    # Check if the request is JSON
    if request.is_json:
        data = request.get_json()
        colored_cells = data.get('colored_cells')
        habit.colored_cells = colored_cells
    else:
        # Handle form data
        habit_name = request.form.get('habit_name')
        habit_description = request.form.get('habit_description')
        habit.name = habit_name
        habit.description = habit_description

    # Commit the changes to the database
    db.session.commit()
    return redirect(url_for('personal'))
    return jsonify({'message': 'Habit updated successfully'}), 200


@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('Вы успешно вышли из системы.')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()