#Import Flask Library
from flask import Flask, render_template, request, session, jsonify, url_for, redirect, flash
import pymysql.cursors
import random
import hashlib


#from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


###Initialize the app from Flask
app = Flask(__name__)
app.secret_key = "secret key"

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 8889,
                       user='root',
                       password='root',
                       db='foodzillaFinal',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/postRecipe')
def postRecipe():
    return render_template('postRecipe.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    salt = "salt2022"
    db_password = password + salt
    hahsed_pass = hashlib.md5(db_password.encode()).hexdigest()


    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE userName = %s and password = %s'
    cursor.execute(query, (username, hahsed_pass))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    salt = "salt2022"
    db_password = password + salt
    hahsed_pass = hashlib.md5(db_password.encode()).hexdigest()
    fName = request.form['fName']
    lName = request.form['lName']
    email = request.form['email']
    profile = request.form['profile']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, hahsed_pass, fName, lName, email, profile))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    try:
        user = session['username']
    except:
        return render_template('index.html')

    else:
        cursor = conn.cursor()
        #get user profile
        query = 'SELECT profile FROM Person WHERE username = %s'
        cursor.execute(query, (user))
        prof = cursor.fetchone()['profile']
        #get recipes posted
        query2 = 'SELECT recipeID, title FROM Recipe WHERE postedBy = %s'
        cursor.execute(query2, (user))
        recipesPosted = cursor.fetchall()
        #get groups belong in 
        query3 = 'SELECT gName FROM GroupMembership WHERE memberName = %s'
        cursor.execute(query3, (user))
        groupMembership = cursor.fetchall()
        cursor.close()
        return render_template('home.html', username=user, profile=prof, recipesPosted = recipesPosted, groups = groupMembership)

@app.route('/searchSimilarUser')
def searchSimilarUser():
    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT Review2.userName FROM Review AS Review1 JOIN Review AS Review2 USING (recipeID) WHERE Review1.userName = %s AND Review2.stars = Review1.stars AND NOT Review2.userNAme = %s'
    cursor.execute(query, (user, user))
    similar_users = cursor.fetchall()
    cursor.close()
    list_of_similar_users = []
    for similar in similar_users:
        list_of_similar_users.append(similar['userName'])
    return render_template('similar_users.html', users = list_of_similar_users, username = user)

@app.route('/review', methods=['GET', 'POST'])
def review():
    try:
        user = session['username']
    except:
        error = "Not logged in, please log in to post a review"
        return render_template('error.html', error = error)

    else:
        userName = request.form['userName']
        recipeID = request.form['recipeID']
        revTitle = request.form['revTitle']
        stars = request.form['stars']
        revDesc = request.form['revDesc'].strip()
        cursor = conn.cursor()
        query = 'INSERT INTO Review VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(query, (userName, recipeID, revTitle, revDesc, stars))
        conn.commit()
        cursor.close()
        sucess = "sucessfully submitted a review for recipe " + str(recipeID) 
        return render_template('sucess.html', sucess = sucess)

@app.route('/search')
def search():
    cursor = conn.cursor()
    query = 'SELECT DISTINCT tagText FROM RecipeTag'
    cursor.execute(query)
    search_tag_results = cursor.fetchall()
    cursor.close()
    tag_list = []
    for item in search_tag_results:
        tag_list.append(item['tagText'])
    return render_template('search.html', tags = tag_list)

@app.route('/searching', methods=['GET', 'POST'])
def searching():
    tag = request.form['chosen_tag']
    cursor = conn.cursor()
    query = 'SELECT DISTINCT recipeID, title FROM RecipeTag NATURAL JOIN RECIPE WHERE tagText = %s'
    cursor.execute(query, (tag))
    recipe_results = cursor.fetchall()
    cursor.close()
    list_of_recipes = []
    recipe_names = []
    for recipe in recipe_results:
        list_of_recipes.append(recipe['recipeID'])
        recipe_names.append(recipe['title'])
    mixed = list(zip(list_of_recipes, recipe_names))
    return render_template("selectRecipes.html", recipes = mixed)

@app.route('/showRecipes', methods=['GET', 'POST'])
def showRecipes():
    try:
        username = session['username']
    except:
        username = None
    finally:
        recipeID = request.form['chosen_recipe']
        cursor = conn.cursor()
        query1 = "SELECT * FROM RECIPE WHERE recipeID = %s"
        query2 = "SELECT stepNo, sDesc FROM Step WHERE recipeID = %s"
        query4 = 'SELECT userName, revTitle, revDesc, stars FROM Review WHERE recipeID = %s'
        cursor.execute(query1, (recipeID))
        recipeInfo = cursor.fetchall()[0]
        cursor.execute(query2, (recipeID))
        stepInfo = cursor.fetchall()
        cursor.execute(query4, (recipeID))
        reviews = cursor.fetchall()
        cursor.close()
        steps = []
        for step in stepInfo:
            steps.append(tuple((step['stepNo'], step['sDesc'])))
        return render_template("displayRecipes.html", info = recipeInfo, steps = steps, username = username, reviews = reviews)

@app.route('/submitRecipeAuth', methods=['GET', 'POST'])
def submitRecipeAuth():
    #grabs information from the forms
    title = request.form['title']
    servings = int(request.form['numServings'])
    posted_by = session['username']
    tags = request.form['tags'].split(" ")
    steps = request.form['steps'].strip().splitlines()
    ingredients = request.form['ingredient'].strip().splitlines()
    recipeID = random.randint(1,500) * random.randint(1,15) + random.randint(1,5)

    cursor = conn.cursor()
    query = 'INSERT INTO Recipe VALUES(%s, %s, %s, %s)'
    cursor.execute(query, (recipeID, title, servings, posted_by))
    conn.commit()
    counter = 1
    #parse steps
    for step in steps:
        query = 'INSERT INTO Step VALUES(%s, %s, %s)'
        cursor.execute(query, (counter, recipeID, step))
        conn.commit()
        counter += 1
    #parse tags
    for tag in tags:
        query = 'INSERT INTO RecipeTag VALUES(%s, %s)'
        cursor.execute(query, (recipeID, tag.lower()))
        conn.commit()
    #parse ingredients
    for ingredient in ingredients:
        #if ingredient name has multiple words make sure to put that together before moving on
        item = ingredient.split(" ")
        iName = []
        for i in item:
            try:
                float(i)
            except:
                iName.append(i)
            else:
                break
        final_iName = ""
        print(iName)
        for name in iName:
            item.remove(name)
            final_iName += name
            final_iName += " "
        final_iName.strip()
        print("here")
        print(item)
        print(final_iName)
        
        #check if in ingredient table if not add to ingreient table then add to recipe ingredient
        cursor = conn.cursor()
        #executes query
        queryCheck = 'SELECT * FROM Ingredient WHERE iName = %s'
        cursor.execute(queryCheck, (final_iName.lower()))
        isIngredient = cursor.fetchone()
        #if ingredient exist insert into recipe ingredient table
        if(isIngredient):
            query2 = 'INSERT INTO RecipeIngredient VALUES(%s, %s, %s, %s)'
            cursor.execute(query2, (recipeID, final_iName.lower(), item[1].lower(), item[0]))
            conn.commit()
        #if ingredient doesnt exist check if its unit exists
        else:
            queryUnit = 'Select * FROM Unit WHERE unitName = %s'
            cursor.execute(queryUnit, (item[1].lower()))
            unitExists = cursor.fetchone()
            if(unitExists): #insert into ingredients and recipe ingredients table
                query1 = 'Insert INTO Ingredient VALUES(%s, %s)'
                cursor.execute(query1, (final_iName.lower(), None))
                query2 = 'INSERT INTO RecipeIngredient VALUES(%s, %s, %s, %s)'
                cursor.execute(query2, (recipeID, final_iName.lower(), item[1].lower(), item[0]))
                conn.commit()
            else: #insert units table and recipe and recipe ingredients table
                query1 = 'Insert INTO Unit VALUES(%s)'
                cursor.execute(query1, (item[1].lower()))
                query2 = 'Insert INTO Ingredient VALUES(%s, %s)'
                cursor.execute(query2, (final_iName.lower(), None))
                query3 = 'INSERT INTO RecipeIngredient VALUES(%s, %s, %s, %s)'
                cursor.execute(query3, (recipeID, final_iName.lower(), item[1].lower(), item[0]))
                conn.commit()

    cursor.close()

    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)