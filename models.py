import mongoengine as me
from pymongo import MongoClient
from datetime import datetime
import re
import hashlib
 
me.connect(host="mongodb://127.0.0.1:27017/TaskBoardDB")
class User(me.Document):
    username = me.EmailField()
    password = me.StringField()
    firstname = me.StringField()
    lastname = me.StringField()
    classes = me.ListField()
    organizations = me.ListField()
    holidays = me.ListField()
    events = me.ListField(me.DictField())

class Organization(me.Document):
    type = me.StringField()
    name = me.StringField()
    events = me.ListField(me.DictField())

'''class Holiday(Document):
    name = StringField()
    day = DateTimeField()
    repeat = BooleanField()'''

class Event(me.Document):
    name = me.StringField()
    starttime = me.DateField()
    endtime = me.DateField()
    location = me.StringField()

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

def add_org(type, name, username): #type - class or org
    name = name.lower()

    if type == "class": #Forcing class names to be course codes only
        if not re.match(r"^[A-Z]{3,4}\d{3,4}$", name.upper()):
            return print("Error: Class names must follow the format 'XXX0000' (3-4 letters followed by 3-4 numbers)")
    
    elif type == "club": #Forcing club names to be alphabetic only
        if not re.match(r"^[a-zA-Z\s]+$", name):
            return print("Error: Club names must contain only alphabetic characters and spaces")

    else:
        return print("Error: Unknown organization type")
    
    if Organization.objects(name=name):
        return print("Error: Organization with that name already exists")
    
    org_data = Organization(type=type, name=name)
    org_data.save()

    add_org_to_user(username, name)

    return print(f"Success: {username} Created {name}")

def add_event(event_name, start_time, end_time, location, username=None, organization_name=None):
    event_data = Event(name=event_name,starttime=start_time,endtime=end_time,location=location)

    if username: 
        user = User.objects(username=username.lower()).first()
        if not user:    #Check that user adding the event exists
            return print("Error: User not found")
        
        if event_data.to_mongo() in user.events:    #Check if event already exists in users calendar
            return print(f"Error: {event_name} already exists in {username}'s calendar")
        
        user.update(add_to_set__events=[event_data.to_mongo()])
        return print(f"Success: {event_name} added to {username}'s calendar")
    
    if organization_name:
        organization = Organization.objects(name=organization_name.lower()).first()
        if not organization:    #Check that organization exists
            return print("Error: Organization not found")
        
        if event_data.to_mongo() in organization.events:    #Check that event does not already exist in org calendar
            return print(f"Error: {event_name} already exists in {organization_name}'s calendar")
        
        organization.update(add_to_set__events=[event_data.to_mongo()])
        return print(f"Success: {event_name} added to {organization_name}'s calendar")
    
    return print("Error: No valid user or organization provided")

def remove_user():
    pass

def remove_org():
    pass

def remove_event():
    pass

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

def add_class_to_user(email, enrolledclass):
    email = email.lower()

    #Check if valid email
    if not User.objects(username=email):
        return print("Error: Account not found")
    
    #Check if class already in user list
    if User.objects(username=email, classes=enrolledclass):
        return print("Error: Class already added")

    #Add class to user
    User.objects(username=email).update(add_to_set__classes=[enrolledclass])

def add_holiday_to_user():
    pass #Add holiday to list on user

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

def get_user_events(username):
    user = User.objects(username=username.lower()).first()
    if not user:
        return print(f"Error: User '{username}' not found")
    
    user_events = user.events

    # Collect events from organizations the user is part of
    org_events = []
    for org_name in user.organizations:
        organization = Organization.objects(name=org_name.lower()).first()
        if organization:
            org_events.extend(organization.events)
    
    # Combine user events with organization events
    all_events = user_events + org_events

    # Return the combined list of events
    return all_events
