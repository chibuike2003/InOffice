from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from jinja2 import DictLoader
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'inoffice_secret_key_change_me'

# Email Configuration (Flask-Mail)
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your_email_password')
mail = Mail(app)

# All HTML templates embedded cleanly using DictLoader
templates = {
    'base': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}InOffice{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-slate-50 font-sans text-slate-800 min-h-screen flex flex-col justify-between">
    <nav class="bg-indigo-600 text-white shadow-md">
        <div class="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
            <a href="{{ url_for('index') }}" class="text-xl font-bold flex items-center gap-2">
                <i class="fa-solid fa-door-open"></i> InOffice
            </a>
            <div class="flex items-center gap-4">
                {% if 'user_id' in session %}
                    <a href="{{ url_for('dashboard') }}" class="hover:underline">Dashboard</a>
                    <a href="{{ url_for('logout') }}" class="bg-indigo-700 px-3 py-1.5 rounded-lg hover:bg-indigo-800 text-sm font-medium">Logout</a>
                {% else %}
                    <a href="{{ url_for('index') }}" class="hover:underline">Home</a>
                    <div class="relative group inline-block">
                        <button class="bg-indigo-500 hover:bg-indigo-700 px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1">
                            Login <i class="fa-solid fa-chevron-down text-xs"></i>
                        </button>
                        <div class="absolute right-0 mt-1 w-40 bg-white text-slate-800 shadow-lg rounded-lg hidden group-hover:block z-50 border border-slate-100">
                            <a href="{{ url_for('student_login') }}" class="block px-4 py-2 hover:bg-indigo-50 text-sm">Student Login</a>
                            <a href="{{ url_for('lecturer_login') }}" class="block px-4 py-2 hover:bg-indigo-50 text-sm border-t border-slate-100">Lecturer Login</a>
                        </div>
                    </div>
                {% endif %}
            </div>
        </div>
    </nav>

    <main class="flex-grow">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="max-w-4xl mx-auto mt-4 px-4">
                    {% for category, message in messages %}
                        <div class="p-4 mb-3 rounded-lg text-sm font-medium {% if category == 'error' %}bg-red-100 text-red-700 border border-red-200{% else %}bg-emerald-100 text-emerald-700 border border-emerald-200{% endif %}">
                            {{ message }}
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </main>

    <footer class="bg-white border-t border-slate-200 py-6 text-center text-sm text-slate-500 mt-12">
        <p>&copy; 2026 InOffice. Real-time availability & direct email alerts for academic consultations.</p>
    </footer>
</body>
</html>''',
    
    'landing': '''{% extends "base" %}
{% block title %}Welcome to InOffice{% endblock %}
{% block content %}
<div class="bg-gradient-to-br from-indigo-600 to-indigo-800 text-white py-20 px-4 text-center">
    <div class="max-w-3xl mx-auto">
        <h1 class="text-4xl md:text-5xl font-extrabold mb-6 tracking-tight">Know When Your Lecturer is In Office</h1>
        <p class="text-lg md:text-xl text-indigo-100 mb-8">Stop walking to empty offices. Check real-time availability, send direct visit requests, and get instant email updates.</p>
        <div class="flex flex-col sm:flex-row justify-center gap-6">
            <div class="bg-white/10 p-6 rounded-2xl backdrop-blur-sm border border-white/20 flex-1">
                <h3 class="font-bold text-lg mb-2 text-indigo-200"><i class="fa-solid fa-user-graduate"></i> Students</h3>
                <p class="text-sm text-indigo-100 mb-4">Check lecturer presence, send visit inquiries, and receive direct email replies.</p>
                <div class="flex justify-center gap-2">
                    <a href="{{ url_for('student_signup') }}" class="bg-white text-indigo-700 px-4 py-2 rounded-lg font-semibold hover:bg-indigo-50 text-sm">Register</a>
                    <a href="{{ url_for('student_login') }}" class="bg-indigo-700 text-white px-4 py-2 rounded-lg font-semibold hover:bg-indigo-800 text-sm border border-indigo-500">Login</a>
                </div>
            </div>
            <div class="bg-white/10 p-6 rounded-2xl backdrop-blur-sm border border-white/20 flex-1">
                <h3 class="font-bold text-lg mb-2 text-indigo-200"><i class="fa-solid fa-chalkboard-user"></i> Lecturers</h3>
                <p class="text-sm text-indigo-100 mb-4">Toggle your office status with one click and respond instantly to student inquiries.</p>
                <div class="flex justify-center gap-2">
                    <a href="{{ url_for('lecturer_signup') }}" class="bg-white text-indigo-700 px-4 py-2 rounded-lg font-semibold hover:bg-indigo-50 text-sm">Register</a>
                    <a href="{{ url_for('lecturer_login') }}" class="bg-indigo-700 text-white px-4 py-2 rounded-lg font-semibold hover:bg-indigo-800 text-sm border border-indigo-500">Login</a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}''',

    'student_signup': '''{% extends "base" %}
{% block title %}Student Signup{% endblock %}
{% block content %}
<div class="max-w-md mx-auto my-10 bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
    <h2 class="text-2xl font-bold text-slate-800 mb-6 text-center">Student Registration</h2>
    <form method="POST" class="space-y-4">
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
            <input type="text" name="name" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">EG Number (Reg No)</label>
            <input type="text" name="eg_number" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g. EG/2022/1234">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
            <input type="email" name="email" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Phone Number</label>
            <input type="text" name="phone" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Faculty</label>
            <input type="text" name="faculty" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g. Engineering">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Department</label>
            <input type="text" name="department" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g. Computer Engineering">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Password</label>
            <input type="password" name="password" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none">
        </div>
        <button type="submit" class="w-full bg-indigo-600 text-white py-2.5 rounded-lg font-semibold hover:bg-indigo-700 transition">Create Account</button>
    </form>
    <p class="text-center text-sm text-slate-600 mt-4">Already have an account? <a href="{{ url_for('student_login') }}" class="text-indigo-600 font-semibold hover:underline">Login here</a></p>
</div>
{% endblock %}''',

    'student_login': '''{% extends "base" %}
{% block title %}Student Login{% endblock %}
{% block content %}
<div class="max-w-md mx-auto mt-16 bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
    <h2 class="text-2xl font-bold text-slate-800 mb-6 text-center">Student Login</h2>
    <form method="POST" class="space-y-4">
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">EG Number, Email, or Phone</label>
            <input type="text" name="identity" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="Enter EG No, email or phone">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Password</label>
            <input type="password" name="password" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none">
        </div>
        <button type="submit" class="w-full bg-indigo-600 text-white py-2.5 rounded-lg font-semibold hover:bg-indigo-700 transition">Login</button>
    </form>
    <p class="text-center text-sm text-slate-600 mt-4">Don't have an account? <a href="{{ url_for('student_signup') }}" class="text-indigo-600 font-semibold hover:underline">Register here</a></p>
</div>
{% endblock %}''',

    'lecturer_signup': '''{% extends "base" %}
{% block title %}Lecturer Signup{% endblock %}
{% block content %}
<div class="max-w-md mx-auto my-10 bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
    <h2 class="text-2xl font-bold text-slate-800 mb-6 text-center">Lecturer Registration</h2>
    <form method="POST" class="space-y-4">
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Full Name & Title</label>
            <input type="text" name="name" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g. Dr. John Doe">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Staff ID</label>
            <input type="text" name="staff_id" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g. LEC/2020/55">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
            <input type="email" name="email" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Phone Number</label>
            <input type="text" name="phone" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Faculty</label>
            <input type="text" name="faculty" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g. Engineering">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Department</label>
            <input type="text" name="department" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g. Computer Engineering">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Password</label>
            <input type="password" name="password" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none">
        </div>
        <button type="submit" class="w-full bg-indigo-600 text-white py-2.5 rounded-lg font-semibold hover:bg-indigo-700 transition">Create Account</button>
    </form>
    <p class="text-center text-sm text-slate-600 mt-4">Already have an account? <a href="{{ url_for('lecturer_login') }}" class="text-indigo-600 font-semibold hover:underline">Login here</a></p>
</div>
{% endblock %}''',

    'lecturer_login': '''{% extends "base" %}
{% block title %}Lecturer Login{% endblock %}
{% block content %}
<div class="max-w-md mx-auto mt-16 bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
    <h2 class="text-2xl font-bold text-slate-800 mb-6 text-center">Lecturer Login</h2>
    <form method="POST" class="space-y-4">
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Staff ID or Email</label>
            <input type="text" name="identity" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="Enter Staff ID or email">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Password</label>
            <input type="password" name="password" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none">
        </div>
        <button type="submit" class="w-full bg-indigo-600 text-white py-2.5 rounded-lg font-semibold hover:bg-indigo-700 transition">Login</button>
    </form>
    <p class="text-center text-sm text-slate-600 mt-4">Don't have an account? <a href="{{ url_for('lecturer_signup') }}" class="text-indigo-600 font-semibold hover:underline">Register here</a></p>
</div>
{% endblock %}''',

    'student_dashboard': '''{% extends "base" %}
{% block title %}Student Dashboard{% endblock %}
{% block content %}
<div class="max-w-6xl mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-8">
        <div>
            <h1 class="text-2xl font-bold text-slate-800">Welcome, {{ user.name }}</h1>
            <p class="text-slate-500 text-sm">EG No: {{ user.eg_number }} | Dept: {{ user.department }}</p>
        </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <!-- Lecturer Directory -->
        <div class="md:col-span-2 space-y-6">
            <h2 class="text-xl font-bold text-slate-800 flex items-center gap-2"><i class="fa-solid fa-chalkboard-user text-indigo-600"></i> Lecturers Directory</h2>
            
            <div class="grid grid-cols-1 gap-4">
                {% for lec in lecturers %}
                <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                        <div class="flex items-center gap-3">
                            <h3 class="font-bold text-lg text-slate-800">{{ lec.name }}</h3>
                            <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold {% if lec.is_in_office %}bg-emerald-100 text-emerald-700{% else %}bg-amber-100 text-amber-700{% endif %}">
                                <i class="fa-solid fa-circle text-[8px] mr-1"></i> {% if lec.is_in_office %}In Office{% else %}Not In Office{% endif %}
                            </span>
                        </div>
                        <p class="text-sm text-slate-500 mt-0.5">{{ lec.department }} ({{ lec.faculty }})</p>
                        <p class="text-xs text-slate-400 mt-1"><i class="fa-regular fa-envelope"></i> {{ lec.email }}</p>
                    </div>
                    
                    <button onclick="openModal('{{ lec.id }}', '{{ lec.name }}')" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition w-full sm:w-auto">
                        <i class="fa-solid fa-paper-plane mr-1"></i> Ask to Visit
                    </button>
                </div>
                {% else %}
                <p class="text-slate-500 bg-white p-6 rounded-xl border text-center">No lecturers registered yet.</p>
                {% endfor %}
            </div>
        </div>

        <!-- My Visit Inquiries -->
        <div>
            <h2 class="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2"><i class="fa-solid fa-clock-rotate-left text-indigo-600"></i> My Inquiries</h2>
            <div class="space-y-3">
                {% for req in requests %}
                <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-200 text-sm">
                    <div class="flex justify-between items-start mb-1">
                        <span class="font-bold text-slate-800">{{ req.lecturer_name }}</span>
                        <span class="px-2 py-0.5 rounded text-xs font-semibold 
                            {% if req.status == 'Pending' %}bg-amber-100 text-amber-700
                            {% elif req.status == 'Approved' %}bg-emerald-100 text-emerald-700
                            {% else %}bg-red-100 text-red-700{% endif %}">
                            {{ req.status }}
                        </span>
                    </div>
                    <p class="text-slate-600 italic my-1">"{{ req.message }}"</p>
                    {% if req.reply %}
                    <div class="mt-2 pt-2 border-t border-slate-100 bg-slate-50 p-2 rounded text-xs">
                        <strong class="text-indigo-700">Lecturer Reply:</strong> {{ req.reply }}
                    </div>
                    {% endif %}
                    <p class="text-[10px] text-slate-400 mt-2 text-right">{{ req.timestamp }}</p>
                </div>
                {% else %}
                <p class="text-slate-500 bg-white p-6 rounded-xl border text-center text-sm">No inquiries sent yet.</p>
                {% endfor %}
            </div>
        </div>
    </div>
</div>

<!-- Visit Request Modal -->
<div id="visitModal" class="fixed inset-0 bg-slate-900/50 hidden items-center justify-center z-50 p-4">
    <div class="bg-white max-w-md w-full p-6 rounded-2xl shadow-xl">
        <h3 class="text-xl font-bold text-slate-800 mb-2" id="modalTitle">Ask Lecturer to Visit</h3>
        <p class="text-sm text-slate-500 mb-4">Send a direct visit inquiry and email notification to the lecturer.</p>
        <form method="POST" action="{{ url_for('send_request') }}">
            <input type="hidden" name="lecturer_id" id="modalLecturerId">
            <div class="mb-4">
                <label class="block text-sm font-medium text-slate-700 mb-1">Message / Purpose of Visit</label>
                <textarea name="message" rows="4" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g., Hello sir, I would like to discuss my project topic at 2 PM today..."></textarea>
            </div>
            <div class="flex justify-end gap-2">
                <button type="button" onclick="closeModal()" class="px-4 py-2 border rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50">Cancel</button>
                <button type="submit" class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700">Send Inquiry</button>
            </div>
        </form>
    </div>
</div>

<script>
function openModal(lecturerId, lecturerName) {
    document.getElementById('modalLecturerId').value = lecturerId;
    document.getElementById('modalTitle').innerText = 'Ask ' + lecturerName + ' to Visit';
    document.getElementById('visitModal').classList.remove('hidden');
    document.getElementById('visitModal').classList.add('flex');
}
function closeModal() {
    document.getElementById('visitModal').classList.remove('flex');
    document.getElementById('visitModal').classList.add('hidden');
}
</script>
{% endblock %}''',

    'lecturer_dashboard': '''{% extends "base" %}
{% block title %}Lecturer Dashboard{% endblock %}
{% block content %}
<div class="max-w-6xl mx-auto px-4 py-8">
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div>
            <h1 class="text-2xl font-bold text-slate-800">{{ user.name }}</h1>
            <p class="text-slate-500 text-sm">Staff ID: {{ user.staff_id }} | Dept: {{ user.department }}</p>
        </div>
        
        <!-- Office Status Toggle -->
        <form method="POST" action="{{ url_for('toggle_status') }}" class="flex items-center gap-3">
            <span class="text-sm font-medium text-slate-700">Office Status:</span>
            <button type="submit" class="px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2 transition {% if user.is_in_office %}bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-200 shadow-lg{% else %}bg-slate-200 hover:bg-slate-300 text-slate-700{% endif %}">
                <i class="fa-solid fa-circle text-xs"></i>
                {% if user.is_in_office %}I am IN OFFICE{% else %}I am OUT OF OFFICE{% endif %}
            </button>
        </form>
    </div>

    <h2 class="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2"><i class="fa-solid fa-inbox text-indigo-600"></i> Student Visit Inquiries</h2>
    
    <div class="grid grid-cols-1 gap-4">
        {% for req in requests %}
        <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div class="space-y-1">
                <div class="flex items-center gap-3">
                    <h3 class="font-bold text-lg text-slate-800">{{ req.student_name }}</h3>
                    <span class="px-2 py-0.5 bg-indigo-50 text-indigo-700 text-xs font-semibold rounded">{{ req.eg_number }}</span>
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold 
                        {% if req.status == 'Pending' %}bg-amber-100 text-amber-700
                        {% elif req.status == 'Approved' %}bg-emerald-100 text-emerald-700
                        {% else %}bg-red-100 text-red-700{% endif %}">
                        {{ req.status }}
                    </span>
                </div>
                <p class="text-xs text-slate-500"><i class="fa-solid fa-building-columns mr-1"></i> Dept: {{ req.department }} | <i class="fa-solid fa-phone mr-1"></i> {{ req.phone }} | <i class="fa-solid fa-envelope mr-1"></i> {{ req.email }}</p>
                <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 text-slate-700 text-sm mt-2">
                    <strong class="text-slate-900 block mb-1">Inquiry Message:</strong>
                    "{{ req.message }}"
                </div>
                {% if req.reply %}
                <p class="text-xs text-indigo-600 mt-1"><strong>Your Response:</strong> {{ req.reply }}</p>
                {% endif %}
                <p class="text-[10px] text-slate-400 mt-1">Received: {{ req.timestamp }}</p>
            </div>

            <!-- Action buttons / response form -->
            <div class="w-full md:w-auto flex flex-col sm:flex-row gap-2">
                {% if req.status == 'Pending' %}
                <form method="POST" action="{{ url_for('respond_request', req_id=req.id) }}" class="flex flex-col sm:flex-row gap-2 w-full">
                    <input type="text" name="reply" placeholder="Quick note (e.g., Come over now)" required class="px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-indigo-500">
                    <button type="submit" name="action" value="Approved" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition">Approve</button>
                    <button type="submit" name="action" value="Declined" class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition">Decline</button>
                </form>
                {% else %}
                <span class="text-sm font-medium text-slate-400 italic">Responded</span>
                {% endif %}
            </div>
        </div>
        {% else %}
        <p class="text-slate-500 bg-white p-8 rounded-2xl border text-center">No student inquiries received yet.</p>
        {% endfor %}
    </div>
</div>
{% endblock %}'''
}

# Attach DictLoader so Flask resolves template inheritance without physical files
app.jinja_loader = DictLoader(templates)

# Database Helper
def init_db():
    conn = sqlite3.connect('inoffice.db')
    c = conn.cursor()
    # Students table
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                eg_number TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                faculty TEXT NOT NULL,
                department TEXT NOT NULL,
                password TEXT NOT NULL)''')
    # Lecturers table
    c.execute('''CREATE TABLE IF NOT EXISTS lecturers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                staff_id TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                faculty TEXT NOT NULL,
                department TEXT NOT NULL,
                password TEXT NOT NULL,
                is_in_office INTEGER DEFAULT 0)''')
    # Visit requests table
    c.execute('''CREATE TABLE IF NOT EXISTS visit_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                lecturer_id INTEGER,
                message TEXT,
                status TEXT DEFAULT 'Pending',
                reply TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# Helper function to send email notifications
def send_email(subject, recipient, body):
    try:
        msg = Message(subject, sender=app.config.get('MAIL_USERNAME', 'noreply@inoffice.com'), recipients=[recipient])
        msg.body = body
        mail.send(msg)
    except Exception as e:
        print(f"Email delivery note (SMTP not fully configured): {e}")

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing')

@app.route('/student/signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        name = request.form['name']
        eg_number = request.form['eg_number']
        email = request.form['email']
        phone = request.form['phone']
        faculty = request.form['faculty']
        department = request.form['department']
        password = generate_password_hash(request.form['password'])

        try:
            conn = sqlite3.connect('inoffice.db')
            c = conn.cursor()
            c.execute("INSERT INTO students (name, eg_number, email, phone, faculty, department, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (name, eg_number, email, phone, faculty, department, password))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('student_login'))
        except sqlite3.IntegrityError:
            flash('EG Number or Email already exists.', 'error')
    return render_template('student_signup')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        identity = request.form['identity']
        password = request.form['password']

        conn = sqlite3.connect('inoffice.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM students WHERE eg_number = ? OR email = ? OR phone = ?", (identity, identity, identity))
        student = c.fetchone()
        conn.close()

        if student and check_password_hash(student['password'], password):
            session['user_id'] = student['id']
            session['role'] = 'student'
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please check your EG No, email/phone and password.', 'error')
    return render_template('student_login')

@app.route('/lecturer/signup', methods=['GET', 'POST'])
def lecturer_signup():
    if request.method == 'POST':
        name = request.form['name']
        staff_id = request.form['staff_id']
        email = request.form['email']
        phone = request.form['phone']
        faculty = request.form['faculty']
        department = request.form['department']
        password = generate_password_hash(request.form['password'])

        try:
            conn = sqlite3.connect('inoffice.db')
            c = conn.cursor()
            c.execute("INSERT INTO lecturers (name, staff_id, email, phone, faculty, department, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (name, staff_id, email, phone, faculty, department, password))
            conn.commit()
            conn.close()
            flash('Lecturer registration successful! Please login.', 'success')
            return redirect(url_for('lecturer_login'))
        except sqlite3.IntegrityError:
            flash('Staff ID or Email already exists.', 'error')
    return render_template('lecturer_signup')

@app.route('/lecturer/login', methods=['GET', 'POST'])
def lecturer_login():
    if request.method == 'POST':
        identity = request.form['identity']
        password = request.form['password']

        conn = sqlite3.connect('inoffice.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM lecturers WHERE staff_id = ? OR email = ?", (identity, identity))
        lecturer = c.fetchone()
        conn.close()

        if lecturer and check_password_hash(lecturer['password'], password):
            session['user_id'] = lecturer['id']
            session['role'] = 'lecturer'
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please check your Staff ID/email and password.', 'error')
    return render_template('lecturer_login')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    conn = sqlite3.connect('inoffice.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if session['role'] == 'student':
        c.execute("SELECT * FROM students WHERE id = ?", (session['user_id'],))
        user = c.fetchone()
        c.execute("SELECT * FROM lecturers")
        lecturers = c.fetchall()
        c.execute('''SELECT vr.*, l.name as lecturer_name FROM visit_requests vr 
                     JOIN lecturers l ON vr.lecturer_id = l.id 
                     WHERE vr.student_id = ? ORDER BY vr.id DESC''', (session['user_id'],))
        requests = c.fetchall()
        conn.close()
        return render_template('student_dashboard', user=user, lecturers=lecturers, requests=requests)
    
    elif session['role'] == 'lecturer':
        c.execute("SELECT * FROM lecturers WHERE id = ?", (session['user_id'],))
        user = c.fetchone()
        c.execute('''SELECT vr.*, s.name as student_name, s.eg_number, s.email, s.phone, s.department 
                     FROM visit_requests vr 
                     JOIN students s ON vr.student_id = s.id 
                     WHERE vr.lecturer_id = ? ORDER BY vr.id DESC''', (session['user_id'],))
        requests = c.fetchall()
        conn.close()
        return render_template('lecturer_dashboard', user=user, requests=requests)

@app.route('/student/request', methods=['POST'])
def send_request():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('index'))

    student_id = session['user_id']
    lecturer_id = request.form['lecturer_id']
    message = request.form['message']

    conn = sqlite3.connect('inoffice.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("INSERT INTO visit_requests (student_id, lecturer_id, message) VALUES (?, ?, ?)", (student_id, lecturer_id, message))
    
    # Fetch details for email
    c.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = c.fetchone()
    c.execute("SELECT * FROM lecturers WHERE id = ?", (lecturer_id,))
    lecturer = c.fetchone()
    conn.commit()
    conn.close()

    # Send email alert to lecturer
    email_subject = f"InOffice Visit Inquiry from {student['name']} ({student['eg_number']})"
    email_body = f"Hello {lecturer['name']},\n\nStudent {student['name']} ({student['eg_number']}, Department: {student['department']}) has sent a visit inquiry:\n\n\"{message}\"\n\nPlease log in to your InOffice dashboard to approve or decline."
    send_email(email_subject, lecturer['email'], email_body)

    flash('Visit inquiry and email notification sent successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/lecturer/toggle', methods=['POST'])
def toggle_status():
    if 'user_id' not in session or session['role'] != 'lecturer':
        return redirect(url_for('index'))

    conn = sqlite3.connect('inoffice.db')
    c = conn.cursor()
    c.execute("UPDATE lecturers SET is_in_office = CASE WHEN is_in_office = 1 THEN 0 ELSE 1 END WHERE id = ?", (session['user_id'],))
    conn.commit()
    conn.close()
    flash('Office status updated successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/lecturer/respond/<int:req_id>', methods=['POST'])
def respond_request(req_id):
    if 'user_id' not in session or session['role'] != 'lecturer':
        return redirect(url_for('index'))

    action = request.form['action'] # 'Approved' or 'Declined'
    reply_msg = request.form['reply']

    conn = sqlite3.connect('inoffice.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("UPDATE visit_requests SET status = ?, reply = ? WHERE id = ? AND lecturer_id = ?", (action, reply_msg, req_id, session['user_id']))
    
    # Fetch request, student, and lecturer details for email notification
    c.execute('''SELECT vr.*, s.email as student_email, s.name as student_name, l.name as lecturer_name 
                 FROM visit_requests vr 
                 JOIN students s ON vr.student_id = s.id 
                 JOIN lecturers l ON vr.lecturer_id = l.id 
                 WHERE vr.id = ?''', (req_id,))
    req_data = c.fetchone()
    conn.commit()
    conn.close()

    if req_data:
        email_subject = f"InOffice Visit Inquiry {action}: {req_data['lecturer_name']}"
        email_body = f"Hello {req_data['student_name']},\n\nYour visit inquiry to {req_data['lecturer_name']} has been {action}.\n\nLecturer Note: \"{reply_msg}\"\n\nLog in to InOffice for more details."
        send_email(email_subject, req_data['student_email'], email_body)

    flash(f'Inquiry {action.lower()} and student notified via email.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)