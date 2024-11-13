from flask import Flask, request, jsonify, render_template, redirect, url_for
from mongoengine import connect
from models import User, add_user  # Import User and helper functions from class.py
import hashlib

app = Flask(__name__)
connect(host="mongodb://127.0.0.1:27017/TaskBoardDB")  # Connect to the MongoDB database

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('pwd')

        user = User.objects(username=username.lower()).first()
        if user and user.password == hashlib.sha256(password.encode()).hexdigest():
            return jsonify({"success": f"User '{username}' logged in successfully"})
        else:
            return jsonify({"error": "Invalid username or password"}), 401

    return render_template('LoginPage.html')  # Display login page

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
            return jsonify({"redirect": url_for('login')})  # Send login redirect URL on success
        else:
            return jsonify({"error": result}), 400

    return render_template('RegisterPage.html')  # Display registration page

''' George - Implement routes for:
        adding event
        adding class/org to user
        get user events to display calendar
'''

'''John - Implement routes for:
        removal of user
        removal of org
        removal of event
        removal of org from user
'''
    
if __name__ == '__main__':
    app.run(debug=True)
