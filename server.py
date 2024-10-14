from flask import Flask, request, jsonify
from pymongo import MongoClient
import hashlib

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['TaskBoardDB']

def add_user(username, email, password):
    if db.users.find_one({"username": username}):
        return {"error": "Username already exists"}

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    user_data = {
        "username": username,
        "email": email,
        "password": hashed_password,
        "organizations": [],
        "personal_events": [],
        "settings": {
            "timezone": "UTC",
            "notifications": True
        }
    }

    db.users.insert_one(user_data)
    return {"success": f"User '{username}' added successfully"}

def add_organization(name, description):
    if db.organizations.find_one({"name": name}):
        return {"error": "Organization already exists"}

    organization_data = {
        "name": name,
        "description": description,
        "members": [],
        "events": []
    }

    db.organizations.insert_one(organization_data)
    return {"success": f"Organization '{name}' added successfully"}

def add_user_to_organization(username, organization_name):
    user = db.users.find_one({"username": username})
    if not user:
        return {"error": f"User '{username}' not found"}

    organization = db.organizations.find_one({"name": organization_name})
    if not organization:
        return {"error": f"Organization '{organization_name}' not found"}

    user_id = user["_id"]
    organization_id = organization["_id"]

    if organization_id not in user["organizations"]:
        db.users.update_one(
            {"_id": user_id},
            {"$push": {"organizations": organization_id}}
        )

    if user_id not in organization["members"]:
        db.organizations.update_one(
            {"_id": organization_id},
            {"$push": {"members": user_id}}
        )

    return {"success": f"User '{username}' added to organization '{organization_name}'"}

def add_event(event_data, event_type):
    if event_type == "personal":
        user = db.users.find_one({"username": event_data.get("owner_username")})
        if not user:
            return {"error": f"User '{event_data.get('owner_username')}' not found"}

        event_data["type"] = "personal"
        event_data["owner_id"] = user["_id"]

        event_id = db.events.insert_one(event_data).inserted_id

        db.users.update_one(
            {"_id": user["_id"]},
            {"$push": {"personal_events": event_id}}
        )
        return {"success": f"Personal event '{event_data['name']}' added for user '{user['username']}'"}

    elif event_type == "organization":
        organization = db.organizations.find_one({"name": event_data.get("organization_name")})
        if not organization:
            return {"error": f"Organization '{event_data.get('organization_name')}' not found"}

        event_data["type"] = "organization"
        event_data["organization_id"] = organization["_id"]

        event_id = db.events.insert_one(event_data).inserted_id

        db.organizations.update_one(
            {"_id": organization["_id"]},
            {"$push": {"events": event_id}}
        )
        return {"success": f"Organization event '{event_data['name']}' added to organization '{organization['name']}'"}

    return {"error": "Invalid event type"}

def get_user_events(username):
    user = db.users.find_one({"username": username})
    if not user:
        return {"error": f"User '{username}' not found"}

    personal_event_ids = user.get("personal_events", [])
    user_organization_ids = user.get("organizations", [])

    personal_events = list(db.events.find({"_id": {"$in": personal_event_ids}}))

    organization_events = list(db.events.find({
        "type": "organization",
        "organization_id": {"$in": user_organization_ids}
    }))

    # Convert ObjectId to string for JSON serialization
    all_events = personal_events + organization_events
    for event in all_events:
        event["_id"] = str(event["_id"])
        if "owner_id" in event:
            event["owner_id"] = str(event["owner_id"])
        if "organization_id" in event:
            event["organization_id"] = str(event["organization_id"])

    return {"events": all_events}

# Flask routes
@app.route('/add_user', methods=['POST'])
def add_user_route():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    result = add_user(username, email, password)
    return jsonify(result)

@app.route('/add_organization', methods=['POST'])
def add_organization_route():
    data = request.json
    name = data.get('name')
    description = data.get('description')

    if not name or not description:
        return jsonify({"error": "Missing required fields"}), 400

    result = add_organization(name, description)
    return jsonify(result)

@app.route('/add_user_to_organization', methods=['POST'])
def add_user_to_organization_route():
    data = request.json
    username = data.get('username')
    organization_name = data.get('organization_name')

    if not username or not organization_name:
        return jsonify({"error": "Missing required fields"}), 400

    result = add_user_to_organization(username, organization_name)
    return jsonify(result)

@app.route('/add_event', methods=['POST'])
def add_event_route():
    data = request.json
    event_type = data.get('type')
    if not event_type or event_type not in ["personal", "organization"]:
        return jsonify({"error": "Invalid event type"}), 400

    # Ensure the duration field is included
    if "duration" not in data:
        return jsonify({"error": "Missing required field: duration"}), 400

    result = add_event(data, event_type)
    return jsonify(result)

@app.route('/get_user_events/<username>', methods=['GET'])
def get_user_events_route(username):
    result = get_user_events(username)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
