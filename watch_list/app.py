import os
import click
from flask import Flask, url_for, render_template, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False;
app.config['SECRET_KEY'] = 'HU'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'If you are admin, do that after login please.'

'''
---------------------------------
define database table Model area
---------------------------------
'''
class User(db.Model, UserMixin):
	'''
	创建数据库模型(相当于数据库中的: create table)
	默认数据库中的表名为类名的小写: user
	'''
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(20))
	username = db.Column(db.String(20))
	password_hash = db.Column(db.String(128))

	def set_password(self, password):
		'''
		密码不能明文保存在数据库中，
		需要保存它自动生成的哈希值。
		'''
		self.password_hash = generate_password_hash(password)

	def validate_password(self, password):
		'''
		通过用户输入的密码，与数据库中保存的哈希
		进行哈希运算，验证密码的正确性。
		'''
		return check_password_hash(self.password_hash, password)

class Movie(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(60))
	year = db.Column(db.String(4))




@login_manager.user_loader
def load_user(user_id):
	user = User.query.first()
	return user



'''
----------------------
define my command area
----------------------
'''
@app.cli.command()
# @click.option('__drop', is_flag=True, help='Create after drop.')
def initdb():
	# if drop:
	db.drop_all()
	db.create_all()
	click.echo('Initialized database.')

@app.cli.command()	# 生成虚拟数据
def forge():
	db.drop_all()
	db.create_all()
	name = 'Mr hu' 
	movies = [
		{'title': 'My Neighbor Totoro',	'year':	'1988'},
		{'title': 'Dead Poets Society',	'year':	'1989'},
		{'title': 'A Perfect World', 'year': '1993'},
		{'title': 'Leon', 'year': '1994'},
		{'title': 'Mahjong', 'year': '1996'},
		{'title': 'Swallowtail Butterfly', 'year':	'1996'},
		{'title': 'King	of Comedy', 'year': '1999'},
		{'title': 'Devils	on the Doorstep', 'year': '1999'},
		{'title': 'WALL-E',	'year':	'2008'},
		{'title': 'The	Pork	of	Music',	'year':	'2012'},
		{'title': 'ONE PIECE', 'year': '1999'}
	]
	user = User(name=name)
	db.session.add(user)
	for movie_item in movies:
		movie = Movie(title=movie_item['title'], year=movie_item['year'])
		db.session.add(movie)
	db.session.commit()
	click.echo('Done')

@app.cli.command()
@click.option('--username', prompt=True, help='The username useed to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
	db.create_all()
	user = User.query.first()
	if user is not None:
		click.echo('Updating user...')
		user.username = username
		user.set_password(password)
	else:
		click.echo('Creating user...')
		user = User(username=username, name='Admin')
		user.set_password(password)
		db.session.add(user)
	db.session.commit()
	click.echo('Done')


'''
---------------------
define view functions
---------------------
'''
@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == 'GET':
		movies = Movie.query.all()
		return render_template('index.html', movies=movies)		
	title = request.form.get('title')
	year = request.form.get('year')
	if not title or not year or len(year) > 4 or len(title) > 60:
		flash('Invalid input')
		return redirect(url_for('index'))
	if Movie.query.filter_by(title=title).first():
		flash('Item existed.')
		return redirect(url_for('index'))
	movie = Movie(title=title, year=year)
	db.session.add(movie)
	db.session.commit()
	flash('Item created')
	return redirect(url_for('index'))	


@app.route('/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit(movie_id):
	item = Movie.query.get_or_404(movie_id)
	if request.method == 'GET':
		return render_template('edit.html', movie=item)		
	if not current_user.is_authenticated:
		return redirect(url_for('login'))
	title = request.form.get('title')
	year = request.form.get('year')
	if not title or not year or len(year) > 4 or len(title) > 60:
		flash('Invalid input.')
		return redirect(url_for('edit', movie_id=movie_id))
	item.title = title
	item.year = year
	db.session.commit()
	flash('Item update.')
	return redirect(url_for('index'))

@login_required
@app.route('/delete/<int:movie_id>', methods=['POST'])
def delete(movie_id):
	movie = Movie.query.get_or_404(movie_id)
	db.session.delete(movie)
	db.session.commit()
	flash('Item deleted.')
	return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')
	username = request.form['username']
	password = request.form['password']
	if not username or not password:
		flash('Invalid input.')
		return redirect(url_for('login'))
	user = User.query.first()
	if username == user.username and user.validate_password(password):
		login_user(user)
		flash('Login success.')
		return redirect(url_for('index'))
	flash('Invalid username or password')
	return redirect(url_for('login'))
	
@app.route('/logout')
@login_required
def logout():
	logout_user()
	flash('Goodbye.')
	return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
	if request.method == 'GET':
		return render_template('settings.html')
	name = request.form['name']
	if not name or len(name) > 20:
		flash('Invalid input')
		return redirect(url_for('settings'))
	current_user.name = name
	db.session.commit()
	flash('Settings updated.')
	return redirect(url_for('index'))

'''
------------------
define error page
------------------
'''
@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

'''
define templates context variable
'''
@app.context_processor
def inject_user():
	user = User.query.first()
	return {'user':user} #must be a dict