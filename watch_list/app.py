from flask import Flask, url_for

app = Flask(__name__)


@app.route('/hello')
@app.route('/')
def index():
	return '<img src="http://helloflask.com/totoro.gif">'

# 增加无参路由
@app.route('/user')
@app.route('/user/<username>')
# 在试图函数中添加参数默认值
def user_page(username="hu"):
	return 'Welcome %s' % username

@app.route('/test_url_for')
def test_url_for():
	return '<p> %s </p>' % url_for('user_page')