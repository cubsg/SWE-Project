from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from mongoengine import connect
from models import User, add_user, get_user_events, add_event, remove_user, remove_org, remove_event, remove_org_from_user, add_org  # Import User and helper functions from class.py
import hashlib
from datetime import datetime, timedelta
import calendar

app = Flask(__name__, static_folder='static')
app.secret_key = 'supersecretkey'
connect(host="mongodb://127.0.0.1:27017/TaskBoardDB")  # Connect to the MongoDB database

@app.route('/')
def home():
    # Home Page
    return render_template('Home.html')

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
            return redirect(url_for('calendar_view'))
        else:
            return render_template('LoginPage.html', error="Invalid username or password")

    return render_template('LoginPage.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template('Home.html')

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
def calendar_view():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    # Get current date or week start from query parameters
    week_start_str = request.args.get('week_start')
    if week_start_str:
        try:
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d')
        except ValueError:
            flash("Invalid date format for week start.", "error")
            week_start = datetime.today()
    else:
       # Default to current week (Monday)
        today = datetime.today()
        week_start = today - timedelta(days=today.weekday())  # weekday()=0 for Monday

    # Ensure week_start is a Monday
    if week_start.weekday() != 0:
        week_start = week_start - timedelta(days=week_start.weekday())

    week_end = week_start + timedelta(days=6)

    # Generate days for the week
    days = [week_start + timedelta(days=i) for i in range(7)]

    # Generate 12 two-hour time slots from 0:00 to 24:00
    time_slots = []
    for i in range(0, 24, 2):
        start_time = f"{i:02d}:00"
        end_time = f"{i+2:02d}:00"
        time_slots.append({
            'start_time': start_time,
            'end_time': end_time
        })

    # Format current month and year
    current_month_year = week_start.strftime('%B %Y')

    # Format week range for display
    week_range = f"{week_start.strftime('%B %d')} to {week_end.strftime('%B %d')}"

    return render_template(
        'Calendar.html',
        days=days,
        time_slots=time_slots,
        current_month_year=current_month_year,
        week_range=week_range,
        week_start=week_start.strftime('%Y-%m-%d')  # Ensure it's in YYYY-MM-DD format
    )

@app.route('/favicon.ico')
def favicon():
    return '', 204

''' George - Implement routes for:
        adding event
        adding class/org to user
        get user events to display calendar
'''

@app.route('/get_events', methods=['GET'])
def get_events():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized access."}), 401

    username = session['username']
    week_start_str = request.args.get('week_start')

    if not week_start_str:
        # Default to current week
        today = datetime.today()
        week_start = today - timedelta(days=today.weekday() + 1)
        week_start_str = week_start.strftime('%Y-%m-%d')
    else:
        try:
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    # Ensure week_start is a Monday
    if week_start.weekday() != 0:
        week_start = week_start - timedelta(days=week_start.weekday())


    events = get_user_events(username, week_start_str=week_start.strftime('%Y-%m-%d'))

    return jsonify({"events": events}), 200

@app.route('/personal_info')
def personal_info():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = User.objects(username=username.lower()).first()
    
    if not user:
        return redirect(url_for('login'))
    
    # Pass user information to the template
    return render_template('PersonalInfo.html', user=user)

@app.route('/personal_info_settings', methods=['GET', 'POST'])
def personal_info_settings():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user = User.objects(username=username.lower()).first()

    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')

        if not firstname or not lastname:
            error = "First name and last name cannot be empty."
            return render_template('PersonalInfoSetting.html', error=error, user=user)

        # Update user's first name and last name
        user.update(firstname=firstname, lastname=lastname)
        return redirect(url_for('personal_info'))

    return render_template('PersonalInfoSetting.html', user=user)

# server.py

@app.route('/event_setting', methods=['GET', 'POST'])
def event_setting():
    if 'username' not in session:
        if request.method == 'POST':
            return jsonify({"error": "Unauthorized access."}), 401
        else:
            return redirect(url_for('login'))

    username = session['username']

    if request.method == 'POST':
        if request.is_json:
            # Handle AJAX-based addition from calendar
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided."}), 400

            event_name = data.get('event_name')
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            location = data.get('location')

            # Validate form fields
            if not event_name or not start_time or not end_time or not location:
                return jsonify({"error": "All fields are required."}), 400

            # Call add_event function to save the event
            result = add_event(event_name, start_time, end_time, location, username=username)
            if "Success" in result:
                return jsonify({"message": result}), 200
            else:
                return jsonify({"error": result}), 400
        else:
            # Handle form-based addition from profile page
            event_name = request.form.get('event_name')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            location = request.form.get('location')

            # Validate form fields
            if not event_name or not start_time or not end_time or not location:
                flash("All fields are required.", "error")
                return render_template('EventSetting.html')

            # Add event to the database
            result = add_event(event_name, start_time, end_time, location, username=username)
            if "Success" in result:
                flash(result, "success")
                return redirect(url_for('calendar_view'))
            else:
                flash(result, "error")
                return render_template('EventSetting.html')

    # If GET request, redirect to calendar or render a default view
    return redirect(url_for('calendar_view'))

@app.route('/organization_setting', methods=['GET', 'POST'])
def organization_setting():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        org_type = request.form.get('org_type')
        org_name = request.form.get('organization_name')

        # Validate and add organization
        result = add_org(org_type, org_name, session['username'])
        if "Success" in result:
            return redirect(url_for('personal_info'))
        else:
            return render_template('OrganizationSetting.html', error=result)

    return render_template('OrganizationSetting.html')

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
