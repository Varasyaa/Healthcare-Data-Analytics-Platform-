import datetime, jwt, os
from functools import wraps
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# Configure your PostgreSQL database URI (adjust username, password, and db name)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/healthcare_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-super-secret-key'

db = SQLAlchemy(app)

# -------------------------------
# Database Models
# -------------------------------

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    visits = db.relationship('Visit', backref='patient', lazy=True)
    lab_results = db.relationship('LabResult', backref='patient', lazy=True)

class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    specialization = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    visits = db.relationship('Visit', backref='doctor', lazy=True)

class Visit(db.Model):
    __tablename__ = 'visits'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    visit_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    diagnosis = db.Column(db.Text)
    treatment = db.Column(db.Text)

class LabResult(db.Model):
    __tablename__ = 'lab_results'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    test_type = db.Column(db.String(100))
    test_date = db.Column(db.Date, nullable=False)
    result_value = db.Column(db.Numeric(10,2))
    units = db.Column(db.String(20))
    reference_range = db.Column(db.String(50))

# For simplicity, we add a User model for authentication (for platform administrators)
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# -------------------------------
# JWT Helper Functions
# -------------------------------

def encode_auth_token(user_id):
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    except Exception as e:
        return None

def decode_auth_token(auth_token):
    try:
        payload = jwt.decode(auth_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            # Expected format: "Bearer <token>"
            parts = request.headers.get('Authorization').split()
            if len(parts) == 2:
                token = parts[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        user_id = decode_auth_token(token)
        if not user_id:
            return jsonify({'message': 'Token is invalid or expired!'}), 401
        return f(user_id, *args, **kwargs)
    return decorated

# -------------------------------
# API Endpoints
# -------------------------------

# User Registration & Login for Admins
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'message': 'User already exists'}), 400
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid credentials'}), 401
    token = encode_auth_token(user.id)
    return jsonify({'token': token}), 200

# Endpoint to ingest new patient data
@app.route('/api/patients', methods=['POST'])
@token_required
def add_patient(current_user_id):
    data = request.json
    new_patient = Patient(
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        date_of_birth=data.get('date_of_birth'),
        gender=data.get('gender')
    )
    db.session.add(new_patient)
    db.session.commit()
    return jsonify({'message': 'Patient added', 'patient_id': new_patient.id}), 201

# Endpoint to add a visit record
@app.route('/api/visits', methods=['POST'])
@token_required
def add_visit(current_user_id):
    data = request.json
    new_visit = Visit(
        patient_id=data.get('patient_id'),
        doctor_id=data.get('doctor_id'),
        visit_date=data.get('visit_date') or datetime.datetime.utcnow(),
        diagnosis=data.get('diagnosis'),
        treatment=data.get('treatment')
    )
    db.session.add(new_visit)
    db.session.commit()
    return jsonify({'message': 'Visit recorded', 'visit_id': new_visit.id}), 201

# Endpoint to add a lab result
@app.route('/api/lab-results', methods=['POST'])
@token_required
def add_lab_result(current_user_id):
    data = request.json
    new_lab = LabResult(
        patient_id=data.get('patient_id'),
        test_type=data.get('test_type'),
        test_date=data.get('test_date'),
        result_value=data.get('result_value'),
        units=data.get('units'),
        reference_range=data.get('reference_range')
    )
    db.session.add(new_lab)
    db.session.commit()
    return jsonify({'message': 'Lab result added', 'lab_result_id': new_lab.id}), 201

# Endpoint to retrieve patient analytics (example: number of visits per patient)
@app.route('/api/analytics/visits-per-patient', methods=['GET'])
@token_required
def visits_per_patient(current_user_id):
    results = db.session.query(
        Patient.first_name,
        Patient.last_name,
        db.func.count(Visit.id).label('visit_count')
    ).join(Visit, Patient.id == Visit.patient_id)\
     .group_by(Patient.id).all()
    data = [{'patient': f"{r.first_name} {r.last_name}", 'visit_count': r.visit_count} for r in results]
    return jsonify(data)

# Endpoint to retrieve lab result analytics (example: average result for a test type)
@app.route('/api/analytics/average-lab-result/<test_type>', methods=['GET'])
@token_required
def average_lab_result(current_user_id, test_type):
    avg_result = db.session.query(db.func.avg(LabResult.result_value))\
        .filter(LabResult.test_type == test_type).scalar()
    return jsonify({'test_type': test_type, 'average_result': float(avg_result) if avg_result else None})

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, port=5000)
