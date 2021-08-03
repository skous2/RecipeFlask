
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import numpy as np
import pandas as pd

app = Flask(__name__)

#Run command: set FLASK_APP=main.py
#Run command: set FLASK_DEBUG=1
#Run command: flask run

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Retalhuleu11'
app.config['MYSQL_DB'] = 'pythonlogin'

# Intialize MySQL
mysql = MySQL(app)

def convert(row):
    #print(row)
    return '<a href={0} target="_blank">{0}</a>'.format(row)

def find_ingredient(searchvals, ing_list):
    return all([any(val in string for string in ing_list) for val in searchvals])

master = pd.read_csv(r'https://elasticbeanstalk-us-west-2-511853890245.s3.us-west-2.amazonaws.com/recipes_master.csv')
master = master.reset_index(drop=True)
master.Ingredients = master.Ingredients.str.replace("'","").str.strip('][').str.split(', ')
#master.Link = master.Link.apply(convert)
#df = master.loc[:,['Blog','Recipe','Link','Time']].head(50)
df = master
# http://localhost:5000/pythonlogin/ - this will be the login page, we need to use both GET and POST requests
@app.route('/FlaskTest/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = 'Whoops something went wrong'
        # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
                # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('index.html', msg='')

# http://localhost:5000/python/logout - this will be the logout page
@app.route('/FlaskTest/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/FlaskTest/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
                # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route('/FlaskTest/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:

        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# http://localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for loggedin users
@app.route('/FlaskTest/profile', methods=['GET', 'POST'])
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:

        if request.method == 'POST':
            print('Editing Database')
            checkedblogs = request.form.getlist('people')
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('DELETE FROM userblog WHERE userID = %s', (session['id'],))
            mysql.connection.commit()
            for checkedblog in checkedblogs:
                cursor.execute('INSERT INTO userblog VALUES ((SELECT blogID FROM blog WHERE blogName = %s),%s)', (checkedblog, session['id'],))
                mysql.connection.commit()

        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()

        cursor.execute('SELECT blogName FROM blog JOIN userblog ON blog.blogID = userblog.blogID WHERE userID = %s ORDER BY blogName', (session['id'],))
        usersblogs = cursor.fetchall()
        userbloglist = [row['blogName'] for row in usersblogs]

        cursor.execute('SELECT blogName FROM blog')
        allblogs = cursor.fetchall()
        allbloglist = [row['blogName'] for row in allblogs]

        otherlist = sorted(set(allbloglist) - set(allbloglist).intersection(set(userbloglist)))
        print(otherlist)

        # Show the profile page with account info
        return render_template('profile.html', account=account, users_blogs=userbloglist, other_blogs=otherlist)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/FlaskTest/pantry', methods=['GET', 'POST'])
def pantry():
    # Check if user is loggedin
    if 'loggedin' in session:
        print(request.form)
        if request.method == 'POST' and 'add' in request.form:
            addedFood = request.form.get('NewIngredient')
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT COUNT(*) AS num FROM food WHERE foodName = %s', (addedFood,))
            foodexists = cursor.fetchone()
            print(foodexists['num'])
            if foodexists['num'] == 0:
                cursor.execute('INSERT INTO food (idFood, foodName, foodExp) VALUES (NULL,%s,21)', (addedFood,))
                mysql.connection.commit()
            cursor.execute('SELECT COUNT(pantry.idFood) AS pantrynum FROM pantry JOIN food ON food.idFood = pantry.idFood WHERE foodName = %s', (addedFood,))
            pantryexists = cursor.fetchone()
            if pantryexists['pantrynum'] == 0:
                cursor.execute('INSERT INTO pantry VALUES(%s,(SELECT idFood FROM food WHERE foodName = %s), curdate())', (session['id'], addedFood,))
                mysql.connection.commit()

        if request.method == 'POST' and 'remove' in request.form:
            checkedfoods = request.form.getlist('food')
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            for checkedfood in checkedfoods:
                cursor.execute('DELETE FROM pantry WHERE idUser = %s AND idFood = (SELECT idFood FROM food WHERE foodName = %s)', (session['id'],checkedfood))
                mysql.connection.commit()
                print(checkedfood)

        if request.method == 'POST' and 'search' in request.form:
            print(request.form.getlist('food'))
            searchfoods = [food.lower() for food in request.form.getlist('food')]

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT blogName FROM blog JOIN userblog ON blog.blogID = userblog.blogID WHERE userID = %s ORDER BY blogName', (session['id'],))
            usersblogs = cursor.fetchall()
            userbloglist = [row['blogName'] for row in usersblogs]

            length = len(df.loc[df.Ingredients.apply(lambda x: find_ingredient(searchfoods, x)) & (master.Blog.isin(userbloglist)), ['Blog', 'Recipe', 'Link', 'Time']].sort_values('Time').reset_index(drop = True))


            return render_template('recipesearch.html', length = length, searchlist = searchfoods, username=session['username'], tables=[df.loc[df.Ingredients.apply(lambda x: find_ingredient(searchfoods, x)) & (master.Blog.isin(userbloglist)), ['Blog', 'Recipe', 'Link', 'Time']].sort_values('Time').reset_index(drop = True).to_html(formatters={'Link':lambda x:f'<a href="{x}" target="_blank">{x}</a>'}, index = False, escape=False, classes='data', header="true")])


        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT foodName, DATE(dateAdded) AS DateAdded, DATE(DATE_ADD(dateAdded, INTERVAL foodExp DAY)) AS ExpirationDate, DATEDIFF(DATE_ADD(dateAdded, INTERVAL foodExp DAY), curdate()) AS DaysLeft FROM pantry JOIN food ON pantry.idFood = food.idFood WHERE idUser = %s ORDER BY DaysLeft ASC', (session['id'],))
        pantryFoods = cursor.fetchall()
        print(pantryFoods)

        # Show the pantry page 
        return render_template('pantry.html', output_data=pantryFoods)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

    # SELECT 
    # foodName,
    # DATE(dateAdded),
    # DATE(DATE_ADD(dateAdded, INTERVAL foodExp DAY)) AS ExpirationDate, 
    # DATEDIFF(DATE_ADD(dateAdded, INTERVAL foodExp DAY), dateAdded) AS DaysLeft FROM pantry
    # JOIN food ON pantry.idFood = food.idFood;

@app.route('/FlaskTest/recipesearch', methods=['GET', 'POST'])
def recipesearch():
    # Check if user is loggedin
    if 'loggedin' in session:
        if request.method == 'GET':
            return f"The URL /recipesearch is accessed directly. Try going to '/home' to submit form"
        if request.method == 'POST':
            form_data = request.form
            print(form_data.values())
            searchlist = list(form_data.values())
            searchlist = [value.lower() for value in searchlist]
            searchlist = searchlist[:-1]
            print(searchlist)
            ing1 = form_data['Ingredient1']
            ing2 = form_data['Ingredient2']
            ing3 = form_data['Ingredient3']
            ing4 = form_data['Ingredient4']
            titlesearch = form_data['Title'].lower()
            
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT blogName FROM blog JOIN userblog ON blog.blogID = userblog.blogID WHERE userID = %s ORDER BY blogName', (session['id'],))
            usersblogs = cursor.fetchall()
            userbloglist = [row['blogName'] for row in usersblogs]

            length = len(df.loc[df.Ingredients.apply(lambda x: find_ingredient(searchlist, x)) & (master.Recipe.str.lower().str.find(titlesearch) > -1) & (master.Blog.isin(userbloglist)), ['Blog', 'Recipe', 'Link', 'Time']].sort_values('Time').reset_index(drop = True))
            

        #return render_template('data.html',form_data = form_data)
        
        # User is loggedin show them the home page
        return render_template('recipesearch.html', length = length, searchlist = searchlist, username=session['username'], tables=[df.loc[df.Ingredients.apply(lambda x: find_ingredient(searchlist, x)) & (master.Recipe.str.lower().str.find(titlesearch) > -1) & (master.Blog.isin(userbloglist)), ['Blog', 'Recipe', 'Link', 'Time']].sort_values('Time').reset_index(drop = True).to_html(formatters={'Link':lambda x:f'<a href="{x}" target="_blank">{x}</a>'}, index = False, escape=False, classes='data', header="true")])

    # User is not loggedin redirect to login page
    return redirect(url_for('register'))

print('Testing')