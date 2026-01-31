from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///users.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "super-secret")

# Extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Supabase client
try:
    from supabaseClient import supabase
except Exception as e:
    supabase = None
    print("Warning: supabaseClient.supabase not loaded:", e)

# Blockchain + stego upload logic
try:
    from uploadFile import async_upload_stego_and_insert
except Exception as e:
    async_upload_stego_and_insert = None
    print("Warning: uploadFile.async_upload_stego_and_insert not loaded:", e)

# Upload blueprint
try:
    from stego_routes import upload_bp
except Exception as e:
    upload_bp = None
    print("Warning: stego_routes.upload_bp not loaded:", e)

# Comments blueprint
try:
    from comments_routes import comments_bp
    app.register_blueprint(comments_bp)
except Exception as e:
    print("Warning: comments_routes not loaded:", e)

# Emoji sentiment scoring
emoji_scores = {}
try:
    df = pd.read_csv("Datasets/Emoji_trimmed.csv")
    df['Score'] = df['Positive'] - df['Negative']
    emoji_scores = dict(zip(df['Emoji'], df['Score']))
except Exception as e:
    print("Emoji dataset not loaded:", e)

_analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment_text(text: str):
    score = _analyzer.polarity_scores(text)
    compound = score.get("compound", 0.0)
    for ch in text:
        if ch in emoji_scores:
            compound += emoji_scores[ch]
    score["compound"] = compound
    if compound > 0.05:
        sentiment = "positive"
    elif compound < -0.05:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    return sentiment, score

def _extract_supabase_result(resp):
    if resp is None:
        return None, "No supabase client response"
    if isinstance(resp, dict):
        return resp.get("data"), resp.get("error")
    data = getattr(resp, "data", None)
    error = getattr(resp, "error", None)
    return data, error

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

# Auth routes
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not email or not username or not password:
        return jsonify({"msg": "email, username and password required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already registered"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already exists"}), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(email=email, username=username, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User registered successfully"}), 201

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"msg": "username and password required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"msg": "Invalid credentials"}), 401

    access_token = create_access_token(identity=username, expires_delta=datetime.timedelta(hours=1))
    return jsonify({"access_token": access_token, "username": user.username})

# Sentiment analysis
@app.route('/analyze', methods=['POST'])
@jwt_required()
def analyze():
    data = request.get_json() or {}
    text = data.get('comment', '')
    sentiment, score = analyze_sentiment_text(text)
    return jsonify({'sentiment': sentiment, 'score': score})

# Comments
@app.route('/comments', methods=['POST'])
@jwt_required()
def add_comment():
    if supabase is None:
        return jsonify({"error": "Supabase client not configured"}), 500

    payload = request.get_json() or {}
    jwt_user = get_jwt_identity()

    post_id = payload.get("post_id")
    text = payload.get("text")
    username = payload.get("username") or jwt_user
    avatar_url = payload.get("avatar_url")
    image_url = payload.get("image_url")

    if not post_id or not text or not username:
        return jsonify({"error": "post_id, text and username required"}), 400

    row = {
        "post_id": post_id,
        "username": username,
        "avatar_url": avatar_url,
        "image_url": image_url,
        "text": text
    }

    try:
        resp = supabase.table("comments").insert(row).execute()
    except Exception as e:
        return jsonify({"error": "Supabase insert failed", "detail": str(e)}), 500

    data, error = _extract_supabase_result(resp)
    if error:
        return jsonify({"error": error}), 500

    created = data[0] if isinstance(data, list) and len(data) > 0 else data
    return jsonify({"status": "ok", "comment": created}), 201

@app.route('/comments', methods=['GET'])
def get_comments():
    if supabase is None:
        return jsonify({"error": "Supabase client not configured"}), 500

    post_id = request.args.get("post_id")
    if not post_id:
        return jsonify({"error": "post_id query parameter required"}), 400

    try:
        resp = supabase.table("comments").select("*").eq("post_id", post_id).order("created_at", desc=False).execute()
    except Exception as e:
        return jsonify({"error": "Supabase select failed", "detail": str(e)}), 500

    data, error = _extract_supabase_result(resp)
    if error:
        return jsonify({"error": error}), 500

    return jsonify({"comments": data or []}), 200

# User's uploaded posts
@app.route("/my-posts", methods=["GET"])
@jwt_required()
def get_my_posts():
    username = get_jwt_identity()
    try:
        resp = supabase.table("stego_uploads").select("*").eq("username", username).order("created_at", desc=True).execute()
        data = resp.data
    except Exception as e:
        return jsonify({"error": "Failed to fetch posts", "detail": str(e)}), 500

    return jsonify({"posts": data}), 200

# Health check
@app.route("/health")
def health():
    return "OK", 200

# Register upload blueprint if available
if upload_bp:
    try:
        app.register_blueprint(upload_bp)
    except Exception as e:
        print("Failed to register upload_bp:", e)

# Run the app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
