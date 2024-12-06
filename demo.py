# demo.py - Used to populate database with test data

import mongoengine as me
from datetime import datetime, timedelta, timezone
from dateutil import parser
import re
import hashlib

me.connect(host="mongodb://127.0.0.1:27017/TaskBoardDB")

class User(me.Document):
    username = me.EmailField(required=True, unique=True)
    password = me.StringField(required=True)
    firstname = me.StringField(required=True)
    lastname = me.StringField(required=True)
    classes = me.ListField()
    organizations = me.ListField(me.StringField())
    holidays = me.ListField()
    events = me.ListField(me.DictField())

class Organization(me.Document):
    type = me.StringField(required=True)
    name = me.StringField(required=True, unique=True)
    events = me.ListField(me.DictField())

class Event(me.Document):
    name = me.StringField(required=True)
    starttime = me.DateTimeField(required=True)
    endtime = me.DateTimeField(required=True)
    location = me.StringField(required=True)

def add_user(email, password, firstname, lastname):
    email = email.lower()

    if (not firstname.isalpha()) or (not lastname.isalpha()):
        print("Error: Enter a valid name")
        return None
    
    if User.objects(username=email):
        print("Error: Account with that email already exists")
        return None

    hashedpassword = hashlib.sha256(password.encode()).hexdigest()

    user_data = User(username=email, password=hashedpassword, firstname=firstname, lastname=lastname)
    user_data.save()
    print("Success: User added successfully")
    return user_data

def main():
    admin_email = 'admin@example.com'
    admin_password = 'adminpassword'
    admin_firstname = 'Admin'
    admin_lastname = 'User'

    if not User.objects(username=admin_email).first():
        print("Creating admin user...")
        admin_user = add_user(admin_email, admin_password, admin_firstname, admin_lastname)
    else:
        admin_user = User.objects(username=admin_email).first()
        print("Admin user already exists.")

    organizations = [
        {
            "type": "class",
            "name": "CEN3031",
            "schedule": {
                "days": ["Monday", "Wednesday", "Friday"],
                "start_time": "09:00",
                "end_time": "10:00"
            }
        },
        {
            "type": "class",
            "name": "COP4600",
            "schedule": {
                "days": ["Monday", "Wednesday", "Friday"],
                "start_time": "10:30",
                "end_time": "11:30"
            }
        },
        {
            "type": "class",
            "name": "CNT4007",
            "schedule": {
                "days": ["Monday", "Wednesday", "Friday"],
                "start_time": "13:00",
                "end_time": "14:00"
            }
        },
        {
            "type": "class",
            "name": "CAP3032",
            "schedule": {
                "days": ["Tuesday", "Thursday"],
                "start_time": "09:30",
                "end_time": "11:00"
            }
        },
        {
            "type": "class",
            "name": "CIS4301",
            "schedule": {
                "days": ["Tuesday", "Thursday"],
                "start_time": "11:30",
                "end_time": "13:00"
            }
        },
        {
            "type": "club",
            "name": "Chess Club",
            "schedule": {
                "day": "Wednesday",
                "start_time": "17:00",
                "end_time": "18:30"
            }
        },
        {
            "type": "club",
            "name": "Robotics Club",
            "schedule": {
                "day": "Thursday",
                "start_time": "18:00",
                "end_time": "19:30"
            }
        },
        {
            "type": "club",
            "name": "Art Club",
            "schedule": {
                "day": "Friday",
                "start_time": "16:00",
                "end_time": "17:30"
            }
        },
        {
            "type": "club",
            "name": "Dance Club",
            "schedule": {
                "day": "Monday",
                "start_time": "18:30",
                "end_time": "20:00"
            }
        },
        {
            "type": "club",
            "name": "Debate Club",
            "schedule": {
                "day": "Tuesday",
                "start_time": "17:00",
                "end_time": "18:30"
            }
        }
    ]

    total_weeks = 15

    semester_start_date = datetime(2024, 9, 4, tzinfo=timezone.utc)

    for org in organizations:
        org_name = org["name"].lower()
        existing_org = Organization.objects(name=org_name).first()
        if not existing_org:
            organization = Organization(
                type=org["type"],
                name=org_name
            )
            organization.save()
            print(f"Success: Created organization '{org['name']}' of type '{org['type']}'.")
        else:
            organization = existing_org
            print(f"Organization '{org['name']}' already exists.")
        
        if org_name not in admin_user.organizations:
            admin_user.update(add_to_set__organizations=org_name)
            print(f"Success: Assigned organization '{org['name']}' to admin user.")
        else:
            print(f"Organization '{org['name']}' already assigned to admin user.")

        if org["type"] == "class":
            days = org["schedule"]["days"]
            start_time = org["schedule"]["start_time"]
            end_time = org["schedule"]["end_time"]

            for week in range(total_weeks):
                week_start_date = semester_start_date + timedelta(weeks=week)
                for day in days:
                    days_ahead = {
                        "Monday": 0,
                        "Tuesday": 1,
                        "Wednesday": 2,
                        "Thursday": 3,
                        "Friday": 4,
                        "Saturday": 5,
                        "Sunday": 6
                    }
                    day_offset = days_ahead[day]
                    event_date = week_start_date + timedelta(days=day_offset)

                    start_datetime_str = f"{event_date.date()}T{start_time}:00Z"
                    end_datetime_str = f"{event_date.date()}T{end_time}:00Z"

                    start_datetime = parser.isoparse(start_datetime_str)
                    end_datetime = parser.isoparse(end_datetime_str)

                    location = f"Room {100 + week%100}"

                    event_dict = {
                        'name': f"{org['name'].upper()} Lecture",
                        'starttime': start_datetime,
                        'endtime': end_datetime,
                        'location': location
                    }

                    if event_dict not in organization.events:
                        organization.update(push__events=event_dict)
                        print(f"Added {org['name']} Lecture on {day} {start_time} - {end_time}.")
                    else:
                        print(f"Event already exists for {org['name']} on {day}.")

        elif org["type"] == "club":
            meeting_day = org["schedule"]["day"]
            start_time = org["schedule"]["start_time"]
            end_time = org["schedule"]["end_time"]

            for week in range(total_weeks):
                week_start_date = semester_start_date + timedelta(weeks=week)
                days_ahead = {
                    "Monday": 0,
                    "Tuesday": 1,
                    "Wednesday": 2,
                    "Thursday": 3,
                    "Friday": 4,
                    "Saturday": 5,
                    "Sunday": 6
                }
                day_offset = days_ahead[meeting_day]
                event_date = week_start_date + timedelta(days=day_offset)

                start_datetime_str = f"{event_date.date()}T{start_time}:00Z"
                end_datetime_str = f"{event_date.date()}T{end_time}:00Z"

                start_datetime = parser.isoparse(start_datetime_str)
                end_datetime = parser.isoparse(end_datetime_str)

                location = "Main Hall"

                event_dict = {
                    'name': f"{org['name']} Meeting",
                    'starttime': start_datetime,
                    'endtime': end_datetime,
                    'location': location
                }

                if event_dict not in organization.events:
                    organization.update(push__events=event_dict)
                    print(f"Added {org['name']} Meeting on {meeting_day} {start_time} - {end_time}.")
                else:
                    print(f"Event already exists for {org['name']} on {meeting_day}.")

    print("Demo data population complete.")

if __name__ == "__main__":
    main()
