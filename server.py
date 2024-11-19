from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from mongoengine import connect
from models import User, add_user, get_user_events  # Import User and helper functions from class.py
import hashlib

app = Flask(__name__)
app.secret_key = 'supersecretkey'
connect(host="mongodb://127.0.0.1:27017/TaskBoardDB")  # Connect to the MongoDB database

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('pwd')

        if not username or not password:
            return render_template('LoginPage.html', error="Username and password are required")

        user = User.objects(username=username.lower()).first()
        if user and user.password == hashlib.sha256(password.encode()).hexdigest():
            session['username'] = username
            return redirect(url_for('calendar'))
        else:
            return render_template('LoginPage.html', error="Invalid username or password")

    return render_template('LoginPage.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('pwd')
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')

        # Check if any fields are empty
        if not username or not password or not firstname or not lastname:
            return jsonify({"error": "All fields are required"}), 400

        # Call add_user function to save the user to the database
        result = add_user(username, password, firstname, lastname)
        if "Success" in result:
            return jsonify({"redirect": url_for('login')})
        else:
            return jsonify({"error": result}), 400

    return render_template('RegisterPage.html')  # Display registration page

@app.route('/calendar')
def calendar():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    events = get_user_events(username)
    return render_template('Calendar.html', events=events)

''' George - Implement routes for:
        adding event
        adding class/org to user
        get user events to display calendar
'''

@app.route('/delete_user', methods=['POST'])
def delete_user():
    username = request.form.get('username')
    result = remove_user(username)
    if "Success" in result:
        return jsonify({"message": result})
    else:
        return jsonify({"error": result}), 400

@app.route('/delete_org', methods=['POST'])
def delete_org():
    org_name = request.form.get('org_name')
    result = remove_org(org_name)
    if "Success" in result:
        return jsonify({"message": result})
    else:
        return jsonify({"error": result}), 400

@app.route('/delete_event', methods=['POST'])
def delete_event():
    event_name = request.form.get('event_name')
    result = remove_event(event_name)
    if "Success" in result:
        return jsonify({"message": result})
    else:
        return jsonify({"error": result}), 400

@app.route('/delete_org_from_user', methods=['POST'])
def delete_org_from_user():
    username = request.form.get('username')
    org_name = request.form.get('org_name')
    result = remove_org_from_user(username, org_name)
    if "Success" in result:
        return jsonify({"message": result})
    else:
        return jsonify({"error": result}), 400
    
if __name__ == '__main__':
    app.run(debug=True)
