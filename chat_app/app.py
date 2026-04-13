from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, decode_token
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['JWT_SECRET_KEY'] = 'jwt-secret'

db = SQLAlchemy(app)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ================= MODELS ================= #

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    status = db.Column(db.String(20), default="offline")
    last_seen = db.Column(db.DateTime)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer)
    receiver_id = db.Column(db.Integer)
    content = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)

class GroupMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer)
    sender_id = db.Column(db.Integer)
    content = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ================= ROUTES ================= #

@app.route('/')
def home():
    return render_template("login.html")

@app.route('/register_page')
def register_page():
    return render_template("register.html")

@app.route('/chat')
def chat():
    return render_template("chat.html")

# ================= AUTH ================= #

@app.route('/register', methods=['POST'])
def register():
    data = request.json

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "User already exists"}), 400

    user = User(username=data['username'], password=data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "Registered successfully"})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()

    if not user or user.password != data['password']:
        return jsonify({"msg": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id))

    return jsonify({
        "token": token,
        "user_id": user.id,
        "username": user.username
    })

# ================= USERS ================= #

@app.route('/users')
@jwt_required()
def users():
    current = int(get_jwt_identity())

    users = User.query.filter(User.id != current).all()

    return jsonify([
        {
            "id": u.id,
            "username": u.username,
            "status": u.status,
            "last_seen": str(u.last_seen)
        }
        for u in users
    ])

# ================= PRIVATE CHAT ================= #

@app.route('/messages/<int:user_id>')
@jwt_required()
def messages(user_id):
    current = int(get_jwt_identity())

    msgs = Message.query.filter(
        ((Message.sender_id == current) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current))
    ).order_by(Message.timestamp).all()

    return jsonify([
        {"sender": m.sender_id, "text": m.content}
        for m in msgs
    ])

# ================= GROUP ================= #

@app.route('/create_group', methods=['POST'])
@jwt_required()
def create_group():
    data = request.json
    creator = int(get_jwt_identity())

    group = Group(name=data['name'])
    db.session.add(group)
    db.session.commit()

    db.session.add(GroupMember(group_id=group.id, user_id=creator))

    for uid in data['members']:
        db.session.add(GroupMember(group_id=group.id, user_id=uid))

    db.session.commit()

    return jsonify({"msg": "Group created"})

@app.route('/groups')
@jwt_required()
def groups():
    user_id = int(get_jwt_identity())

    memberships = GroupMember.query.filter_by(user_id=user_id).all()

    result = []
    for m in memberships:
        g = Group.query.get(m.group_id)
        result.append({"id": g.id, "name": g.name})

    return jsonify(result)

@app.route('/group_messages/<int:group_id>')
def group_messages(group_id):
    msgs = GroupMessage.query.filter_by(group_id=group_id)\
        .order_by(GroupMessage.timestamp).all()

    result = []
    for m in msgs:
        user = User.query.get(m.sender_id)
        result.append({
            "sender_id": m.sender_id,
            "sender_name": user.username,
            "text": m.content
        })

    return jsonify(result)
@app.route('/delete_group/<int:group_id>', methods=['DELETE'])
@jwt_required()
def delete_group(group_id):
    # delete members
    GroupMember.query.filter_by(group_id=group_id).delete()

    # delete messages
    GroupMessage.query.filter_by(group_id=group_id).delete()

    # delete group
    Group.query.filter_by(id=group_id).delete()

    db.session.commit()

    return jsonify({"msg": "Group deleted"})



@app.route('/group_members/<int:group_id>', methods=['GET'])
@jwt_required()
def group_members(group_id):
    current_user = int(get_jwt_identity())

    # 🔐 check user is part of group
    member = GroupMember.query.filter_by(
        group_id=group_id,
        user_id=current_user
    ).first()

    if not member:
        return jsonify({"msg": "Access denied"}), 403

    members = GroupMember.query.filter_by(group_id=group_id).all()

    result = []
    for m in members:
        user = User.query.get(m.user_id)
        if user:
            result.append({
                "id": user.id,
                "username": user.username
            })

    return jsonify(result)


@app.route('/remove_member', methods=['POST'])
@jwt_required()
def remove_member():
    data = request.json

    GroupMember.query.filter_by(
        group_id=data['group_id'],
        user_id=data['user_id']
    ).delete()

    db.session.commit()

    return jsonify({"msg": "User removed"})

# ================= SOCKET ================= #

online_users = {}

@socketio.on('connect_user')
def connect_user(data):
    user_id = int(decode_token(data['token'])['sub'])
    online_users[user_id] = request.sid

    user = User.query.get(user_id)
    user.status = "online"
    db.session.commit()

    emit('user_status', {"user_id": user_id, "status": "online"}, broadcast=True)

@socketio.on('send_message')
def send_message(data):
    sender = int(decode_token(data['token'])['sub'])

    db.session.add(Message(
        sender_id=sender,
        receiver_id=int(data['receiver']),
        content=data['message']
    ))
    db.session.commit()

    if int(data['receiver']) in online_users:
        emit('receive_message', {
            "sender": sender,
            "message": data['message']
        }, room=online_users[int(data['receiver'])])

@socketio.on('send_group_message')
def send_group_message(data):
    sender = int(decode_token(data['token'])['sub'])

    db.session.add(GroupMessage(
        group_id=data['group_id'],
        sender_id=sender,
        content=data['message']
    ))
    db.session.commit()

    user = User.query.get(sender)

    members = GroupMember.query.filter_by(group_id=data['group_id']).all()

    for m in members:
        if m.user_id in online_users:
            emit('receive_group_message', {
                "group_id": data['group_id'],
                "sender_id": sender,
                "sender_name": user.username,
                "message": data['message']
            }, room=online_users[m.user_id])

@socketio.on('disconnect')
def disconnect():
    for user_id, sid in list(online_users.items()):
        if sid == request.sid:
            user = User.query.get(user_id)
            user.status = "offline"
            user.last_seen = datetime.utcnow()
            db.session.commit()

            del online_users[user_id]

            emit('user_status', {"user_id": user_id, "status": "offline"}, broadcast=True)

# ================= RUN ================= #

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    socketio.run(app, debug=True, port=5002)




