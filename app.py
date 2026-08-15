import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'ca_foundation_jan2027_ultra_master_key_production'
app.permanent_session_lifetime = timedelta(days=90)

# Configuration for Profile Picture Uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
            pin TEXT NOT NULL,
            profile_pic TEXT DEFAULT '',
            manifestation_completed INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute("PRAGMA table_info(users)")
    cols = [c[1] for c in cursor.fetchall()]
    if 'dob' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN dob TEXT")
    if 'profile_pic' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT DEFAULT ''")
    if 'manifestation_completed' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN manifestation_completed INTEGER DEFAULT 0")

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
# 1. ICAI OFFICIAL SYLLABUS DATA (HOMEPAGE - UNIT WISE BREAKDOWN)
# ==========================================================
ICAI_SYLLABUS = {
    "Paper 1: Accounting (Official ICAI)": [
        {"unit": "Chapter 1: Theoretical Framework", "sub_units": [
            "Unit 1: Meaning and Scope of Accounting",
            "Unit 2: Accounting Concepts, Principles and Conventions",
            "Unit 3: Capital and Revenue Expenditures and Receipts",
            "Unit 4: Contingent Assets and Contingent Liabilities",
            "Unit 5: Accounting Policies",
            "Unit 6: Accounting as Measurement Discipline – Valuation Principles, Accounting Estimates",
            "Unit 7: Accounting Standards"
        ]},
        {"unit": "Chapter 2: Accounting Process", "sub_units": [
            "Unit 1: Basic Accounting Procedures – Journal entries",
            "Unit 2: Ledgers",
            "Unit 3: Trial Balance",
            "Unit 4: Subsidiary Books",
            "Unit 5: Cash Book",
            "Unit 6: Rectification of Errors"
        ]},
        {"unit": "Chapter 3: Bank Reconciliation Statement", "sub_units": ["Bank Reconciliation Statement Complete"]},
        {"unit": "Chapter 4: Inventories", "sub_units": ["Inventories Valuation Complete"]},
        {"unit": "Chapter 5: Depreciation and Amortisation", "sub_units": ["Depreciation & Amortisation Complete"]},
        {"unit": "Chapter 6: Bills of Exchange and Promissory Notes", "sub_units": ["Bills of Exchange Complete"]},
        {"unit": "Chapter 7: Preparation of Final Accounts of Sole Proprietors", "sub_units": [
            "Unit 1: Final Accounts of Non-Manufacturing Entities",
            "Unit 2: Final Accounts of Manufacturing Entities"
        ]},
        {"unit": "Chapter 8: Financial Statements of Not-for-Profit Organisations", "sub_units": ["NPO Financial Statements Complete"]},
        {"unit": "Chapter 9: Accounts from Incomplete Records", "sub_units": ["Single Entry System Complete"]},
        {"unit": "Chapter 10: Partnership and LLP Accounts", "sub_units": [
            "Unit 1: Introduction to Partnership Accounts",
            "Unit 2: Treatment of Goodwill in Partnership Accounts",
            "Unit 3: Admission of a New Partner",
            "Unit 4: Retirement of a Partner",
            "Unit 5: Death of a Partner",
            "Unit 6: Dissolution of Partnership Firms and LLPs"
        ]},
        {"unit": "Chapter 11: Company Accounts", "sub_units": [
            "Unit 1: Introduction to Company Accounts",
            "Unit 2: Issue, Forfeiture and Re-Issue of Shares",
            "Unit 3: Issue of Debentures",
            "Unit 4: Accounting for Bonus Issue and Right Issue",
            "Unit 5: Redemption of Preference Shares",
            "Unit 6: Redemption of Debentures"
        ]}
    ],
    "Paper 2: Business Laws (Official ICAI)": [
        {"unit": "Chapter 1: Indian Regulatory Framework", "sub_units": ["Regulatory Framework Overview"]},
        {"unit": "Chapter 2: The Indian Contract Act, 1872", "sub_units": [
            "Unit 1: Nature of Contracts",
            "Unit 2: Consideration",
            "Unit 3: Other Essential Elements of a Contract",
            "Unit 4: Performance of Contract",
            "Unit 5: Breach of Contract and its Remedies",
            "Unit 6: Contingent and Quasi Contracts",
            "Unit 7: Contract of Indemnity and Guarantee",
            "Unit 8: Bailment and Pledge",
            "Unit 9: Agency"
        ]},
        {"unit": "Chapter 3: The Sale of Goods Act, 1930", "sub_units": [
            "Unit 1: Formation of the Contract of Sale",
            "Unit 2: Conditions & Warranties",
            "Unit 3: Transfer of Ownership and Delivery of Goods",
            "Unit 4: Unpaid Seller"
        ]},
        {"unit": "Chapter 4: The Indian Partnership Act, 1932", "sub_units": [
            "Unit 1: General Nature of Partnership",
            "Unit 2: Relations of Partners",
            "Unit 3: Registration and Dissolution of a Firm"
        ]},
        {"unit": "Chapter 5: The Limited Liability Partnership Act, 2008", "sub_units": ["LLP Act Overview & Provisions"]},
        {"unit": "Chapter 6: The Companies Act, 2013", "sub_units": ["Company Law Foundations & Incorporation"]},
        {"unit": "Chapter 7: The Negotiable Instruments Act, 1881", "sub_units": ["Promissory Notes, Bills & Cheques"]}
    ],
    "Paper 3: Quantitative Aptitude (Official ICAI)": [
        {"unit": "PART-A: BUSINESS MATHEMATICS", "sub_units": [
            "Chapter 1: Ratio and Proportion, Indices, Logarithms",
            "Chapter 2: Equations",
            "Chapter 3: Linear Inequalities",
            "Chapter 4: Mathematics of Finance",
            "Chapter 5: Basic Concepts of Permutations and Combinations",
            "Chapter 6: Sequence and Series – AP & GP",
            "Chapter 7: Sets, Relations and Functions, Limits & Continuity",
            "Chapter 8: Applications of Differential and Integral Calculus"
        ]},
        {"unit": "PART-B: LOGICAL REASONING", "sub_units": [
            "Chapter 9: Number Series, Coding and Decoding and Odd Man Out",
            "Chapter 10: Direction Sense Test",
            "Chapter 11: Seating Arrangements",
            "Chapter 12: Blood Relations"
        ]},
        {"unit": "PART-C: STATISTICS", "sub_units": [
            "Chapter 13 - Unit I: Statistical Description of Data",
            "Chapter 13 - Unit II: Sampling",
            "Chapter 14 - Unit I: Measures of Central Tendency",
            "Chapter 14 - Unit II: Dispersion",
            "Chapter 15: Probability",
            "Chapter 16: Theoretical Distributions",
            "Chapter 17: Correlation and Regression",
            "Chapter 18: Index Numbers"
        ]}
    ],
    "Paper 4: Business Economics (Official ICAI)": [
        {"unit": "Chapter 1: Nature & Scope of Business Economics", "sub_units": [
            "Unit 1: Introduction",
            "Unit 2: Basic Problems of an Economy & Role of Price Mechanism"
        ]},
        {"unit": "Chapter 2: Theory of Demand and Supply", "sub_units": [
            "Unit 1: Law of Demand and Elasticity of Demand",
            "Unit 2: Theory of Consumer Behaviour",
            "Unit 3: Supply"
        ]},
        {"unit": "Chapter 3: Theory of Production and Cost", "sub_units": [
            "Unit 1: Theory of Production",
            "Unit 2: Theory of Cost"
        ]},
        {"unit": "Chapter 4: Price Determination in Different Markets", "sub_units": [
            "Unit 1: Meaning and Types of Markets",
            "Unit 2: Determination of Prices",
            "Unit 3: Price Output Determination under Different Market Forms"
        ]},
        {"unit": "Chapter 5: Business Cycles", "sub_units": ["Business Cycles Phases & Theories"]},
        {"unit": "Chapter 6: Determination of National Income", "sub_units": [
            "Unit 1: National Income Accounting",
            "Unit 2: The Keynesian Theory of Determination of National Income"
        ]},
        {"unit": "Chapter 7: Public Finance", "sub_units": [
            "Unit 1: Fiscal Functions: An Overview Centre and State Finance",
            "Unit 2: Market Failure/ Government intervention to correct Market Failure",
            "Unit 3: Budget Making, Revenue & Public Debt",
            "Unit 4: Fiscal Policy"
        ]},
        {"unit": "Chapter 8: Money Market", "sub_units": [
            "Unit 1: Concept of Money Demand",
            "Unit 2: Concept of Money Supply",
            "Unit 3: Monetary Policy"
        ]},
        {"unit": "Chapter 9: International Trade", "sub_units": [
            "Unit 1: Theories of International Trade",
            "Unit 2: Instruments of Trade Policy",
            "Unit 3: Trade Negotiations",
            "Unit 4: Exchange Rate and Its Economic Effects",
            "Unit 5: International Capital Movements"
        ]},
        {"unit": "Chapter 10: Indian Economy", "sub_units": ["Overview of Indian Economy"]}
    ]
}

# ==========================================================
# 2. PERSONAL LECTURE PLANNER DATA (SIDEBAR)
# ==========================================================
PERSONAL_SYLLABUS = {
    "Accounting (Lecture Planner)": [
        {"unit": "Unit 1: Accounts Basics (2 Lecs)", "lectures": ["Basics Lec 1", "Basics Lec 2"]},
        {"unit": "Unit 2: Accounting Process (10 Lecs)", "lectures": [f"Journal/Ledger/Trial/Subsidiary/CashBook Lec {i}" for i in range(1, 11)]},
        {"unit": "Unit 3: Depreciation & Amortisation (7 Lecs)", "lectures": [f"Depreciation Lec {i}" for i in range(1, 8)]},
        {"unit": "Unit 4: Bills of Exchange (6 Lecs)", "lectures": [f"Bills of Exchange Lec {i}" for i in range(1, 7)]},
        {"unit": "Unit 5: BRS (5 Lecs)", "lectures": [f"BRS Lec {i}" for i in range(1, 6)]},
        {"unit": "Unit 6: Final Accounts of Sole Proprietor (9 Lecs)", "lectures": [f"Final A/cs Lec {i}" for i in range(1, 10)]},
        {"unit": "Unit 7: Rectification of Errors (5 Lecs)", "lectures": [f"Rectification Lec {i}" for i in range(1, 6)]},
        {"unit": "Unit 8: Accounts from Incomplete Records (8 Lecs)", "lectures": [f"Incomplete Records Lec {i}" for i in range(1, 9)]},
        {"unit": "Unit 9: Inventories (5 Lecs)", "lectures": [f"Inventories Lec {i}" for i in range(1, 6)]},
        {"unit": "Unit 10: Partnership Accounts (22 Lecs)", "lectures": [f"Partnership Lec {i}" for i in range(1, 23)]},
        {"unit": "Unit 11: Non-Profit Organisation (9 Lecs)", "lectures": [f"NPO Lec {i}" for i in range(1, 10)]},
        {"unit": "Unit 12: Company Accounts (19 Lecs)", "lectures": [f"Company A/cs Lec {i}" for i in range(1, 20)]},
        {"unit": "Unit 13: Theoretical Framework (4 Lecs)", "lectures": [f"Theory Lec {i}" for i in range(1, 5)]}
    ],
    "Quantitative Aptitude (Lecture Planner)": [
        {"unit": "Unit 1: Basic Mathematics (2 Lecs)", "lectures": ["Basic Math Lec 1", "Basic Math Lec 2"]},
        {"unit": "Unit 2: Mathematics of Finance (13 Lecs)", "lectures": [f"Math of Finance Lec {i}" for i in range(1, 14)]},
        {"unit": "Unit 3: Ratio, Proportion, Indices, Logarithm (9 Lecs)", "lectures": [f"Ratio & Log Lec {i}" for i in range(1, 10)]},
        {"unit": "Unit 4: Central Tendency & Dispersion (11 Lecs)", "lectures": [f"Dispersion Lec {i}" for i in range(1, 12)]},
        {"unit": "Unit 5: Number Series & Coding (1 Lec)", "lectures": ["Coding Decoding Lec 1"]},
        {"unit": "Unit 6: Direction Test (2 Lecs)", "lectures": ["Direction Test Lec 1", "Direction Test Lec 2"]},
        {"unit": "Unit 7: Blood Relation (2 Lecs)", "lectures": ["Blood Relation Lec 1", "Blood Relation Lec 2"]},
        {"unit": "Unit 8: Seating Arrangement (2 Lecs)", "lectures": ["Seating Arrangement Lec 1", "Seating Arrangement Lec 2"]},
        {"unit": "Unit 9: Correlation and Regression (6 Lecs)", "lectures": [f"Correlation Lec {i}" for i in range(1, 7)]},
        {"unit": "Unit 10: Index Number (4 Lecs)", "lectures": [f"Index Number Lec {i}" for i in range(1, 5)]},
        {"unit": "Unit 11: Equations (5 Lecs)", "lectures": [f"Equations Lec {i}" for i in range(1, 6)]},
        {"unit": "Unit 12: Inequalities (2 Lecs)", "lectures": ["Inequalities Lec 1", "Inequalities Lec 2"]},
        {"unit": "Unit 13: Permutation & Combination (5 Lecs)", "lectures": [f"P&C Lec {i}" for i in range(1, 6)]},
        {"unit": "Unit 14: Sequence and Series (4 Lecs)", "lectures": [f"Sequence Lec {i}" for i in range(1, 5)]},
        {"unit": "Unit 15: Sets, Relation and Functions (5 Lecs)", "lectures": [f"Sets & Functions Lec {i}" for i in range(1, 6)]},
        {"unit": "Unit 16: Probability (4 Lecs)", "lectures": [f"Probability Lec {i}" for i in range(1, 5)]},
        {"unit": "Unit 17: Theoretical Distributions (3 Lecs)", "lectures": [f"Theoretical Dist Lec {i}" for i in range(1, 4)]},
        {"unit": "Unit 18: Statistical Description of Data (3 Lecs)", "lectures": [f"Stats Data Lec {i}" for i in range(1, 4)]},
        {"unit": "Unit 19: Sampling (3 Lecs)", "lectures": [f"Sampling Lec {i}" for i in range(1, 4)]},
        {"unit": "Unit 20: Differential & Integral Calculus (4 Lecs)", "lectures": [f"Calculus Lec {i}" for i in range(1, 5)]}
    ],
    "Business Economics (Lecture Planner)": [
        {"unit": "Unit 1: Basics (2 Lecs)", "lectures": ["Basics Lec 1", "Basics Lec 2"]},
        {"unit": "Unit 2: Indian Economy (5 Lecs)", "lectures": [f"Indian Economy Lec {i}" for i in range(1, 6)]},
        {"unit": "Unit 3: Public Finance (10 Lecs)", "lectures": [f"Public Finance Lec {i}" for i in range(1, 11)]},
        {"unit": "Unit 4: Money Market (6 Lecs)", "lectures": [f"Money Market Lec {i}" for i in range(1, 7)]},
        {"unit": "Unit 5: International Trade (8 Lecs)", "lectures": [f"International Trade Lec {i}" for i in range(1, 9)]},
        {"unit": "Unit 6: Nature & Scope of Economics (5 Lecs)", "lectures": [f"Nature & Scope Lec {i}" for i in range(1, 6)]},
        {"unit": "Unit 7: Demand and Supply (14 Lecs)", "lectures": [f"Demand & Supply Lec {i}" for i in range(1, 15)]},
        {"unit": "Unit 8: Production and Cost (10 Lecs)", "lectures": [f"Production & Cost Lec {i}" for i in range(1, 11)]},
        {"unit": "Unit 9: Price Determination in Markets (9 Lecs)", "lectures": [f"Markets Lec {i}" for i in range(1, 10)]},
        {"unit": "Unit 10: National Income (14 Lecs)", "lectures": [f"National Income Lec {i}" for i in range(1, 15)]},
        {"unit": "Unit 11: Business Cycles (4 Lecs)", "lectures": [f"Business Cycles Lec {i}" for i in range(1, 5)]}
    ],
    "Business Law (FastTrack & Writing Practice)": [
        {"unit": "FastTrack Concept Lectures (48 Lessons)", "lectures": [f"Law Concept FastTrack Lec {i}" for i in range(1, 49)]},
        {"unit": "Answer Writing Practice Sessions (24 Sessions)", "lectures": [f"Law Answer Writing Session {i}" for i in range(1, 25)]}
    ]
}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CA Foundation Master Target Tracker</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #0b0f19; color: #f8fafc; font-family: 'Segoe UI', Tahoma, sans-serif; }
        
        /* Digital Plate Countdown Clock Styling */
        .digital-clock-container { display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; }
        .clock-plate {
            background: linear-gradient(180deg, #1e293b 50%, #0f172a 50%);
            border: 2px solid #38bdf8;
            border-radius: 10px;
            padding: 10px 15px;
            min-width: 80px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(56, 189, 248, 0.25);
        }
        .clock-digit { font-size: 2rem; font-weight: 800; color: #fbbf24; font-family: 'Courier New', monospace; margin: 0; }
        .clock-label { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }

        /* UI Cards & Elements */
        .subject-card { background-color: #1e293b; border: 1px solid #334155; border-radius: 14px; margin-bottom: 24px; overflow: hidden; }
        .accordion-button { background-color: #334155 !important; color: #f8fafc !important; font-weight: 600; }
        .accordion-button:not(.collapsed) { background-color: #475569 !important; color: #38bdf8 !important; }
        .accordion-item { background-color: #1e293b; border-color: #334155; }
        .form-check-input:checked { background-color: #10b981; border-color: #10b981; }
        .progress-bar-custom { background: linear-gradient(90deg, #3b82f6, #10b981); }

        /* Offcanvas Sidebar */
        .offcanvas-dark { background-color: #0f172a; color: #f8fafc; border-left: 2px solid #3b82f6; }

        /* Manifestation & Golden Theme */
        .gold-input { color: #fbbf24 !important; font-weight: bold; background: #0f172a !important; border: 1px solid #f59e0b !important; }
        .manifestation-card { background: linear-gradient(135deg, #1e1b4b, #312e81); border: 2px solid #fbbf24; border-radius: 16px; }
        
        .profile-img-container { width: 55px; height: 55px; border-radius: 50%; overflow: hidden; border: 2px solid #fbbf24; background: #3b82f6; display: flex; align-items: center; justify-content: center; }
        .profile-img-container img { width: 100%; height: 100%; object-fit: cover; }
    </style>
</head>
<body>
    <div class="container py-4">
        <!-- TOP HEADER: PROFILE (LEFT) & SIDEBAR BUTTON (RIGHT) -->
        <div class="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom border-secondary">
            <!-- Left Corner: Profile Section -->
            <div class="d-flex align-items-center gap-3">
                <div class="profile-img-container shadow">
                    {% if user_pic %}
                        <img src="{{ url_for('static', filename='uploads/' ~ user_pic) }}" alt="Profile">
                    {% else %}
                        <span class="fs-3 fw-bold text-white">{{ user_name[0] if user_name else 'S' }}</span>
                    {% endif %}
                </div>
                <div>
                    <h5 class="m-0 text-warning fw-bold">🎓 Future CA {{ user_name }}</h5>
                    <small class="text-info">📱 {{ user_mobile }} | 🎂 DOB: {{ user_dob if user_dob else 'N/A' }}</small>
                    <div class="mt-1">
                        <label for="picUpload" class="badge bg-secondary text-light cursor-pointer" style="cursor:pointer;"><i class="fa-solid fa-camera"></i> Change Photo</label>
                        <form id="picForm" action="/upload_profile_pic" method="POST" enctype="multipart/form-data" class="d-none">
                            <input type="file" id="picUpload" name="profile_pic" accept="image/*" onchange="document.getElementById('picForm').submit();">
                        </form>
                    </div>
                </div>
            </div>

            <!-- Right Corner: Personal Planner Toggle & Logout -->
            <div class="d-flex align-items-center gap-2">
                <button class="btn btn-warning fw-bold shadow" type="button" data-bs-toggle="offcanvas" data-bs-target="#personalSidebar">
                    📚 Personal Planner Sidebar <i class="fa-solid fa-arrow-right"></i>
                </button>
                <a href="{{ url_for('logout') }}" class="btn btn-outline-danger btn-sm"><i class="fa-solid fa-right-from-bracket"></i> Logout</a>
            </div>
        </div>

        <!-- DYNAMIC DIGITAL PLATE COUNTDOWN CLOCK -->
        <div class="bg-dark p-4 text-center mb-4 rounded-3 border border-secondary shadow-lg">
            <h5 class="text-light mb-3"><i class="fa-regular fa-clock text-warning"></i> TARGET EXAM COUNTDOWN: JAN 2027 ATTEMPT</h5>
            <div class="digital-clock-container">
                <div class="clock-plate"><div class="clock-digit" id="months">00</div><div class="clock-label">Months</div></div>
                <div class="clock-plate"><div class="clock-digit" id="days">00</div><div class="clock-label">Days</div></div>
                <div class="clock-plate"><div class="clock-digit" id="hours">00</div><div class="clock-label">Hours</div></div>
                <div class="clock-plate"><div class="clock-digit" id="minutes">00</div><div class="clock-label">Minutes</div></div>
                <div class="clock-plate"><div class="clock-digit" id="seconds">00</div><div class="clock-label">Seconds</div></div>
            </div>
        </div>

        <!-- DYNAMIC PROGRESS BAR -->
        <div class="card bg-dark border-secondary p-3 mb-4 shadow">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="m-0 text-light"><i class="fa-solid fa-chart-line text-info"></i> ICAI Official Syllabus Progress</h6>
                <span class="badge bg-success fs-6" id="overall-percentage">0%</span>
            </div>
            <div class="progress" style="height: 16px;">
                <div class="progress-bar progress-bar-custom" id="overall-bar" style="width: 0%;"></div>
            </div>
        </div>

        <!-- MAIN HOMEPAGE: OFFICIAL ICAI SYLLABUS -->
        <h4 class="text-warning mb-3"><i class="fa-solid fa-book"></i> Official ICAI Syllabus Tracker</h4>
        {% for subject, chapters in icai_syllabus.items() %}
        {% set subject_idx = loop.index %}
        <div class="subject-card p-3">
            <h5 class="text-info mb-3"><i class="fa-solid fa-bookmark"></i> {{ subject }}</h5>
            <div class="accordion" id="icai-accordion-{{ subject_idx }}">
                {% for ch_data in chapters %}
                {% set ch_idx = loop.index %}
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#icai-collapse-{{ subject_idx }}-{{ ch_idx }}">
                            {{ ch_data.unit }}
                        </button>
                    </h2>
                    <div id="icai-collapse-{{ subject_idx }}-{{ ch_idx }}" class="accordion-collapse collapse">
                        <div class="accordion-body">
                            {% for sub in ch_data.sub_units %}
                            {% set key = subject ~ '_' ~ ch_data.unit ~ '_' ~ sub %}
                            <div class="form-check mb-2">
                                <input class="form-check-input lec-checkbox" type="checkbox" data-key="{{ key }}" id="icai-chk-{{ subject_idx }}-{{ ch_idx }}-{{ loop.index }}" {% if user_progress.get(key) == 1 %}checked{% endif %}>
                                <label class="form-check-label text-light" for="icai-chk-{{ subject_idx }}-{{ ch_idx }}-{{ loop.index }}">
                                    {{ sub }}
                                </label>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </div>

    <!-- SIDEBAR: PERSONAL LECTURE PLANNER -->
    <div class="offcanvas offcanvas-end offcanvas-dark" style="width: 88%; max-width: 650px;" tabindex="-1" id="personalSidebar">
        <div class="offcanvas-header border-bottom border-secondary">
            <h5 class="offcanvas-title text-warning"><i class="fa-solid fa-bullseye"></i> Personal Lecture Planner</h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas"></button>
        </div>
        <div class="offcanvas-body">
            <!-- Sidebar Countdown Header -->
            <div class="bg-dark p-3 text-center mb-3 rounded border border-info">
                <small class="text-info d-block mb-1">🎯 Personal Goal Tracker Clock</small>
                <div class="digital-clock-container" style="gap:6px;">
                    <div class="clock-plate" style="min-width:55px; padding:4px;"><div class="clock-digit fs-5" id="sb-months">00</div><div class="clock-label" style="font-size:0.6rem;">Mon</div></div>
                    <div class="clock-plate" style="min-width:55px; padding:4px;"><div class="clock-digit fs-5" id="sb-days">00</div><div class="clock-label" style="font-size:0.6rem;">Days</div></div>
                    <div class="clock-plate" style="min-width:55px; padding:4px;"><div class="clock-digit fs-5" id="sb-hours">00</div><div class="clock-label" style="font-size:0.6rem;">Hrs</div></div>
                    <div class="clock-plate" style="min-width:55px; padding:4px;"><div class="clock-digit fs-5" id="sb-minutes">00</div><div class="clock-label" style="font-size:0.6rem;">Min</div></div>
                    <div class="clock-plate" style="min-width:55px; padding:4px;"><div class="clock-digit fs-5" id="sb-seconds">00</div><div class="clock-label" style="font-size:0.6rem;">Sec</div></div>
                </div>
            </div>

            <div class="mb-3">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <small class="text-light">Lecture Progress</small>
                    <small class="text-success fw-bold" id="sb-percentage">0%</small>
                </div>
                <div class="progress" style="height: 10px;">
                    <div class="progress-bar progress-bar-custom" id="sb-bar" style="width: 0%;"></div>
                </div>
            </div>

            {% for subject, units in personal_syllabus.items() %}
            {% set s_idx = loop.index %}
            <div class="subject-card p-3 mb-3">
                <h6 class="text-warning mb-3"><i class="fa-solid fa-circle-play"></i> {{ subject }}</h6>
                <div class="accordion" id="personal-accordion-{{ s_idx }}">
                    {% for unit_data in units %}
                    {% set u_idx = loop.index %}
                    <div class="accordion-item">
                        <h2 class="accordion-header">
                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#p-collapse-{{ s_idx }}-{{ u_idx }}">
                                {{ unit_data.unit }}
                            </button>
                        </h2>
                        <div id="p-collapse-{{ s_idx }}-{{ u_idx }}" class="accordion-collapse collapse">
                            <div class="accordion-body">
                                <div class="row">
                                    {% for lec in unit_data.lectures %}
                                    {% set lec_key = subject ~ '_' ~ unit_data.unit ~ '_' ~ lec %}
                                    <div class="col-12 mb-2">
                                        <div class="form-check">
                                            <input class="form-check-input sb-checkbox" type="checkbox" data-key="{{ lec_key }}" id="p-chk-{{ s_idx }}-{{ u_idx }}-{{ loop.index }}" {% if user_progress.get(lec_key) == 1 %}checked{% endif %}>
                                            <label class="form-check-label text-light" for="p-chk-{{ s_idx }}-{{ u_idx }}-{{ loop.index }}">
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
    </div>

    <!-- FIRST TIME MANIFESTATION POPUP MODAL -->
    {% if not manifestation_done %}
    <div class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.88);">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content manifestation-card text-light p-4 shadow-lg">
                <h3 class="text-center text-warning fw-bold">🌟 Future CA {{ user_name }}</h3>
                <h5 class="text-center text-info mb-4">"My Manifestation"</h5>
                
                <form action="/save_manifestation" method="POST">
                    <div class="mb-3">
                        <label class="form-label text-light">I will clear CA Foundation in</label>
                        <select name="foundation_attempt" class="form-select gold-input" required>
                            <option value="Jan 2027">Jan 2027 Attempt</option>
                            <option value="May/June 2027">May/June 2027 Attempt</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label text-light">I will appear for CA Intermediate in</label>
                        <select name="inter_attempt" class="form-select gold-input" required>
                            <option value="Jan 2028">Jan 2028 Attempt</option>
                            <option value="May 2028">May 2028 Attempt</option>
                        </select>
                    </div>
                    <div class="mb-4">
                        <label class="form-label text-light">I will appear for CA Final in</label>
                        <select name="final_attempt" class="form-select gold-input" required>
                            <option value="Nov 2030">Nov 2030 Attempt</option>
                            <option value="May 2031">May 2031 Attempt</option>
                        </select>
                    </div>

                    <p class="text-center text-warning fst-italic" style="font-size: 0.9rem;">
                        "Hard work beats talent when talent doesn't work hard. Your future self is counting on you!" 🔥
                    </p>
                    
                    <button type="submit" class="btn btn-warning w-100 fw-bold py-2 mt-2 shadow">Lock My Goals 🚀</button>
                </form>
            </div>
        </div>
    </div>
    {% endif %}

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Precision Dynamic Digital Plate Clock
        function updateDigitalClock() {
            const examDate = new Date("January 1, 2027 00:00:00").getTime();
            const now = new Date().getTime();
            const diff = examDate - now;

            if (diff > 0) {
                const months = Math.floor(diff / (1000 * 60 * 60 * 24 * 30.4375));
                const days = Math.floor((diff % (1000 * 60 * 60 * 24 * 30.4375)) / (1000 * 60 * 60 * 24));
                const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((diff % (1000 * 60)) / 1000);

                const mStr = months.toString().padStart(2, '0');
                const dStr = days.toString().padStart(2, '0');
                const hStr = hours.toString().padStart(2, '0');
                const minStr = minutes.toString().padStart(2, '0');
                const sStr = seconds.toString().padStart(2, '0');

                document.getElementById("months").innerText = mStr;
                document.getElementById("days").innerText = dStr;
                document.getElementById("hours").innerText = hStr;
                document.getElementById("minutes").innerText = minStr;
                document.getElementById("seconds").innerText = sStr;

                if(document.getElementById("sb-months")){
                    document.getElementById("sb-months").innerText = mStr;
                    document.getElementById("sb-days").innerText = dStr;
                    document.getElementById("sb-hours").innerText = hStr;
                    document.getElementById("sb-minutes").innerText = minStr;
                    document.getElementById("sb-seconds").innerText = sStr;
                }
            }
        }
        setInterval(updateDigitalClock, 1000);
        updateDigitalClock();

        // Checkbox & Progress Calculation (Homepage & Sidebar)
        function calculateOverallProgress() {
            const total = document.querySelectorAll('.lec-checkbox').length;
            const checked = document.querySelectorAll('.lec-checkbox:checked').length;
            const percentage = total > 0 ? Math.round((checked / total) * 100) : 0;
            document.getElementById('overall-percentage').innerText = percentage + '%';
            document.getElementById('overall-bar').style.width = percentage + '%';
        }

        function calculateSidebarProgress() {
            const total = document.querySelectorAll('.sb-checkbox').length;
            const checked = document.querySelectorAll('.sb-checkbox:checked').length;
            const percentage = total > 0 ? Math.round((checked / total) * 100) : 0;
            if(document.getElementById('sb-percentage')){
                document.getElementById('sb-percentage').innerText = percentage + '%';
                document.getElementById('sb-bar').style.width = percentage + '%';
            }
        }

        calculateOverallProgress();
        calculateSidebarProgress();

        document.querySelectorAll('.lec-checkbox, .sb-checkbox').forEach(chk => {
            chk.addEventListener('change', function() {
                const key = this.getAttribute('data-key');
                const status = this.checked ? 1 : 0;
                
                calculateOverallProgress();
                calculateSidebarProgress();

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

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Student Portal</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #090d16; color: #ffffff; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px 0; font-family: 'Segoe UI', Roboto, sans-serif; }
        .login-card { background-color: #1e293b; border: 2px solid #3b82f6; border-radius: 16px; width: 100%; max-width: 420px; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5); }
        .form-label { color: #f1f5f9 !important; font-weight: 600; font-size: 0.95rem; margin-bottom: 6px; }
        .custom-input { background-color: #0f172a !important; color: #ffffff !important; border: 1px solid #475569 !important; border-radius: 8px; padding: 12px; font-size: 1rem; }
        .custom-input:focus { border-color: #38bdf8 !important; box-shadow: 0 0 8px rgba(56, 189, 248, 0.4) !important; }
        .btn-custom { background: linear-gradient(135deg, #f59e0b, #d97706); border: none; color: #000000; font-weight: 700; padding: 12px; border-radius: 8px; font-size: 1.05rem; }
    </style>
</head>
<body>
    <div class="login-card p-4 shadow-lg">
        <h3 class="text-center text-warning mb-1 fw-bold">🎓 CA Student Portal</h3>
        <p class="text-center text-light mb-4" style="font-size: 0.85rem;">Target Exam Tracker Jan 2027</p>

        {% if error %}
            <div class="alert alert-danger p-2 text-center fw-bold" style="font-size: 0.9rem;">{{ error }}</div>
        {% endif %}

        <form method="POST">
            <div class="mb-3">
                <label class="form-label">📱 Mobile Number</label>
                <input type="text" id="mobileInput" name="mobile" class="form-control custom-input" placeholder="Enter Mobile Number" required autocomplete="off" oninput="checkAdmin()">
            </div>

            <div class="mb-3">
                <label class="form-label">👤 Full Name <span class="text-warning" style="font-size: 0.75rem;">(For New Account)</span></label>
                <input type="text" name="name" class="form-control custom-input" placeholder="Enter your full name" autocomplete="off">
            </div>

            <div class="mb-3">
                <label class="form-label">🎂 Date of Birth</label>
                <input type="text" name="dob" class="form-control custom-input" placeholder="e.g. 15/08/2005" autocomplete="off">
            </div>

            <!-- Dynamic Admin Password Security Trigger -->
            <div class="mb-3 d-none" id="adminBox">
                <label class="form-label text-warning">🛡️ Admin Security Password</label>
                <input type="password" name="admin_pass" class="form-control custom-input border-warning" placeholder="Enter Admin Password">
            </div>

            <div class="mb-4">
                <label class="form-label">🔑 4-Digit Security PIN</label>
                <input type="password" name="pin" class="form-control custom-input" placeholder="Set or Enter 4-Digit PIN" required maxlength="4">
            </div>

            <button type="submit" class="btn btn-custom w-100 shadow">Login / Register Now 🚀</button>
        </form>
    </div>

    <script>
        function checkAdmin() {
            const mob = document.getElementById('mobileInput').value.trim();
            const adminBox = document.getElementById('adminBox');
            if (mob === '9693471716' || mob.toLowerCase() === 'admin') {
                adminBox.classList.remove('d-none');
            } else {
                adminBox.classList.add('d-none');
            }
        }
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user_id' in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, mobile, dob, profile_pic, manifestation_completed FROM users WHERE id = ?", (session['user_id'],))
        row = cursor.fetchone()
        
        user_name = row['name'] if row else 'Student'
        user_mobile = row['mobile'] if row else ''
        user_dob = row['dob'] if row else ''
        user_pic = row['profile_pic'] if row else ''
        manifestation_done = row['manifestation_completed'] if row else 0

        cursor.execute("SELECT item_id, status FROM user_progress WHERE user_id = ?", (session['user_id'],))
        progress_data = {r['item_id']: r['status'] for r in cursor.fetchall()}
        conn.close()
        
        return render_template_string(
            HTML_TEMPLATE, 
            user_name=user_name, 
            user_mobile=user_mobile, 
            user_dob=user_dob,
            user_pic=user_pic,
            manifestation_done=manifestation_done,
            icai_syllabus=ICAI_SYLLABUS, 
            personal_syllabus=PERSONAL_SYLLABUS, 
            user_progress=progress_data
        )

    if request.method == 'POST':
        mobile = request.form.get('mobile', '').strip()
        name = request.form.get('name', '').strip()
        dob = request.form.get('dob', '').strip()
        pin = request.form.get('pin', '').strip()
        admin_pass = request.form.get('admin_pass', '').strip()

        if (mobile == '9693471716' or mobile.toLowerCase() == 'admin') and admin_pass != 'admin123':
            return render_template_string(LOGIN_TEMPLATE, error="Invalid Admin Security Password!")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, pin FROM users WHERE mobile = ?", (mobile,))
        user = cursor.fetchone()

        if user:
            if str(user['pin']) == str(pin):
                session.permanent = True
                session['user_id'] = user['id']
                conn.close()
                return redirect(url_for('home'))
            else:
                conn.close()
                return render_template_string(LOGIN_TEMPLATE, error="Invalid PIN! Please try again.")
        else:
            if not name:
                conn.close()
                return render_template_string(LOGIN_TEMPLATE, error="Please enter your Name to register!")
            cursor.execute("INSERT INTO users (mobile, name, dob, pin) VALUES (?, ?, ?, ?)", (mobile, name, dob, pin))
            conn.commit()
            user_id = cursor.lastrowid
            session.permanent = True
            session['user_id'] = user_id
            conn.close()
            return redirect(url_for('home'))

    return render_template_string(LOGIN_TEMPLATE)

@app.route('/upload_profile_pic', methods=['POST'])
def upload_profile_pic():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file.filename != '':
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                filename = f"user_{session['user_id']}.{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET profile_pic = ? WHERE id = ?", (filename, session['user_id']))
                conn.commit()
                conn.close()
    return redirect(url_for('home'))

@app.route('/save_manifestation', methods=['POST'])
def save_manifestation():
    if 'user_id' in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET manifestation_completed = 1 WHERE id = ?", (session['user_id'],))
        conn.commit()
        conn.close()
    return redirect(url_for('home'))

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
