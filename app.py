from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import qrcode
import qrcode.constants
import json
import io
import base64
import uuid
import re
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendease.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# Database Models
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    emp_id = db.Column(db.String(50), unique=True, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    course = db.Column(db.String(50), nullable=False)
    year = db.Column(db.String(20), nullable=False)
    section = db.Column(db.String(20), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)

class AttendanceSession(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    class_section = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), db.ForeignKey('attendance_session.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)

# Helper function
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Routes
@app.route('/')
def home():
    return jsonify({'message': 'AttendEase API is running!', 'status': 'success'})

@app.route('/api/register/teacher', methods=['POST'])
def register_teacher():
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['fullname', 'email', 'password', 'department', 'emp_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if teacher exists
        if Teacher.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        if Teacher.query.filter_by(emp_id=data['emp_id']).first():
            return jsonify({'error': 'Employee ID already exists'}), 400
        
        # Create teacher
        teacher = Teacher(
            fullname=data['fullname'],
            email=data['email'].lower(),
            department=data['department'],
            emp_id=data['emp_id']
        )
        teacher.set_password(data['password'])
        
        db.session.add(teacher)
        db.session.commit()
        
        return jsonify({'message': 'Teacher registered successfully'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/register/student', methods=['POST'])
def register_student():
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['fullname', 'email', 'password', 'roll_no', 'course', 'year', 'section']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if student exists
        if Student.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        if Student.query.filter_by(roll_no=data['roll_no']).first():
            return jsonify({'error': 'Roll number already exists'}), 400
        
        # Create student
        student = Student(
            fullname=data['fullname'],
            email=data['email'].lower(),
            roll_no=data['roll_no'],
            course=data['course'],
            year=data['year'],
            section=data['section']
        )
        student.set_password(data['password'])
        
        db.session.add(student)
        db.session.commit()
        
        return jsonify({'message': 'Student registered successfully'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        user_type = data.get('type')
        email = data.get('email', '').lower()
        password = data.get('password', '')
        
        if not all([user_type, email, password]):
            return jsonify({'error': 'All fields are required'}), 400
        
        user = None
        if user_type == 'teacher':
            user = Teacher.query.filter_by(email=email).first()
        elif user_type == 'student':
            user = Student.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'fullname': user.fullname,
                'email': user.email,
                'type': user_type
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/teacher/subjects', methods=['GET'])
def get_subjects():
    try:
        teacher_id = request.args.get('teacher_id')
        if not teacher_id:
            return jsonify({'error': 'Teacher ID required'}), 400
        
        subjects = Subject.query.filter_by(teacher_id=teacher_id).all()
        result = [{'id': s.id, 'name': s.name} for s in subjects]
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch subjects'}), 500

@app.route('/api/teacher/subjects', methods=['POST'])
def add_subject():
    try:
        data = request.get_json()
        
        teacher_id = data.get('teacher_id')
        name = data.get('name', '').strip()
        
        if not teacher_id or not name:
            return jsonify({'error': 'Teacher ID and subject name required'}), 400
        
        # Check if subject exists
        existing = Subject.query.filter_by(teacher_id=teacher_id, name=name).first()
        if existing:
            return jsonify({'error': 'Subject already exists'}), 400
        
        subject = Subject(name=name, teacher_id=teacher_id)
        db.session.add(subject)
        db.session.commit()
        
        return jsonify({'message': 'Subject added successfully'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add subject'}), 500

@app.route('/api/teacher/generate-qr', methods=['POST'])
def generate_qr_code():
    try:
        print("🔄 QR Code generation started...")
        data = request.get_json()
        print(f"📥 Received data: {data}")
        
        teacher_id = data.get('teacher_id')
        subject_id = data.get('subject_id')
        class_section = data.get('class_section', '').strip()
        
        print(f"👨‍🏫 Teacher ID: {teacher_id}")
        print(f"📚 Subject ID: {subject_id}")
        print(f"🏫 Class Section: {class_section}")
        
        if not all([teacher_id, subject_id, class_section]):
            print("❌ Missing required fields")
            return jsonify({'error': 'All fields required'}), 400
        
        # Verify teacher and subject
        teacher = Teacher.query.get(teacher_id)
        subject = Subject.query.filter_by(id=subject_id, teacher_id=teacher_id).first()
        
        if not teacher:
            print("❌ Teacher not found")
            return jsonify({'error': 'Teacher not found'}), 404
            
        if not subject:
            print("❌ Subject not found")
            return jsonify({'error': 'Subject not found'}), 404
        
        print(f"✅ Teacher: {teacher.fullname}")
        print(f"✅ Subject: {subject.name}")
        
        # Create session
        session_id = str(uuid.uuid4())
        session = AttendanceSession(
            id=session_id,
            teacher_id=teacher_id,
            subject_id=subject_id,
            class_section=class_section
        )
        
        db.session.add(session)
        db.session.commit()
        print(f"✅ Session created: {session_id}")
        
        # Generate QR data
        qr_data = {
            'session_id': session_id,
            'subject': subject.name,
            'teacher': teacher.fullname,
            'class_section': class_section
        }
        print(f"📋 QR Data: {qr_data}")
        
        try:
            # Create QR code with detailed error handling
            print("🔧 Creating QR Code object...")
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            print("📝 Adding data to QR Code...")
            qr_data_string = json.dumps(qr_data)
            qr.add_data(qr_data_string)
            qr.make(fit=True)
            
            print("🖼️ Creating QR Code image...")
            img = qr.make_image(fill_color="black", back_color="white")
            print("✅ QR image created successfully")
            
            # Convert to base64
            print("🔄 Converting to base64...")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            print("✅ QR code converted to base64")
            
            response_data = {
                'session_id': session_id,
                'qr_code': f'data:image/png;base64,{img_str}',
                'session_info': {
                    'subject': subject.name,
                    'class_section': class_section,
                    'teacher': teacher.fullname
                }
            }
            
            print("🎉 QR Code generation completed successfully!")
            return jsonify(response_data), 200
            
        except Exception as qr_error:
            print(f"❌ QR Code creation error: {qr_error}")
            print(f"❌ Error type: {type(qr_error)}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            return jsonify({'error': f'QR Code generation failed: {str(qr_error)}'}), 500
        
    except Exception as e:
        print(f"❌ General error: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({'error': f'Failed to generate QR code: {str(e)}'}), 500

@app.route('/api/student/mark-attendance', methods=['POST'])
def mark_attendance():
    try:
        data = request.get_json()
        
        qr_data_str = data.get('qr_data')
        student_id = data.get('student_id')
        
        if not qr_data_str or not student_id:
            return jsonify({'error': 'QR data and student ID required'}), 400
        
        # Parse QR data
        try:
            qr_data = json.loads(qr_data_str)
            session_id = qr_data.get('session_id')
        except:
            return jsonify({'error': 'Invalid QR code'}), 400
        
        if not session_id:
            return jsonify({'error': 'Invalid QR code data'}), 400
        
        # Verify session
        session = AttendanceSession.query.filter_by(id=session_id, is_active=True).first()
        if not session:
            return jsonify({'error': 'Session not found or expired'}), 400
        
        # Check if already marked
        existing = Attendance.query.filter_by(session_id=session_id, student_id=student_id).first()
        if existing:
            return jsonify({'error': 'Attendance already marked'}), 400
        
        # Mark attendance
        attendance = Attendance(session_id=session_id, student_id=student_id)
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({'message': 'Attendance marked successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to mark attendance'}), 500

@app.route('/api/teacher/attendance-records', methods=['GET'])
def get_attendance_records():
    try:
        teacher_id = request.args.get('teacher_id')
        if not teacher_id:
            return jsonify({'error': 'Teacher ID required'}), 400
        
        sessions = AttendanceSession.query.filter_by(teacher_id=teacher_id).all()
        
        records = []
        for session in sessions:
            subject = Subject.query.get(session.subject_id)
            attendance_count = Attendance.query.filter_by(session_id=session.id).count()
            
            # Get student details
            attendances = Attendance.query.filter_by(session_id=session.id).all()
            students = []
            for att in attendances:
                student = Student.query.get(att.student_id)
                if student:
                    students.append({
                        'name': student.fullname,
                        'roll_no': student.roll_no,
                        'marked_at': att.marked_at.strftime('%H:%M:%S')
                    })
            
            records.append({
                'session_id': session.id,
                'subject': subject.name if subject else 'Unknown',
                'class_section': session.class_section,
                'date': session.created_at.strftime('%Y-%m-%d'),
                'time': session.created_at.strftime('%H:%M:%S'),
                'attendance_count': attendance_count,
                'students': students
            })
        
        return jsonify(records), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch records'}), 500

@app.route('/api/student/attendance-history', methods=['GET'])
def get_student_history():
    try:
        student_id = request.args.get('student_id')
        if not student_id:
            return jsonify({'error': 'Student ID required'}), 400
        
        attendances = Attendance.query.filter_by(student_id=student_id).all()
        
        history = []
        for att in attendances:
            session = AttendanceSession.query.get(att.session_id)
            if session:
                subject = Subject.query.get(session.subject_id)
                teacher = Teacher.query.get(session.teacher_id)
                
                history.append({
                    'date': session.created_at.strftime('%Y-%m-%d'),
                    'time': session.created_at.strftime('%H:%M:%S'),
                    'subject': subject.name if subject else 'Unknown',
                    'class_section': session.class_section,
                    'teacher': teacher.fullname if teacher else 'Unknown',
                    'marked_at': att.marked_at.strftime('%H:%M:%S')
                })
        
        return jsonify(history), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch history'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database created successfully!")
    
    print("🚀 Starting AttendEase API on http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)