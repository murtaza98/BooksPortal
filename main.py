from flask import Flask,request,render_template,flash,redirect,url_for,session,logging
from flask_mysqldb import MySQL
from wtforms import Form ,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.utils import secure_filename
import os
from flask_uploads import UploadSet, configure_uploads, IMAGES
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from werkzeug.utils import secure_filename
from data import Products


app=Flask(__name__)

#config MySQL
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='books_users'
app.config['MYSQL_CURSORCLASS']='DictCursor'
#initialize MYSQL
mysql=MySQL(app)
#configure uploads

UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif','PNG','JPG','JPEG','GIF'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def home():
	return render_template('home.html')

@app.route('/about')
def about():
	return render_template('about.html')

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

def is_logged_in(f):
	@wraps(f)
	def wrap(*args,**kwargs):
		if('logged_in' in session):
			return f(*args,**kwargs)
		else:
			flash('Unauthorized, Please login','danger')
			return redirect(url_for('login'))
	return wrap


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

		return redirect(url_for('login'))

	return render_template('register.html',form=form)


@app.route('/login',methods=['GET','POST'])
def login():
	if(request.method=='POST'):
		username=request.form['username']
		password_candidate=request.form['password']

		cur=mysql.connection.cursor()
		result=cur.execute('SELECT * FROM users WHERE username= %s',[username])

		if(result>0):
			data=cur.fetchone()
			password=data['password']

			if(sha256_crypt.verify(password_candidate,password)):
				app.logger.info('Password matched')

				session['logged_in']=True
				session['username']=username
				session['name']=data['NAME']

				flash('You are now logged in','success')

				return redirect(url_for('dashboard'))
			else:
				error='Incorrect Password'
				return render_template('login.html',error=error)
		else:
			error='No User with the specified username found'
			return render_template("login.html",error=error)
		cur.close()
	return render_template('login.html')

@app.route('/dashboard')
@is_logged_in
def dashboard():
	return render_template('dashboard.html')


class ProductRegistration(Form):
	name=StringField('Name',[validators.Length(min=1,max=50)],render_kw={"placeholder": "Product Name"})
	num_regex='^[0-9]*$'
	price=StringField('Price',[validators.Regexp(num_regex, message='Invalid input')],render_kw={'placeholder':'Selling Price'})
	description=TextAreaField('Description',[validators.Length(min=1)],render_kw={"placeholder": "Product Description"})
	category=StringField('Category',[validators.Length(min=1,max=50)],render_kw={"placeholder": "Product Category"})
	#image=FileField ('Images',validators=[FileRequired()])
	stock=StringField('Available Books',[validators.Regexp(num_regex, message='Invalid input')],render_kw={'placeholder':'Number of books you wish to sell'})
	#image=FileField()

def allowed_file(filename):
	return '.' in filename and \
			filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/sell_book',methods=['GET','POST'])
@is_logged_in
def sell_book():
	form=ProductRegistration(request.form)
	#app.logger.info(form.image.data)

	if(request.method =='POST' and form.validate()):
		cur=mysql.connection.cursor()
		name=form.name.data
		price=form.price.data
		description=form.description.data
		category=form.category.data
		stock=form.stock.data
		#image upload logic
		image = request.files['image']
		app.logger.info(image.filename)
		filename=''
		if image and allowed_file(image.filename):
			app.logger.info("inside")
			filename = secure_filename(image.filename)
			image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		else:
			flash('Error uploading image,Please check the image format.','danger')
			return render_template('sell_book.html',form=form)

		imagename = filename


		cur.execute("INSERT INTO products(username,product_name,product_description,product_price,product_category,product_image,in_stock) VALUES(%s,%s,%s,%s,%s,%s,%s)",[session['username'],name,description,price,category,filename,stock])
		mysql.connection.commit()
		cur.close()
		flash('Product saved','success')
		return redirect(url_for('sell_book'))

	return render_template('sell_book.html',form=form)


@app.route('/products')
def products():
	#products=Products()
	cur=mysql.connection.cursor()
	result=cur.execute('SELECT * FROM products')
	products=cur.fetchall()
	if(result>0):
		return render_template('products.html',products=products)
	else:
		msg='No products found'
		return render_template('products.html',msg=msg)
	cur.close()	

@app.route('/product/<string:id>/')
def product(id):
	cur=mysql.connection.cursor()
	result=cur.execute('SELECT * FROM products WHERE id=%s',[id])
	product=cur.fetchone()
	return render_template('product.html',product=product)

	

@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are now logged out','success')
	return redirect(url_for('login'))







if __name__ =='__main__':
	app.secret_key="secret123"
	app.run(debug=True)


