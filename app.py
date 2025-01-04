from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import uuid, secrets
import firebase_admin
from firebase_admin import credentials, firestore


app = Flask(__name__)
app.secret_key = secrets.token_hex(24)

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/create', methods=['POST'])
def create_chat_room():
    room_id = str(uuid.uuid4())[:8]
    password = str(uuid.uuid4())[:8]
    db.collection('chat_rooms').document(room_id).set({'password': password})
    db.collection('chat_records').document(room_id).set({'messages': []})
    
    return jsonify({"room_id": room_id, "password": password})


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        room_id = request.form.get('room_id')
        password = request.form.get('password')
        username = request.form.get('username')
        room_doc = db.collection('chat_rooms').document(room_id).get()

        if room_doc.exists and room_doc.to_dict().get('password') == password:
            session['room_id'] = room_id
            session['username'] = username
            return render_template('chat.html', room_id=room_id, username=username)
        else:
            return "Invalid Room ID or Password", 401

    # Handle GET request
    room_id = request.args.get('room_id', '')  # Get pre-filled room_id
    password = request.args.get('password', '')  # Get pre-filled password

    return render_template('login.html', room_id=room_id, password=password)


@app.route('/join_chat', methods=['GET'])
def join_chat():
    room_id = request.args.get('room_id')
    password = request.args.get('password')

    if not room_id or not password:
        return "Room ID and password are required.", 400

    # Redirect to login page with room_id and password as query parameters
    return redirect(url_for('chat', room_id=room_id, password=password))


@app.route('/send_message', methods=['POST'])
def send_message():
    room_id = session.get('room_id')
    if not room_id:
        return "Unauthorized", 401

    data = request.json  # Access JSON data
    message = data.get('message')  # Get the message from JSON payload
    username = data.get('username')  # Explicitly pass the username

    # Add the message to Firestore
    chat_ref = db.collection('chat_records').document(room_id)
    chat_ref.update({
        'messages': firestore.ArrayUnion([{"username": username, "message": message}])
    })

    return jsonify({"status": "success"})

@app.route('/get_messages', methods=['GET'])
def get_messages():
    room_id = session.get('room_id')
    if not room_id:
        return "Unauthorized", 401

    room_doc = db.collection('chat_rooms').document(room_id).get()
    if not room_doc.exists:
        return jsonify({"error": "Room closed"})


    chat_doc = db.collection('chat_records').document(room_id).get()
    if chat_doc.exists:
        return jsonify(chat_doc.to_dict().get('messages', []))
    return jsonify([])



@app.route('/killswitch', methods=['POST'])
def kill_switch():
    room_id = request.form.get('room_id')
    password = request.form.get('password')
    room_doc = db.collection('chat_rooms').document(room_id).get()
    if room_doc.exists and room_doc.to_dict().get('password') == password:
        db.collection('chat_rooms').document(room_id).delete()
        db.collection('chat_records').document(room_id).delete()
        return jsonify({"status": "Chat room deleted"})
    return "Invalid Room ID or Password", 401


@app.route('/exit_chat', methods=['POST'])
def exit_chat():
    data = request.json
    room_id = data.get('room_id')

    if not room_id:
        return "Unauthorized", 401

    db.collection('chat_rooms').document(room_id).delete()
    db.collection('chat_records').document(room_id).delete()
    
    return jsonify({"status": "Chat room closed for everyone"})



if __name__ == '__main__':
    app.run(debug=False)
