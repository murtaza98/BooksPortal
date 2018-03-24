from flask import Flask,request,render_template,flash,redirect,url_for,session,logging
from flask_mysqldb import MySQL
from wtforms import Form ,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

app=Flask(__name__)

#config MySQL
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='books_users'
app.config['MYSQL_CURSORCLASS']='DictCursor'
#initialize MYSQL
mysql=MySQL(app)

@app.route('/')
def home():
	return render_template('home.html')

#register form class
class RegisterForm(Form):
	name=StringField('Name',[validators.Length(min=1,max=50)],render_kw={"placeholder": "Enter your Name"})
	username=StringField('Username',[validators.Length(min=4,max=25)],render_kw={"placeholder": "Enter your username"})
	email=StringField('Email',[validators.Length(min=6,max=50)],render_kw={"placeholder": "Enter your email"})
	password=PasswordField('Password',[
		validators.DataRequired(),
		validators.EqualTo('confirm',message='Password do not match'),
	],render_kw={"placeholder": "Enter your Password"})
	confirm=PasswordField('Confirm Password',render_kw={"placeholder": "Confirm your Password"})


@app.route('/register',methods=['GET','POST'])
def register():
	form=RegisterForm(request.form)
	if(request.method=='POST' and form.validate()):
		cur=mysql.connection.cursor()
		name=form.name.data
		username=form.username.data
		email=form.email.data
		password=sha256_crypt.encrypt((str(form.password.data)))
		cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)",[name,email,username,password])
		mysql.connection.commit()
		cur.close()

		flash('You are now registered and can LOG IN','success')

		return redirect(url_for('register'))

	return render_template('register.html',form=form)





if __name__ =='__main__':
	app.secret_key="secret123"
	app.run(debug=True)
