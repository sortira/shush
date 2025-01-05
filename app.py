from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import uuid, secrets
import firebase_admin
import re
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
    room_Censor = True
    room_id = session.get('room_id')
    if not room_id:
        return "Unauthorized", 401

    data = request.json  # Access JSON data
    message = " " + data.get('message') + " "  # Get the message from JSON payload
    username = data.get('username')  # Explicitly pass the username
    #process message with regex

    if(room_Censor):
        #regx = "<>([a-z://.A-Z0-9]+)<>"
        badword = ["4r5e", "5h1t", "5hit", "a55", "anal", "anus", "ar5e", "arrse", "arse", "ass", "ass-fucker", "asses", "assfucker", "assfukka", "asshole", "assholes", "asswhole", "a_s_s", "b!tch", "b00bs", "b17ch", "b1tch", "ballbag", "balls", "ballsack", "bastard", "beastial", "beastiality", "bellend", "bestial", "bestiality", "bi+ch", "biatch", "bitch", "bitcher", "bitchers", "bitches", "bitchin", "bitching", "bloody", "blow job", "blowjob", "blowjobs", "boiolas", "bollock", "bollok", "boner", "boob", "boobs", "booobs", "boooobs", "booooobs", "booooooobs", "breasts", "buceta", "bugger", "bum", "bunny fucker", "butt", "butthole", "buttmuch", "buttplug", "c0ck", "c0cksucker", "carpet muncher", "cawk", "chink", "cipa", "cl1t", "clit", "clitoris", "clits", "cnut", "cock", "cock-sucker", "cockface", "cockhead", "cockmunch", "cockmuncher", "cocks", "cocksuck", "cocksucked", "cocksucker", "cocksucking", "cocksucks", "cocksuka", "cocksukka", "cok", "cokmuncher", "coksucka", "coon", "cox", "crap", "cum", "cummer", "cumming", "cums", "cumshot", "cunilingus", "cunillingus", "cunnilingus", "cunt", "cuntlick", "cuntlicker", "cuntlicking", "cunts", "cyalis", "cyberfuc", "cyberfuck", "cyberfucked", "cyberfucker", "cyberfuckers", "cyberfucking", "d1ck", "damn", "dick", "dickhead", "dildo", "dildos", "dink", "dinks", "dirsa", "dlck", "dog-fucker", "doggin", "dogging", "donkeyribber", "doosh", "duche", "dyke", "ejaculate", "ejaculated", "ejaculates", "ejaculating", "ejaculatings", "ejaculation", "ejakulate", "f u c k", "f u c k e r", "f4nny", "fag", "fagging", "faggitt", "faggot", "faggs", "fagot", "fagots", "fags", "fanny", "fannyflaps", "fannyfucker", "fanyy", "fatass", "fcuk", "fcuker", "fcuking", "feck", "fecker", "felching", "fellate", "fellatio", "fingerfuck", "fingerfucked", "fingerfucker", "fingerfuckers", "fingerfucking", "fingerfucks", "fistfuck", "fistfucked", "fistfucker", "fistfuckers", "fistfucking", "fistfuckings", "fistfucks", "flange", "fook", "fooker", "fuck", "fucka", "fucked", "fucker", "fuckers", "fuckhead", "fuckheads", "fuckin", "fucking", "fuckings", "fuckingshitmotherfucker", "fuckme", "fucks", "fuckwhit", "fuckwit", "fudge packer", "fudgepacker", "fuk", "fuker", "fukker", "fukkin", "fuks", "fukwhit", "fukwit", "fux", "fux0r", "f_u_c_k", "gangbang", "gangbanged", "gangbangs", "gaylord", "gaysex", "goatse", "God", "god-dam", "god-damned", "goddamn", "goddamned", "hardcoresex", "hell", "heshe", "hoar", "hoare", "hoer", "homo", "hore", "horniest", "horny", "hotsex", "jack-off", "jackoff", "jap", "jerk-off", "jism", "jiz", "jizm", "jizz", "kawk", "knob", "knobead", "knobed", "knobend", "knobhead", "knobjocky", "knobjokey", "kock", "kondum", "kondums", "kum", "kummer", "kumming", "kums", "kunilingus", "l3i+ch", "l3itch", "labia", "lust", "lusting", "m0f0", "m0fo", "m45terbate", "ma5terb8", "ma5terbate", "masochist", "master-bate", "masterb8", "masterbat*", "masterbat3", "masterbate", "masterbation", "masterbations", "masturbate", "mo-fo", "mof0", "mofo", "mothafuck", "mothafucka", "mothafuckas", "mothafuckaz", "mothafucked", "mothafucker", "mothafuckers", "mothafuckin", "mothafucking", "mothafuckings", "mothafucks", "mother fucker", "motherfuck", "motherfucked", "motherfucker", "motherfuckers", "motherfuckin", "motherfucking", "motherfuckings", "motherfuckka", "motherfucks", "muff", "mutha", "muthafecker", "muthafuckker", "muther", "mutherfucker", "n1gga", "n1gger", "nazi", "nigg3r", "nigg4h", "nigga", "niggah", "niggas", "niggaz", "nigger", "niggers", "nob", "nob jokey", "nobhead", "nobjocky", "nobjokey", "numbnuts", "nutsack", "orgasim", "orgasims", "orgasm", "orgasms", "p0rn", "pawn", "pecker", "penis", "penisfucker", "phonesex", "phuck", "phuk", "phuked", "phuking", "phukked", "phukking", "phuks", "phuq", "pigfucker", "pimpis", "piss", "pissed", "pisser", "pissers", "pisses", "pissflaps", "pissin", "pissing", "pissoff", "poop", "porn", "porno", "pornography", "pornos", "prick", "pricks", "pron", "pube", "pusse", "pussi", "pussies", "pussy", "pussys", "rectum", "retard", "rimjaw", "rimming", "s hit", "s.o.b.", "sadist", "schlong", "screwing", "scroat", "scrote", "scrotum", "semen", "sex", "sh!+", "sh!t", "sh1t", "shag", "shagger", "shaggin", "shagging", "shemale", "shi+", "shit", "shitdick", "shite", "shited", "shitey", "shitfuck", "shitfull", "shithead", "shiting", "shitings", "shits", "shitted", "shitter", "shitters", "shitting", "shittings", "shitty", "skank", "slut", "sluts", "smegma", "smut", "snatch", "son-of-a-bitch", "spac", "spunk", "s_h_i_t", "t1tt1e5", "t1tties", "teets", "teez", "testical", "testicle", "tit", "titfuck", "tits", "titt", "tittie5", "tittiefucker", "titties", "tittyfuck", "tittywank", "titwank", "tosser", "turd", "tw4t", "twat", "twathead", "twatty", "twunt", "twunter", "v14gra", "v1gra", "vagina", "viagra", "vulva", "w00se", "wang", "wank", "wanker", "wanky", "whoar", "whore", "willies", "willy", "xrated", "xxx"]
        for regx in badword:
            regx = " " + regx + " "
            finalMessage = ""
            stars = ""
            #object that stores the first occurence of matched regex string
            match = re.search(regx,message)
            while(match):
                finalMessage += message[0:match.span()[0]]
                stars = ""
                #finalMessage += match.group()[2:len(match.group())-2]
                for i in range (0,len(match.group())):
                    stars += "*"
                finalMessage += " " + stars[1:len(stars)-1] + " "
                message = message[match.span()[1]:]
                match = re.search(regx,message)
            if(len(message) > 0):
                finalMessage += message
            message = finalMessage
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
