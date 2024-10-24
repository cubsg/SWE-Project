import mongoengine as me
from pymongo import MongoClient
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

class Organization(me.Document):
    name = me.StringField()
    event = me.ListField(me.DictField())

'''class Holiday(Document):
    name = StringField()
    day = DateTimeField()
    repeat = BooleanField()'''

'''class Event(meDocument):
    name = StringField()
    starttime = DateField()
    endtime = DateField()
    duration = IntField()
    location = StringField()'''

def add_user(email, password, firstname, lastname):
    email = email.lower()

    #Check if name contains all letters
    if (not firstname.isalpha()) or (not lastname.isalpha()):
        return print("Error: Enter a valid name")
    
    #Check if email is unique
    if User.objects(username=email):
        return print("Error: Account with that email already exists")

    #Hash password
    hashedpassword = hashlib.sha256(password.encode()).hexdigest()

    #Store data to database
    user_data = User(username=email, password=hashedpassword, firstname=firstname, lastname=lastname)
    user_data.save()
    return print(f"Success: User {email} added successfully")

def add_org():
    pass
    #Add code to check if org already there, then add org

def add_event():
    pass
    #Check if duplicate event, then add event into Organization or Class

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



#add_user("Quickie@gmAIL.com", "Whatspopping", "John", "Quick")
#add_org_to_user("george.cubs3@hotstuFF.com", "SHPE")
#add_class_to_user("quickie@gmail.com", "COMP ORG")
remove_org_from_user("george.cubs3@hotstuff.com", "COMP ORG")