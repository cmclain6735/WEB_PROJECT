from flask import Flask, render_template, request, flash, redirect, url_for, session, json, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta  # Used to set session time, perm


# from flask_login import login_user, logout_user, login_required, current_user


# Create Flask APP
def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'kfdsjahfkdjsh dkjsahfksld'

    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'KodaBlue1!'
    app.config['MYSQL_DB'] = 'task'
    # converts from string to dictionary
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
    # set session life time
    app.permanent_session_lifetime = timedelta(minutes=15)

    return app


# Instance of Flask APP
app = create_app()

# Instance of MySQL DB
mysql = MySQL(app)


# Create MySQL DB in MySQL server


# ------ ROUTES
#   Index
@app.route('/', methods=['GET'])
def index():
    return render_template('login.html')


#   Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    # data = request.form
    # print(data)
    if request.method == 'POST':
        # Open Connection
        cur = mysql.connection.cursor()

        # Get data input in form
        email = request.form.get('email')
        password = request.form.get('password')

        # Get saved data in DB to match with
        select_stmt = """SELECT email, password FROM user WHERE email = %(email)s AND password = %(password)s """
        cur.execute(select_stmt, {'email': email, 'password': password})
        user = cur.fetchall()

        if user:
            if user[0]['password'] == password:
                # flash("You are logged in.", category='success')
                # Define THIS session as permanent defined above
                session.permanent = True
                session['user'] = user
                return redirect(url_for('home'))
            else:
                flash("Incorrect password, try again.", category='error')
        else:
            flash("User Not Found.", category='error')
            return render_template('login.html')

        # Close the db connection
        cur.close()

    if request.method == 'GET':
        if "user" in session:
            return redirect(url_for('home'))

    return render_template('login.html')


#   Sign Up
@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':

        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        role = request.form.get('role')
        print(role)

        password_hash = generate_password_hash(password1, method='sha256')
        user_data = (email, password1, first_name, role)

        # Open Connection
        cur = mysql.connection.cursor()
        select_stmt = """SELECT email FROM user WHERE email = %(email)s """
        cur.execute(select_stmt, {'email': email})
        user = cur.fetchall()
        # Close the cursor connection

        if user:
            flash("User already exists", category='error')
        elif len(email) <= 4:
            flash("Email must be greater than 4 characters.", category='error')
        elif len(first_name) <= 2:
            flash("First name must be greater than 2 characters.", category='error')
        elif role == '':
            flash("Please select a user role.", category='error')
        elif password1 != password2:
            flash("Passwords don\'t match", category='error')
        elif len(password1) < 7:
            flash("Password must be at least 7 characters.", category='error')
        else:
            # add user to DB
            cur.execute('''INSERT INTO user VALUES (%s, %s, %s, %s)''', user_data)
            mysql.connection.commit()
            cur.close()
            flash("Account created!", category='success')
            return redirect(url_for('login'))

    return render_template('sign_up.html')


#   Logout
@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for('login'))


@app.route('/home', methods=['GET', "POST"])
def home():
    if "user" in session:
        if request.method == 'GET':
            # Open Connection
            cur = mysql.connection.cursor()

            # snapshot user object
            user = session['user']
            print(session)
            # print(user)

            # parse user name from user object
            user_name = user[0]['email']
            print(user_name)

            # get user role from DB
            select_role = """SELECT role FROM user WHERE email = %(user_name)s """
            cur.execute(select_role, {'user_name': user_name})
            role_obj = cur.fetchall()
            user_role = role_obj[0]['role']
            print(user_role)

            # get firstname of user from user db
            select_first_name = """SELECT first_name FROM user WHERE email = %(user_name)s """
            cur.execute(select_first_name, {'user_name': user_name})
            first_name_obj = cur.fetchall()
            first_name = first_name_obj[0]['first_name']
            # print(first_name)

            if user_role == 'User':
                # get list of open tasks for user
                select_open_task_list = """SELECT task_num, task, status, description FROM task WHERE assigned_to = %(first_name)s AND status != 'Closed' """
                cur.execute(select_open_task_list, {'first_name': first_name})
                open_task_list = cur.fetchall()
                # print(task_list)

                # get list of closed tasks for user
                select_closed_task_list = """SELECT task_num, task, status, description FROM task WHERE assigned_to = %(first_name)s AND status = 'Closed' """
                cur.execute(select_closed_task_list, {'first_name': first_name})
                closed_task_list = cur.fetchall()
                # print(task_list)

                return render_template('home.html', first_name=first_name, open_task_list=open_task_list, closed_task_list=closed_task_list)

            if user_role == "Boss":
                return redirect(url_for('boss'))

    return render_template("login.html")


@app.route('/task', methods=['GET', 'POST'])
def task():
    if "user" in session:
        #     if request.method == 'GET':
        # Open Connection
        cur = mysql.connection.cursor()

        # snapshot user object
        user = session['user']
        # print(user)
        # parse user name from user object
        user_name = user[0]['email']
        # print(user_name)

        # get role of user from user db
        select_role = """SELECT role FROM user WHERE email = %(user_name)s """
        cur.execute(select_role, {'user_name': user_name})
        role_obj = cur.fetchall()
        role = role_obj[0]['role']
        # print(role)

        # get firstname of user from user db
        select_first_name = """SELECT first_name FROM user WHERE email = %(user_name)s """
        cur.execute(select_first_name, {'user_name': user_name})
        first_name_obj = cur.fetchall()
        first_name = first_name_obj[0]['first_name']
        # print(first_name)

        # Get Task Number from form body
        task_number = request.form.get('taskNum')
        # print(task_number)

        # get task detail of task from task table
        select_task = """SELECT status, priority, start_date, assigned_to, target_date, description, task FROM task WHERE task_num = %(tempTaskNum)s """
        cur.execute(select_task, {'tempTaskNum': task_number})
        task_detail = cur.fetchall()
        # print(task_detail)

        # Get Comments associated to task selected
        select_comments_query = """SELECT comment, assigned_to FROM comments WHERE task_num = %(task_number)s """
        cur.execute(select_comments_query, {'task_number': task_number})
        comment_list = cur.fetchall()
        print(comment_list)

        # Get List of users
        select_user_list = """SELECT first_name FROM user """
        cur.execute(select_user_list)
        user_list = cur.fetchall()
        # print(user_list)

        cur.close()

        task_status = task_detail[0]['status']
        task_priority = task_detail[0]['priority']
        task_start_date = task_detail[0]['start_date']
        task_assigned_to = task_detail[0]['assigned_to']
        task_target_date = task_detail[0]['target_date']
        task_description = task_detail[0]['description']
        task_label = task_detail[0]['task']
        print(task_status)
        # return redirect(url_for('task'))

        return render_template("task.html", task_status=task_status,
                               task_priority=task_priority,
                               task_start_date=task_start_date,
                               task_assigned_to=task_assigned_to,
                               task_target_date=task_target_date,
                               task_description=task_description,
                               comment_list=comment_list,
                               task_label=task_label,
                               task_number=task_number,
                               user_list=user_list)
    return render_template("login.html")


@app.route('/add_comment', methods=['GET', "POST"])
def addComment():
    if "user" in session:
        if request.method == 'POST':
            comment_data = request.form
            # print(comment_data.get('newCommentText'))
            # print(comment_data.get('task_number'))
            comment = comment_data.get('newCommentText')
            task_number = comment_data.get('task_number')

            # snapshot user object
            user = session['user']
            # print(user)
            # parse user name from user object
            user_name = user[0]['email']
            # print(user_name)

            # Open Connection
            cur = mysql.connection.cursor()

            # get firstname of user from user db
            select_first_name = """SELECT first_name FROM user WHERE email = %(user_name)s """
            cur.execute(select_first_name, {'user_name': user_name})
            first_name_obj = cur.fetchall()
            first_name = first_name_obj[0]['first_name']
            # print(first_name)

            # Insert comment with user first name and task number into comments table
            search_data = (first_name, comment, task_number)
            cur.execute('''INSERT INTO comments VALUES (%s, %s, %s)''', search_data)
            mysql.connection.commit()
            # Close the cursor connection
            cur.close()

            return render_template('task.html', task_number=task_number)

            # return redirect(url_for('task'))


@app.route('/remove_comment', methods=['GET', "POST"])
def removeComment():
    if "user" in session:
        if request.method == 'POST':

            # snapshot user object
            user = session['user']
            # print(user)
            # parse user name from user object
            user_name = user[0]['email']
            # print(user_name)

            # Open Connection
            cur = mysql.connection.cursor()

            # get firstname of user from user db
            select_first_name = """SELECT first_name FROM user WHERE email = %(user_name)s """
            cur.execute(select_first_name, {'user_name': user_name})
            first_name_obj = cur.fetchall()
            first_name = first_name_obj[0]['first_name']
            # print(first_name)

            # Get Comment text and Task number to remove from comments table
            comment_text = request.form.get("commentText")
            print(comment_text)
            task_num = request.form.get('commentTaskNum')
            print(task_num)

            # Remove comment from comments table assoicated to task number
            remove_comment_query = """DELETE FROM comments  WHERE assigned_to = %(first_name)s AND comment = %(comment)s AND task_num = %(task_num)s """
            cur.execute(remove_comment_query, {'first_name': first_name, "comment": comment_text, "task_num": task_num})
            mysql.connection.commit()
            cur.close()

            return redirect(url_for('task'))


@app.route('/new_task', methods=['GET', "POST"])
def newTask():
    if "user" in session:
        if request.method == 'POST':
            temp = request.form
            print(temp)

            # Open Connection
            cur = mysql.connection.cursor()

            # Each field should be initialized to null
            # So all values can be passed to DB, and null inserted if nothing chosen
            task_label = ''
            task_label = request.form.get("task_label")
            task_desc = ''
            task_desc = request.form.get("task_desc")
            task_start = ''
            task_start = request.form.get("task_start")
            task_target = ''
            task_target = request.form.get("task_target")
            task_status = ''
            task_status = request.form.get("task_status")
            task_priority = '0'
            task_priority = request.form.get("task_priority")
            task_assigned = ''
            task_assigned = request.form.get("task_assigned")
            first_name = ''

            # Check box on task screen, will assign to current user creating the task when checked
            if task_assigned == 'on':
                # snapshot user object
                user = session['user']
                # print(user)

                # parse user name from user object
                user_name = user[0]['email']
                # print(user_name)
                # get firstname of user from user db
                select_first_name = """SELECT first_name FROM user WHERE email = %(user_name)s """
                cur.execute(select_first_name, {'user_name': user_name})
                first_name_obj = cur.fetchall()
                first_name = first_name_obj[0]['first_name']
                # print(first_name)


            # Get Max task number, add one to it for next added task
            select_highest_task_num = """SELECT MAX(DISTINCT task_num) as maxNum FROM task"""
            cur.execute(select_highest_task_num)
            max_task_obj = cur.fetchall()
            max_task = max_task_obj[0]['maxNum']
            # print(max_task)
            # Set Next incremental Task Number
            task_num = max_task + 1

            task_data = (task_num, task_label, task_status, task_priority, task_start, task_target, first_name, task_desc)
            cur.execute('''INSERT INTO task VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''', task_data)
            mysql.connection.commit()

            # Close the cursor connection
            cur.close()

            return redirect(url_for('home'))

    return render_template("new_task.html")


@app.route('/boss', methods=['GET', "POST"])
def boss():
    if "user" in session:
        if request.method == 'GET':
            # Open Connection
            cur = mysql.connection.cursor()

            # snapshot user object
            user = session['user']
            # print(user)
            # parse user name from user object
            user_name = user[0]['email']
            # print(user_name)
            # get firstname of user from user db
            select_first_name = """SELECT first_name FROM user WHERE email = %(user_name)s """
            cur.execute(select_first_name, {'user_name': user_name})
            first_name_obj = cur.fetchall()
            first_name = first_name_obj[0]['first_name']
            # print(first_name)

            # Get number of tasks per user
            select_user_count_query = """SELECT assigned_to, count(assigned_to) as count FROM task 
                WHERE assigned_to != '' GROUP BY assigned_to ORDER BY count(assigned_to) desc """
            cur.execute(select_user_count_query)
            user_count = cur.fetchall()
            print(user_count)

            # Get number of unassigned Tasks
            select_unassigned_count_query = """SELECT assigned_to, count(assigned_to) as count FROM task 
                            WHERE assigned_to = '' GROUP BY assigned_to ORDER BY count(assigned_to) desc """
            cur.execute(select_unassigned_count_query)
            unassigned_count = cur.fetchall()
            print(user_count)

            # Get number of task per each Priority
            select_priority_count_query = """SELECT priority, count(priority) as count FROM task 
                                        GROUP BY priority ORDER BY count(priority) desc """
            cur.execute(select_priority_count_query)
            priority_count = cur.fetchall()
            print(priority_count)

            # get list of open assigned tasks from task db
            user_assigned_task_list = """SELECT task_num, task, status, description, assigned_to FROM task WHERE assigned_to != '' AND status != 'Closed'  """
            cur.execute(user_assigned_task_list, {'first_name': first_name})
            task_list = cur.fetchall()
            print(task_list)

            # get task list of open unassigned tasks from task db
            user_not_assigned_task_list = """SELECT task_num, task, status, description, assigned_to FROM task WHERE assigned_to = '' AND status != 'Closed'  """
            cur.execute(user_not_assigned_task_list, {'first_name': first_name})
            unassigned_task_list = cur.fetchall()
            print(unassigned_task_list)

            # get task list of closed tasks from task db
            user_closed_task_list = """SELECT task_num, task, status, description, assigned_to FROM task WHERE status = 'Closed'  """
            cur.execute(user_closed_task_list, {'first_name': first_name})
            closed_task_list = cur.fetchall()
            # print(unassigned_task_list)

            cur.close()

            return render_template('boss.html', first_name=first_name,
                                   task_list=task_list,
                                   unassigned_task_list=unassigned_task_list,
                                   user_count=user_count,
                                   unassigned_count=unassigned_count,
                                   priority_count=priority_count,
                                   closed_task_list=closed_task_list)

    return render_template("login.html")


@app.route('/update_task', methods=['GET', "POST"])
def updateTask():
    if "user" in session:
        if request.method == 'POST':
            temp = request.form
            print(temp)

            task_new_target = request.form.get("target_change")
            task_new_status = request.form.get("status_change")
            task_new_priority = request.form.get("priority_change")
            task_new_assigned = request.form.get("user_change")
            task_num = request.form.get("updateTaskNum")

            # Open Connection
            cur = mysql.connection.cursor()

            # Update task table with new details
            update_statement = """  UPDATE task SET target_date = %s, status = %s, priority  = %s, assigned_to = %s WHERE task_num = %s """
            values = (task_new_target, task_new_status, task_new_priority, task_new_assigned, task_num)
            cur.execute(update_statement, values)
            mysql.connection.commit()

            cur.close()
            # return '200'
            return redirect(url_for('home'))

    return render_template("task.html")













@app.route('/assign_user', methods=['GET', "POST"])
def assignUser():
    return render_template("home.html")


#   Capture current list of movies shown on the screen
# @app.route('/shown_movies', methods=['GET', 'POST'])
# def shownMovies():
#     if "user" in session:
#         if request.method == 'POST':
#
#             # Get list
#             information = request.data
#             temp = json.loads(information)
#             # print(temp)
#
#             return "200"


#  User clicks on Movie, caputre Title save as Viewed
# @app.route('/viewed_movie', methods=['GET', 'POST'])
# def viewedMovie():
#     if "user" in session:
#         if request.method == 'POST':
#
#             # Get Movie
#             information = request.data
#             temp = json.loads(information)
#             # print(temp['value'])
#             watched_title = temp['value']
#             # print(watched_title)
#
#             user = session['user']
#             # print(user)
#             # parse user name from user object
#             user_name = user[0]['email']
#
#             # Open Connection
#             cur = mysql.connection.cursor()
#
#             # check if movice already in db
#             # select_stmt = """ SELECT COUNT(movie_title) FROM viewed WHERE movie_title = %(watched_title)s """
#             # values = (watched_title)
#             # query = """ SELECT movie_title FROM viewed WHERE movie_title = %s """
#             # cur.execute(query, values)
#             # is_in_db = cur.fetchall()
#             # print(is_in_db)
#
#             viewed_data = (user_name, watched_title)
#
#             cur.execute('''INSERT INTO viewed VALUES (%s, %s)''', viewed_data)
#             mysql.connection.commit()
#             # Close the cursor connection
#             cur.close()
#             flash("Moive added to Viewed List", category='success')
#             # return redirect(url_for('search'))
#             return redirect(url_for('search'))


#  Search Text Captured from search field to show recietn searches
# @app.route('/filtered-list', methods=['GET', 'POST'])
# def searchData():
#     if "user" in session:
#         if request.method == 'POST':
#             search_data = request.data
#             temp = json.loads(search_data)
#             # print(temp)
#             tempGenre = temp[0]['genres']
#             # print(tempGenre)
#             # print(temp[0]['genres'])
#
#             # parse user name from user object
#             user = session['user']
#             user_name = user[0]['email']
#
#             for g in tempGenre:
#                 # Open Connection
#                 # print(g)
#                 cur = mysql.connection.cursor()
#
#                 # Feed Filtered List into Database
#                 search_data = (user_name, '', g)
#                 cur.execute('''INSERT INTO search VALUES (%s, %s, %s)''', search_data)
#                 mysql.connection.commit()
#                 # Close the cursor connection
#                 cur.close()
#
#             return "200"


#  Search Text Captured from search field to show recietn searches
# @app.route('/search', methods=['GET', "POST"])
# def search():
#     if "user" in session:
#         if request.method == 'POST':
#             # Open Connection
#             cur = mysql.connection.cursor()
#
#             user = session['user']
#             # print(user[0]['email'])
#             user_email = user[0]['email']
#
#             information = request.data
#             temp = json.loads(information)
#             # print(temp['value'])
#             search_text = temp['value']
#             # print(search_text)
#
#             search_data = (user_email, search_text, '')
#
#             cur.execute('''INSERT INTO search VALUES (%s, %s, %s)''', search_data)
#             mysql.connection.commit()
#             # Close the cursor connection
#             cur.close()
#             return "200"
#         else:
#             return render_template('search.html', data=data)
#     else:
#         return redirect(url_for("login"))
#
# @app.route('/clear_viewd', methods=['GET', 'POST'])
# def clearViewed():
#     if "user" in session:
#         if request.method == 'GET':
#             # snapshot user object
#             user = session['user']
#             # print(user)
#
#             # parse user name from user object
#             user_name = user[0]['email']
#
#             # Open Connection
#             cur = mysql.connection.cursor()
#             delete_movie_title = """DELETE FROM viewed  WHERE email = %(user_name)s """
#             cur.execute(delete_movie_title, {'user_name': user_name})
#             mysql.connection.commit()
#             # Close the cursor connection
#             cur.close()
#             # print(movie_title)
#             return  redirect(url_for('home'))
#     return render_template('home.html')


#
# @app.route('/clear_searched', methods=['GET', 'POST'])
# def clearSearched():
#     if "user" in session:
#         if request.method == 'GET':
#             # snapshot user object
#             user = session['user']
#             # print(user)
#
#             # parse user name from user object
#             user_name = user[0]['email']
#
#             # Open Connection
#             cur = mysql.connection.cursor()
#             delete_movie_title = """DELETE FROM search  WHERE email = %(user_name)s AND genres = '' """
#             cur.execute(delete_movie_title, {'user_name': user_name})
#             mysql.connection.commit()
#             # Close the cursor connection
#             cur.close()
#             # print(movie_title)
#             return  redirect(url_for('home'))
#     return render_template('home.html')
#
# @app.route('/clear_genres', methods=['GET', 'POST'])
# def clearGenres():
#     if "user" in session:
#         if request.method == 'GET':
#             # snapshot user object
#             user = session['user']
#             # print(user)
#
#             # parse user name from user object
#             user_name = user[0]['email']
#
#             # Open Connection
#             cur = mysql.connection.cursor()
#             delete_movie_title = """DELETE FROM search  WHERE email = %(user_name)s AND genres != '' """
#             cur.execute(delete_movie_title, {'user_name': user_name})
#             mysql.connection.commit()
#             # Close the cursor connection
#             cur.close()
#             # print(movie_title)
#             return  redirect(url_for('home'))
#     return render_template('home.html')


# #   Dispcy Home screen, with recent Searches, Genres Searched, and Movices viewd listed
# @app.route('/home', methods=['GET', "POST"])
# def home():
#     if "user" in session:
#         # Open Connection
#         cur = mysql.connection.cursor()
#
#         # snapshot user object
#         user = session['user']
#         # print(user)
#
#         # parse user name from user object
#         user_name = user[0]['email']
#         # print(user_name)
#
#         # get firstname of user from user db
#         select_first_name = """SELECT first_name FROM user WHERE email = %(user_name)s """
#         cur.execute(select_first_name, {'user_name': user_name})
#         first_name_obj = cur.fetchall()
#         first_name = first_name_obj[0]['first_name']
#         # print(first_name)
#
#         # get previous searches of user from search db
#         select_search_text = """SELECT search_text FROM search WHERE email = %(user_name)s AND genres = '' """
#         cur.execute(select_search_text, {'user_name': user_name})
#         search_text = cur.fetchall()
#         # print(search_text)
#
#         # get movies viewed by user from viewed db
#         select_movie_title = """SELECT movie_title FROM viewed WHERE email = %(user_name)s """
#         cur.execute(select_movie_title, {'user_name': user_name})
#         movie_title = cur.fetchall()
#         # print(movie_title)
#
#         # get genres searched by user from viewed db
#         select_genre = """SELECT genres, count(genres) as count FROM search
#                 WHERE email = %(user_name)s AND genres != ''GROUP BY genres ORDER BY count(genres) desc """
#         cur.execute(select_genre, {'user_name': user_name})
#         movie_genre = cur.fetchall()
#         # print(movie_genre)
#         # json_movie_genre = json.loads(movie_genre)
#         def condition(data):
#             for key in movie_genre:
#                 # print(data)
#                 for x, y in zip(data['genres'], key):
#                     if x == key[y]:
#                         # print(x)
#                         # print(key[y])
#                         return True
#
#         filtered_by_genre = [x for x in data if condition(x)]
#         print(filtered_by_genre)
#         print(type(filtered_by_genre))
#         # print("BREAK")
#         # print(data)
#
#         # Close the cursor connection
#         cur.close()
#         return render_template('home.html', filtered_by_genre=filtered_by_genre,
#                                first_name=first_name,
#                                search_text=search_text,
#                                movie_title=movie_title,
#                                movie_genre=movie_genre,)
#     else:
#         return redirect(url_for("login"))


if __name__ == '__main__':
    app.run(debug=True)