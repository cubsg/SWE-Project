import mongoengine as me
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import re
import hashlib
from dateutil import parser
 
me.connect(host="mongodb://127.0.0.1:27017/TaskBoardDB")

class User(me.Document):
    username = me.EmailField()
    password = me.StringField()
    firstname = me.StringField()
    lastname = me.StringField()
    organizations = me.ListField()
    events = me.ListField(me.DictField())

class Organization(me.Document):
    type = me.StringField()
    name = me.StringField()
    events = me.ListField(me.DictField())

class Event(me.Document):
    name = me.StringField(required=True)
    starttime = me.DateTimeField(required=True)
    endtime = me.DateTimeField(required=True)
    location = me.StringField(required=True)

def add_user(email, password, firstname, lastname):
    email = email.lower()

    # Check if name contains all letters
    if (not firstname.isalpha()) or (not lastname.isalpha()):
        return "Error: Enter a valid name"
    
    # Check if email is unique
    if User.objects(username=email):
        return "Error: Account with that email already exists"

    # Hash password
    hashedpassword = hashlib.sha256(password.encode()).hexdigest()

    # Store data to database
    user_data = User(username=email, password=hashedpassword, firstname=firstname, lastname=lastname)
    user_data.save()
    return "Success: User added successfully"

def add_event(event_name, start_time, end_time, location, username=None, organization_name=None):
    # Parse the start_time and end_time with timezone awareness
    try:
        start_datetime = parser.isoparse(start_time)
        end_datetime = parser.isoparse(end_time)
        
        # Optionally, convert to UTC
        if start_datetime.tzinfo is None:
            start_datetime = start_datetime.replace(tzinfo=timezone.utc)
        else:
            start_datetime = start_datetime.astimezone(timezone.utc)
        
        if end_datetime.tzinfo is None:
            end_datetime = end_datetime.replace(tzinfo=timezone.utc)
        else:
            end_datetime = end_datetime.astimezone(timezone.utc)
        
    except ValueError:
        return "Error: Invalid date and time format. Use ISO 8601 format."
    
    event_dict = {
        'name': event_name,
        'starttime': start_datetime,
        'endtime': end_datetime,
        'location': location
    }

    if username: 
        user = User.objects(username=username.lower()).first()
        if not user:
            return "Error: User not found."
        
        # Check if event already exists in user's calendar
        for event in user.events:
            if (event.get('name') == event_name and 
                event.get('starttime') == start_datetime and 
                event.get('endtime') == end_datetime):
                return f"Error: '{event_name}' already exists in your calendar."
        
        user.update(add_to_set__events=[event_dict])
        return f"Success: '{event_name}' added to your calendar."
    
    if organization_name:
        organization = Organization.objects(name=organization_name.lower()).first()
        if not organization:
            return "Error: Organization not found."
        
        # Check that event does not already exist in org calendar
        for event in organization.events:
            if (event.get('name') == event_name and 
                event.get('starttime') == start_datetime and 
                event.get('endtime') == end_datetime):
                return f"Error: '{event_name}' already exists in {organization_name}'s calendar."
        
        organization.update(add_to_set__events=[event_dict])
        return f"Success: '{event_name}' added to {organization_name}'s calendar."
    
    return "Error: No valid user or organization provided."

def remove_user(username):
    user = User.objects(username=username.lower()).first()
    if not user:
            return "Error: User not found"
    user.delete()
    return f"Success: User '{username}' removed successfully"

def remove_org(name):
    org = Organization.objects(name=name.lower()).first()
    if not org:
        return "Error: Organization not found"
    org.delete()
    return f"Success: Organization '{name}' removed successfully"

def remove_event(event_name):
    event = Event.objects(name=event_name).first()
    if not event:
        return "Error: Event not found"
    event.delete()
    return f"Success: Event '{event_name}' removed successfully"

def add_org_to_user(email, organization):
    email = email.lower()

    #Check if valid email
    if not User.objects(username=email):
        return print("Error: Account not found")
    
    #Check if organization already in user list
    if User.objects(username=email, organizations=organization):
        return print("Error: Organization already added")

    #Add organization to user
    User.objects(username=email).update(add_to_set__organizations=[organization])
    return print(f"Success: Added '{organization}' to user '{email}'")

def remove_org_from_user(email, organization):
    email = email.lower()

    #Check if valid email
    if not User.objects(username=email):
        return print("Error: Account not found")
    
    #Check if organization not in user list
    if not User.objects(username=email, organizations=organization):
        return print("Error: Organization not found")

    #Remove organization from user
    User.objects(username=email).update_one(pull__organizations=organization)
    return print(f"Success: Removed '{organization}' from user '{email}'")

def get_user_events(username, week_start_str=None):
    user = User.objects(username=username.lower()).first()
    if not user:
        return []

    try:
        week_start_date = datetime.strptime(week_start_str, '%Y-%m-%d') if week_start_str else datetime.today()
    except ValueError:
        return []

    week_end_date = week_start_date + timedelta(days=7)
    
    user_events = [
        event for event in user.events
        if event.get('starttime') <= week_end_date and event.get('endtime') >= week_start_date
    ]

    org_events = []
    for org_name in user.organizations:
        organization = Organization.objects(name=org_name.lower()).first()
        if organization:
            org_events.extend([
                event for event in organization.events
                if event.get('starttime') <= week_end_date and event.get('endtime') >= week_start_date
            ])

    all_events = user_events + org_events
    formatted_events = [
        {
            'name': event.get('name'),
            'starttime': event.get('starttime').isoformat(),
            'endtime': event.get('endtime').isoformat(),
            'location': event.get('location')
        }
        for event in all_events
    ]
    
    return formatted_events

