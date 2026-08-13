import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'ca_foundation_jan2027_super_secret_key'
app.permanent_session_lifetime = timedelta(days=60)  # 60 Days Persistent Login

DB_PATH = os.path.join(os.path.dirname(__file__), 'castudy.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mobile TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            dob TEXT,
            pin TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            user_id INTEGER,
            item_id TEXT,
            status INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, item_id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ==========================================================
# ACCURATE LECTURE SYLLABUS DATA
# ==========================================================
SYLLABUS = {
    "Accounting": [
        {"unit": "Unit 1: Accounts Basics", "lectures": [f"Acc Lec {i}" for i in range(1, 11)]},
        {"unit": "Unit 2: Depreciation & Amortisation", "lectures": [f"Acc Lec {i}" for i in range(11, 18)]},
        {"unit": "Unit 3: Bills of Exchange & Promissory Notes", "lectures": [f"Acc Lec {i}" for i in range(18, 24)]},
        {"unit": "Unit 4: Bank Reconciliation Statement (BRS)", "lectures": [f"Acc Lec {i}" for i in range(24, 29)]},
        {"unit": "Unit 5: Final Accounts of Sole Proprietors", "lectures": [f"Acc Lec {i}" for i in range(29, 38)]},
        {"unit": "Unit 6: Rectification of Errors", "lectures": [f"Acc Lec {i}" for i in range(38, 43)]},
        {"unit": "Unit 7: Accounts from Incomplete Records", "lectures": [f"Acc Lec {i}" for i in range(43, 51)]},
        {"unit": "Unit 8: Inventories", "lectures": [f"Acc Lec {i}" for i in range(51, 56)]},
        {"unit": "Unit 9: Partnership Accounts", "lectures": [f"Acc Lec {i}" for i in range(56, 78)]},
        {"unit": "Unit 10: Non-Profit Organisation (NPO)", "lectures": [f"Acc Lec {i}" for i in range(78, 87)]},
        {"unit": "Unit 11: Company Accounts", "lectures": [f"Acc Lec {i}" for i in range(87, 105)]},
        {"unit": "Unit 12: Theoretical Framework", "lectures": [f"Acc Lec {i}" for i in range(105, 109)]}
    ],
    "Quantitative Aptitude": [
        {"unit": "Basic Mathematics", "lectures": ["QA Lec 1", "QA Lec 2"]},
        {"unit": "Mathematics of Finance", "lectures": [f"QA Lec {i}" for i in range(3, 16)]},
        {"unit": "Ratio, Proportion, Indices, Logarithm", "lectures": [f"QA Lec {i}" for i in range(16, 25)]},
        {"unit": "Measures of Central Tendency & Dispersion", "lectures": [f"QA Lec {i}" for i in range(25, 36)]},
        {"unit": "Number Series, Coding Decoding", "lectures": ["QA Lec 36"]},
        {"unit": "Direction Test & Blood Relation", "lectures": [f"QA Lec {i}" for i in range(37, 41)]},
        {"unit": "Seating Arrangement", "lectures": ["QA Lec 41", "QA Lec 42"]},
        {"unit": "Correlation and Regression", "lectures": [f"QA Lec {i}" for i in range(43, 49)]},
        {"unit": "Index Number", "lectures": [f"QA Lec {i}" for i in range(49, 53)]},
        {"unit": "Equations & Inequalities", "lectures": [f"QA Lec {i}" for i in range(53, 60)]},
        {"unit": "Permutation & Combination", "lectures": [f"QA Lec {i}" for i in range(60, 65)]},
        {"unit": "Sequence & Series", "lectures": [f"QA Lec {i}" for i in range(65, 69)]},
        {"unit": "Sets, Relation and Functions", "lectures": [f"QA Lec {i}" for i in range(69, 74)]},
        {"unit": "Probability & Theoretical Distributions", "lectures": [f"QA Lec {i}" for i in range(74, 82)]},
        {"unit": "Statistical Description & Calculus", "lectures": [f"QA Lec {i}" for i in range(82, 89)]}
    ],
    "Business Economics": [
        {"unit": "Basics & Indian Economy", "lectures": [f"Eco Lec {i}" for i in range(1, 6)]},
        {"unit": "Public Finance", "lectures": [f"Eco Lec {i}" for i in range(6, 16)]},
        {"unit": "Money Market", "lectures": [f"Eco Lec {i}" for i in range(16, 22)]},
        {"unit": "International Trade", "lectures": [f"Eco Lec {i}" for i in range(22, 30)]},
        {"unit": "Nature & Scope of Business Economics", "lectures": [f"Eco Lec {i}" for i in range(30, 35)]},
        {"unit": "Theory of Demand and Supply", "lectures": [f"Eco Lec {i}" for i in range(35, 49)]},
        {"unit": "Theory of Production and Cost", "lectures": [f"Eco Lec {i}" for i in range(49, 59)]},
        {"unit": "Price Determination in Different Markets", "lectures": [f"Eco Lec {i}" for i in range(59, 68)]},
        {"unit": "Determination of National Income", "lectures": [f"Eco Lec {i}" for i in range(68, 82)]},
        {"unit": "Business Cycles", "lectures": [f"Eco Lec {i}" for i in range(82, 86)]}
    ],
    "Business Law": [
        {"unit": "Category 1: Concept Lectures", "lectures": [f"Law Concept Lec {i}" for i in range(1, 29)]},
        {"unit": "Category 2: Written Practice Sessions", "lectures": [f"Law Written Practice Lec {i}" for i in range(1, 15)]}
    ]
}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CA Foundation Jan 2027 Study Planner</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .countdown-card { background: linear-gradient(135deg, #1e1b4b, #312e81); border: 1px solid #4338ca; border-radius: 15px; }
        .timer-unit { background: rgba(255,255,255,0.1); padding: 10px 15px; border-radius: 10px; min-width: 80px; text-align: center; }
        .subject-card { background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; margin-bottom: 20px; }
        .accordion-button { background-color: #334155 !important; color: #f8fafc !important; }
        .accordion-button:not(.collapsed) { background-color: #475569 !important; }
        .accordion-item { background-color: #1e293b; border-color: #334155; }
        .form-check-input:checked { background-color: #10b981; border-color: #10b981; }
        .progress-bar-custom { background: linear-gradient(90deg, #3b82f6, #10b981); }
    </style>
</head>
<body>
    <div class="container py-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h4 class="m-0 text-warning">🎓 CA Foundation Jan 2027 Planner</h4>
            <div>
                <span class="me-3 text-info">👤 {{ user.name }} ({{ user.mobile }})</span>
                <a href="{{ url_for('logout') }}" class="btn btn-outline-danger btn-sm">Logout</a>
            </div>
        </div>

        <div class="countdown-card p-4 text-center mb-4 shadow-lg">
            <h5 class="text-light mb-3">⏳ Target Exam Countdown: Jan 2027 Attempt</h5>
            <div class="d-flex justify-content-center gap-3 flex-wrap" id="timer">
                <div class="timer-unit"><h3 id="months" class="m-0 text-warning">0</h3><small>Months</small></div>
                <div class="timer-unit"><h3 id="days" class="m-0 text-warning">0</h3><small>Days</small></div>
                <div class="timer-unit"><h3 id="hours" class="m-0 text-warning">0</h3><small>Hours</small></div>
                <div class="timer-unit"><h3 id="minutes" class="m-0 text-warning">0</h3><small>Minutes</small></div>
            </div>
        </div>

        <div class="card bg-dark border-secondary p-3 mb-4">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="m-0 text-light">Overall Completion Progress</h6>
                <span class="badge bg-success fs-6" id="overall-percentage">0%</span>
            </div>
            <div class="progress" style="height: 12px;">
                <div class="progress-bar progress-bar-custom" id="overall-bar" style="width: 0%;"></div>
            </div>
        </div>

        {% for subject, units in syllabus.items() %}
        <div class="subject-card p-3">
            <h5 class="text-info mb-3">📚 {{ subject }}</h5>
            <div class="accordion" id="accordion-{{ loop.index }}">
                {% for unit_data in units %}
                {% set unit_id = loop.index %}
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-{{ loop.parent.index }}-{{ unit_id }}">
                            {{ unit_data.unit }}
                        </button>
                    </h2>
                    <div id="collapse-{{ loop.parent.index }}-{{ unit_id }}" class="accordion-collapse collapse">
                        <div class="accordion-body">
                            <div class="row">
                                {% for lec in unit_data.lectures %}
                                {% set lec_key = subject ~ '_' ~ unit_data.unit ~ '_' ~ lec %}
                                <div class="col-md-4 col-sm-6 mb-2">
                                    <div class="form-check">
                                        <input class="form-check-input lec-checkbox" type="checkbox" data-key="{{ lec_key }}" id="chk-{{ loop.parent.parent.index }}-{{ loop.parent.index }}-{{ loop.index }}" {% if user_progress.get(lec_key) == 1 %}checked{% endif %}>
                                        <label class="form-check-label text-light" for="chk-{{ loop.parent.parent.index }}-{{ loop.parent.index }}-{{ loop.index }}">
                                            {{ lec }}
                                        </label>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function updateCountdown() {
            const examDate = new Date("January 1, 2027 00:00:00").getTime();
            const now = new Date().getTime();
            const diff = examDate - now;

            if (diff > 0) {
                const months = Math.floor(diff / (1000 * 60 * 60 * 24 * 30.4375));
                const days = Math.floor((diff % (1000 * 60 * 60 * 24 * 30.4375)) / (1000 * 60 * 60 * 24));
                const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

                document.getElementById("months").innerText = months;
                document.getElementById("days").innerText = days;
                document.getElementById("hours").innerText = hours;
                document.getElementById("minutes").innerText = minutes;
            }
        }
        setInterval(updateCountdown, 1000);
        updateCountdown();

        function calculateProgress() {
            const total = document.querySelectorAll('.lec-checkbox').length;
            const checked = document.querySelectorAll('.lec-checkbox:checked').length;
            const percentage = total > 0 ? Math.round((checked / total) * 100) : 0;
            document.getElementById('overall-percentage').innerText = percentage + '%';
            document.getElementById('overall-bar').style.width = percentage + '%';
        }
        calculateProgress();

        document.querySelectorAll('.lec-checkbox').forEach(chk => {
            chk.addEventListener('change', function() {
                const key = this.getAttribute('data-key');
                const status = this.checked ? 1 : 0;
                calculateProgress();

                fetch('/update_progress', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({item_id: key, status: status})
                });
            });
        });
    </script>
</body>
</html>
'''

# ULTRA HIGH CONTRAST LOGIN FORM
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - CA Foundation Planner</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: #090d16; 
            color: #ffffff; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            min-height: 100vh; 
            padding: 20px 0; 
            font-family: 'Segoe UI', Roboto, sans-serif;
        }
        .login-card { 
            background-color: #1e293b; 
            border: 2px solid #3b82f6; 
            border-radius: 16px; 
            width: 100%; 
            max-width: 420px; 
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
        }
        .form-label {
            color: #f1f5f9 !important;
            font-weight: 600;
            font-size: 0.95rem;
            margin-bottom: 6px;
        }
        .custom-input {
            background-color: #0f172a !important;
            color: #ffffff !important;
            border: 1px solid #475569 !important;
            border-radius: 8px;
            padding: 12px;
            font-size: 1rem;
        }
        .custom-input:focus {
            border-color: #38bdf8 !important;
            box-shadow: 0 0 8px rgba(56, 189, 248, 0.4) !important;
            background-color: #0f172a !important;
            color: #ffffff !important;
        }
        .custom-input::placeholder {
            color: #94a3b8 !important;
            opacity: 1;
        }
        .btn-custom {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            border: none;
            color: #000000;
            font-weight: 700;
            padding: 12px;
            border-radius: 8px;
            font-size: 1.05rem;
            transition: all 0.2s ease;
        }
        .btn-custom:hover {
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            color: #000000;
        }
    </style>
</head>
<body>
    <div class="login-card p-4 shadow-lg">
        <h3 class="text-center text-warning mb-1 font-weight-bold">🎓 Student Portal</h3>
        <p class="text-center text-light mb-4" style="font-size: 0.85rem;">CA Foundation Jan 2027 Planner</p>

        {% if error %}
            <div class="alert alert-danger p-2 text-center font-weight-bold" style="font-size: 0.9rem;">{{ error }}</div>
        {% endif %}

        <form method="POST">
            <div class="mb-3">
                <label class="form-label">📱 Mobile Number</label>
                <input type="text" name="mobile" class="form-control custom-input" placeholder="Enter 10-digit mobile number" required autocomplete="off">
            </div>

            <div class="mb-3">
                <label class="form-label">👤 Full Name <span class="text-warning" style="font-size: 0.75rem;">(New Student)</span></label>
                <input type="text" name="name" class="form-control custom-input" placeholder="Enter your full name" autocomplete="off">
            </div>

            <div class="mb-3">
                <label class="form-label">🎂 Date of Birth</label>
                <input type="text" name="dob" class="form-control custom-input" placeholder="DD/MM/YYYY (e.g. 15/08/2005)" autocomplete="off">
            </div>

            <div class="mb-4">
                <label class="form-label">🔑 4-Digit Security PIN</label>
                <input type="password" name="pin" class="form-control custom-input" placeholder="Set or Enter 4-Digit PIN" required maxlength="4">
            </div>

            <button type="submit" class="btn btn-custom w-100 shadow">Login / Register Now 🚀</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user_id' in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        
        cursor.execute("SELECT item_id, status FROM user_progress WHERE user_id = ?", (session['user_id'],))
        progress_data = {row['item_id']: row['status'] for row in cursor.fetchall()}
        conn.close()
        return render_template_string(HTML_TEMPLATE, user=user, syllabus=SYLLABUS, user_progress=progress_data)

    if request.method == 'POST':
        mobile = request.form.get('mobile').strip()
        name = request.form.get('name', '').strip()
        dob = request.form.get('dob', '').strip()
        pin = request.form.get('pin').strip()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE mobile = ?", (mobile,))
        user = cursor.fetchone()

        if user:
            if user['pin'] == pin:
                session.permanent = True
                session['user_id'] = user['id']
                conn.close()
                return redirect(url_for('home'))
            else:
                conn.close()
                return render_template_string(LOGIN_TEMPLATE, error="Invalid PIN! Please check and try again.")
        else:
            if not name:
                conn.close()
                return render_template_string(LOGIN_TEMPLATE, error="Please enter your Name to register new account!")
            cursor.execute("INSERT INTO users (mobile, name, dob, pin) VALUES (?, ?, ?, ?)", (mobile, name, dob, pin))
            conn.commit()
            user_id = cursor.lastrowid
            session.permanent = True
            session['user_id'] = user_id
            conn.close()
            return redirect(url_for('home'))

    return render_template_string(LOGIN_TEMPLATE)

@app.route('/update_progress', methods=['POST'])
def update_progress():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    item_id = data.get('item_id')
    status = data.get('status')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_progress (user_id, item_id, status)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, item_id) DO UPDATE SET status=excluded.status
    ''', (session['user_id'], item_id, status))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
