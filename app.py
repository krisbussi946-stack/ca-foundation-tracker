import os
import urllib.parse as urlparse
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'ca_foundation_jan2027_pro_master_key_v9'
app.permanent_session_lifetime = timedelta(days=60)

# Cloud PostgreSQL Connection URL from Render Environment Variable
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    if DATABASE_URL:
        # Neon PostgreSQL Database Connection
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    else:
        # Fallback local connection if URL missing
        conn = psycopg2.connect(
            "postgresql://neondb_owner:npg_q9LY6igBNtGv@ep-raspy-lake-aw7xvwza.c-12.us-east-1.aws.neon.tech/neondb?sslmode=require"
        )
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            mobile VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            dob VARCHAR(50),
            pin VARCHAR(10) NOT NULL,
            is_blocked INTEGER DEFAULT 0
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_chats (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            user_name VARCHAR(100),
            message TEXT,
            media_url TEXT,
            timestamp VARCHAR(50) NOT NULL
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

init_db()

# ==========================================================
# ICAI OFFICIAL SYLLABUS DATA
# ==========================================================
ICAI_SYLLABUS = {
    "Paper-1: Accounting (Official ICAI Syllabus)": [
        {"chapter": "Chapter 1: Theoretical Framework", "units": ["Unit 1: Meaning and Scope of Accounting", "Unit 2: Accounting Concepts, Principles and Conventions", "Unit 3: Capital and Revenue Expenditures and Receipts", "Unit 4: Contingent Assets and Contingent Liabilities", "Unit 5: Accounting Policies", "Unit 6: Accounting as a Measurement Discipline", "Unit 7: Accounting Standards"]},
        {"chapter": "Chapter 2: Accounting Process", "units": ["Unit 1: Basic Accounting Procedures – Journal entries", "Unit 2: Ledgers", "Unit 3: Trial Balance", "Unit 4: Subsidiary Books", "Unit 5: Cash Book", "Unit 6: Rectification of Errors"]},
        {"chapter": "Chapter 3: Bank Reconciliation Statement", "units": ["Bank Reconciliation Statement"]},
        {"chapter": "Chapter 4: Inventories", "units": ["Inventories"]},
        {"chapter": "Chapter 5: Depreciation and Amortisation", "units": ["Depreciation and Amortisation"]},
        {"chapter": "Chapter 6: Bills of Exchange and Promissory Notes", "units": ["Bills of Exchange and Promissory Notes"]},
        {"chapter": "Chapter 7: Preparation of Final Accounts of Sole Proprietors", "units": ["Unit 1: Final Accounts of Non-Manufacturing Entities", "Unit 2: Final Accounts of Manufacturing Entities"]},
        {"chapter": "Chapter 8: Financial Statements of NPO", "units": ["Financial Statements of Not-for-Profit Organisations"]},
        {"chapter": "Chapter 9: Accounts from Incomplete Records", "units": ["Accounts from Incomplete Records"]},
        {"chapter": "Chapter 10: Partnership and LLP Accounts", "units": ["Unit 1: Introduction to Partnership Accounts", "Unit 2: Treatment of Goodwill in Partnership Accounts", "Unit 3: Admission of a New Partner", "Unit 4: Retirement of a Partner", "Unit 5: Death of a Partner", "Unit 6: Dissolution of Partnership Firms and LLPs"]},
        {"chapter": "Chapter 11: Company Accounts", "units": ["Unit 1: Introduction to Company Accounts", "Unit 2: Issue, Forfeiture and Re-Issue of Shares", "Unit 3: Issue of Debentures", "Unit 4: Accounting for Bonus Issue and Right Issue", "Unit 5: Redemption of Preference Shares", "Unit 6: Redemption of Debentures"]}
    ],
    "Paper-2: Business Laws (Official ICAI Syllabus)": [
        {"chapter": "Chapter 1: Indian Regulatory Framework", "units": ["Indian Regulatory Framework"]},
        {"chapter": "Chapter 2: The Indian Contract Act, 1872", "units": ["Unit 1: Nature of Contracts", "Unit 2: Consideration", "Unit 3: Other Essential Elements of a Contract", "Unit 4: Performance of Contract", "Unit 5: Breach of Contract and its Remedies", "Unit 6: Contingent and Quasi Contracts", "Unit 7: Contract of Indemnity and Guarantee", "Unit 8: Bailment and Pledge", "Unit 9: Agency"]},
        {"chapter": "Chapter 3: The Sale of Goods Act, 1930", "units": ["Unit 1: Formation of the Contract of Sale", "Unit 2: Conditions & Warranties", "Unit 3: Transfer of Ownership and Delivery of Goods", "Unit 4: Unpaid Seller"]},
        {"chapter": "Chapter 4: The Indian Partnership Act, 1932", "units": ["Unit 1: General Nature of Partnership", "Unit 2: Relations of Partners", "Unit 3: Registration and Dissolution of a Firm"]},
        {"chapter": "Chapter 5: The Limited Liability Partnership Act, 2008", "units": ["The Limited Liability Partnership Act, 2008"]},
        {"chapter": "Chapter 6: The Companies Act, 2013", "units": ["The Companies Act, 2013"]},
        {"chapter": "Chapter 7: The Negotiable Instruments Act, 1881", "units": ["The Negotiable Instruments Act, 1881"]}
    ],
    "Paper-3: Quantitative Aptitude (Official ICAI Syllabus)": [
        {"chapter": "PART-A: BUSINESS MATHEMATICS", "units": ["Chapter 1: Ratio and Proportion, Indices, Logarithms", "Chapter 2: Equations", "Chapter 3: Linear Inequalities", "Chapter 4: Mathematics of Finance", "Chapter 5: Basic Concepts of Permutations and Combinations", "Chapter 6: Sequence and Series", "Chapter 7: Sets, Relations and Functions", "Chapter 8: Calculus in Business and Economics"]},
        {"chapter": "PART-B: LOGICAL REASONING", "units": ["Chapter 9: Number Series, Coding-Decoding and Odd Man Out", "Chapter 10: Direction Sense Test", "Chapter 11: Seating Arrangements", "Chapter 12: Blood Relations"]},
        {"chapter": "PART-C: STATISTICS", "units": ["Chapter 13 Unit I: Statistical Description of Data", "Chapter 13 Unit II: Sampling", "Chapter 14 Unit I: Measures of Central Tendency", "Chapter 14 Unit II: Dispersion", "Chapter 15: Probability", "Chapter 16: Theoretical Distributions", "Chapter 17: Correlation and Regression", "Chapter 18: Index Numbers"]}
    ],
    "Paper-4: Business Economics (Official ICAI Syllabus)": [
        {"chapter": "Chapter 1: Nature & Scope of Business Economics", "units": ["Unit 1: Introduction", "Unit 2: Basic Problems of an Economy & Role of Price Mechanism"]},
        {"chapter": "Chapter 2: Theory of Demand and Supply", "units": ["Unit 1: Law of Demand and Elasticity of Demand", "Unit 2: Theory of Consumer Behaviour", "Unit 3: Supply"]},
        {"chapter": "Chapter 3: Theory of Production and Cost", "units": ["Unit 1: Theory of Production", "Unit 2: Theory of Cost"]},
        {"chapter": "Chapter 4: Price Determination in Different Markets", "units": ["Unit 1: Meaning and Types of Markets", "Unit 2: Determination of Prices", "Unit 3: Price Output Determination under Different Market Forms"]},
        {"chapter": "Chapter 5: Business Cycles", "units": ["Business Cycles"]},
        {"chapter": "Chapter 6: Determination of National Income", "units": ["Unit 1: National Income Accounting", "Unit 2: The Keynesian Theory of Determination of National Income"]},
        {"chapter": "Chapter 7: Public Finance", "units": ["Unit 1: Fiscal Functions: An Overview, Centre and State Finance", "Unit 2: Market Failure/ Government intervention to correct Market Failure", "Unit 3: Budget Making: Sources of Revenue, Expenditure & Public Debt", "Unit 4: Fiscal Policy"]},
        {"chapter": "Chapter 8: Money Market", "units": ["Unit 1: Concept of Money Demand: Important Theories", "Unit 2: Concept of Money Supply", "Unit 3: Monetary Policy"]},
        {"chapter": "Chapter 9: International Trade", "units": ["Unit 1: Theories of International Trade", "Unit 2: Instruments of Trade Policy", "Unit 3: Trade Negotiations", "Unit 4: Exchange Rate and Its Economic Effects", "Unit 5: International Capital Movements"]},
        {"chapter": "Chapter 10: Indian Economy", "units": ["Indian Economy"]}
    ]
}

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
    "Business Law (Lecture Planner)": [
        {"unit": "Category 1: Concept FastTrack Lectures (48 Lecs)", "lectures": [f"Law Concept Lec {i}" for i in range(1, 49)]},
        {"unit": "Category 2: Written Practice Sessions (24 Lecs)", "lectures": [f"Law Answer Writing Session {i}" for i in range(1, 25)]}
    ]
}

SHARED_LAYOUT_HEADER = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CA Foundation Target Portal</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #080c14; color: #f8fafc; font-family: 'Segoe UI', Tahoma, sans-serif; }
        .digital-clock-container { display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; }
        .clock-plate {
            background: linear-gradient(180deg, #1e293b 50%, #0f172a 50%);
            border: 2px solid #38bdf8;
            border-radius: 10px;
            padding: 10px 15px;
            min-width: 75px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(56, 189, 248, 0.2);
        }
        .clock-digit { font-size: 1.8rem; font-weight: 800; color: #fbbf24; font-family: 'Courier New', monospace; margin: 0; }
        .clock-label { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
        .subject-card { background-color: #111827; border: 1px solid #1f2937; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
        .accordion-button { background-color: #1f2937 !important; color: #f8fafc !important; font-weight: 600; }
        .accordion-button:not(.collapsed) { background-color: #374151 !important; color: #38bdf8 !important; }
        .accordion-item { background-color: #111827; border-color: #1f2937; }
        .form-check-input:checked { background-color: #10b981; border-color: #10b981; }
        .progress-bar-custom { background: linear-gradient(90deg, #3b82f6, #10b981); }
        .gold-input { color: #fbbf24 !important; font-weight: bold; background: #0f172a; border: 1px solid #f59e0b; }
        .chat-box { background: #111827; border: 1px solid #1f2937; border-radius: 12px; height: 380px; overflow-y: auto; padding: 15px; }
        .chat-msg { background: #1f2937; border-left: 3px solid #38bdf8; padding: 10px 14px; border-radius: 8px; margin-bottom: 12px; }
        .media-preview { max-width: 100%; max-height: 250px; border-radius: 8px; margin-top: 6px; }
        .pro-tip-box { background: linear-gradient(135deg, #1e1b4b, #312e81); border-left: 4px solid #f59e0b; padding: 15px; border-radius: 8px; }
        .action-card {
            background: linear-gradient(145deg, #1f2937, #111827);
            border: 2px solid #3b82f6;
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .action-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(59, 130, 246, 0.4);
            border-color: #fbbf24;
        }
        .table-custom th { background-color: #1f2937; color: #fbbf24; text-align: center; vertical-align: middle; font-size: 0.8rem; }
        .table-custom td { background-color: #111827; color: #ffffff; text-align: center; vertical-align: middle; font-size: 0.85rem; }
    </style>
</head>
<body>
    <div class="container py-4">
        <div class="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom border-secondary">
            <div class="d-flex align-items-center gap-3">
                <div class="rounded-circle bg-primary d-flex align-items-center justify-content-center text-white fw-bold" style="width: 48px; height: 48px; font-size: 1.2rem;">
                    {{ user_name[0] if user_name else 'S' }}
                </div>
                <div>
                    <h5 class="m-0 text-warning font-weight-bold">👤 {{ user_name }}</h5>
                    <small class="text-info">📱 {{ user_mobile }} | 🎂 {{ user_dob if user_dob else 'N/A' }}</small>
                </div>
            </div>

            <div class="d-flex align-items-center gap-2 flex-wrap">
                <a href="https://t.me/+T00sbNCe1eU3ZWQ1" target="_blank" class="btn btn-primary font-weight-bold shadow-sm">
                    ✈️ Join Telegram
                </a>
                
                {% if is_admin %}
                    <a href="{{ url_for('admin_panel') }}" class="btn btn-danger font-weight-bold shadow-sm">🛡️ Admin Panel</a>
                {% endif %}
                <a href="{{ url_for('community_chat') }}" class="btn btn-success font-weight-bold shadow-sm">💬 Group Chat</a>
                
                {% if active_page == 'icai' %}
                    <a href="{{ url_for('personal_planner') }}" class="btn btn-warning font-weight-bold shadow-sm">🎯 My Personal Planner ➔</a>
                {% else %}
                    <a href="{{ url_for('home') }}" class="btn btn-info font-weight-bold shadow-sm">📘 ICAI Tracker Page ➔</a>
                {% endif %}
                <a href="{{ url_for('logout') }}" class="btn btn-outline-danger btn-sm">Logout</a>
            </div>
        </div>

        <div class="bg-dark p-4 text-center mb-4 rounded-3 border border-secondary shadow-lg">
            <h5 class="text-light mb-3">⏳ TARGET EXAM COUNTDOWN: JAN 2027 ATTEMPT</h5>
            <div class="digital-clock-container">
                <div class="clock-plate border-warning">
                    <div class="clock-digit text-warning" id="total-days">000</div>
                    <div class="clock-label text-warning">Total Days Left</div>
                </div>

                <div class="clock-plate"><div class="clock-digit" id="months">00</div><div class="clock-label">Months</div></div>
                <div class="clock-plate"><div class="clock-digit" id="days">00</div><div class="clock-label">Days</div></div>
                <div class="clock-plate"><div class="clock-digit" id="hours">00</div><div class="clock-label">Hours</div></div>
                <div class="clock-plate"><div class="clock-digit" id="minutes">00</div><div class="clock-label">Minutes</div></div>
                <div class="clock-plate"><div class="clock-digit" id="seconds">00</div><div class="clock-label">Seconds</div></div>
            </div>
        </div>

        <div class="card bg-dark border-secondary p-3 mb-4">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="m-0 text-light">Overall Completion Progress</h6>
                <span class="badge bg-success fs-6" id="overall-percentage">0%</span>
            </div>
            <div class="progress" style="height: 14px;">
                <div class="progress-bar progress-bar-custom" id="overall-bar" style="width: 0%;"></div>
            </div>
        </div>
'''

SHARED_LAYOUT_FOOTER = '''
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function updateDigitalClock() {
            const examDate = new Date("January 1, 2027 00:00:00").getTime();
            const now = new Date().getTime();
            const diff = examDate - now;

            if (diff > 0) {
                const totalDays = Math.floor(diff / (1000 * 60 * 60 * 24));
                const months = Math.floor(diff / (1000 * 60 * 60 * 24 * 30.4375));
                const days = Math.floor((diff % (1000 * 60 * 60 * 24 * 30.4375)) / (1000 * 60 * 60 * 24));
                const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((diff % (1000 * 60)) / 1000);

                const tdElem = document.getElementById("total-days");
                if(tdElem) tdElem.innerText = totalDays;

                document.getElementById("months").innerText = months.toString().padStart(2, '0');
                document.getElementById("days").innerText = days.toString().padStart(2, '0');
                document.getElementById("hours").innerText = hours.toString().padStart(2, '0');
                document.getElementById("minutes").innerText = minutes.toString().padStart(2, '0');
                document.getElementById("seconds").innerText = seconds.toString().padStart(2, '0');
            }
        }
        setInterval(updateDigitalClock, 1000);
        updateDigitalClock();

        function calculateOverallProgress() {
            const total = document.querySelectorAll('.lec-checkbox').length;
            const checked = document.querySelectorAll('.lec-checkbox:checked').length;
            const percentage = total > 0 ? Math.round((checked / total) * 100) : 0;
            const elem = document.getElementById('overall-percentage');
            if (elem) {
                elem.innerText = percentage + '%';
                document.getElementById('overall-bar').style.width = percentage + '%';
            }
        }
        calculateOverallProgress();

        document.querySelectorAll('.lec-checkbox').forEach(chk => {
            chk.addEventListener('change', function() {
                const key = this.getAttribute('data-key');
                const status = this.checked ? 1 : 0;
                calculateOverallProgress();

                fetch('/update_progress', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({item_id: key, status: status})
                });
            });
        });

        function toggleGroupCheckboxes(groupId) {
            const group = document.getElementById(groupId);
            if (!group) return;
            const checkboxes = group.querySelectorAll('.lec-checkbox');
            if (checkboxes.length === 0) return;

            let allChecked = true;
            checkboxes.forEach(c => { if (!c.checked) allChecked = false; });

            const newStatus = allChecked ? 0 : 1;
            const bulkItems = [];

            checkboxes.forEach(c => {
                c.checked = !allChecked;
                bulkItems.push({
                    item_id: c.getAttribute('data-key'),
                    status: newStatus
                });
            });

            calculateOverallProgress();

            fetch('/bulk_update_progress', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({items: bulkItems})
            });
        }
    </script>
</body>
</html>
'''

ICAI_PAGE_TEMPLATE = SHARED_LAYOUT_HEADER + '''
    <h4 class="text-warning mb-3">📘 Official ICAI Syllabus Tracker Page</h4>
    {% for subject, chapters in syllabus.items() %}
    {% set subject_idx = loop.index %}
    <div class="subject-card p-3">
        <h5 class="text-info mb-3">📖 {{ subject }}</h5>
        <div class="accordion" id="accordion-icai-{{ subject_idx }}">
            {% for chap in chapters %}
            {% set chap_idx = loop.index %}
            {% set group_id = 'group-icai-' ~ subject_idx ~ '-' ~ chap_idx %}
            <div class="accordion-item" id="{{ group_id }}">
                <h2 class="accordion-header d-flex align-items-center justify-content-between pe-3">
                    <button class="accordion-button collapsed flex-grow-1" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-icai-{{ subject_idx }}-{{ chap_idx }}">
                        {{ chap.chapter }}
                    </button>
                    <button class="btn btn-sm btn-outline-warning ms-2" type="button" onclick="toggleGroupCheckboxes('{{ group_id }}')">
                        Select All ✅
                    </button>
                </h2>
                <div id="collapse-icai-{{ subject_idx }}-{{ chap_idx }}" class="accordion-collapse collapse">
                    <div class="accordion-body">
                        <div class="row">
                            {% for u in chap.units %}
                            {% set key = subject ~ '_' ~ chap.chapter ~ '_' ~ u %}
                            <div class="col-md-6 mb-2">
                                <div class="form-check">
                                    <input class="form-check-input lec-checkbox" type="checkbox" data-key="{{ key }}" id="chk-icai-{{ subject_idx }}-{{ chap_idx }}-{{ loop.index }}" {% if user_progress.get(key) == 1 %}checked{% endif %}>
                                    <label class="form-check-label text-light" for="chk-icai-{{ subject_idx }}-{{ chap_idx }}-{{ loop.index }}">
                                        {{ u }}
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
''' + SHARED_LAYOUT_FOOTER

PERSONAL_PAGE_TEMPLATE = SHARED_LAYOUT_HEADER + '''
    <h4 class="text-warning mb-4">🎯 Personal Study Dashboard</h4>
    
    <div class="row g-4 my-2">
        <div class="col-md-6">
            <a href="/view_lectures" class="text-decoration-none text-light">
                <div class="action-card h-100 d-flex flex-column justify-content-center align-items-center p-5">
                    <div style="font-size: 3.5rem;" class="mb-3">📚</div>
                    <h3 class="text-warning font-weight-bold mb-2">Chapter & Lecture Planner</h3>
                    <p class="text-muted">Full Page View: Track subject-wise FastTrack, concept lectures & written practice sessions.</p>
                    <span class="btn btn-warning mt-2 fw-bold">Open Full Screen Planner ➔</span>
                </div>
            </a>
        </div>

        <div class="col-md-6">
            <a href="/view_routine" class="text-decoration-none text-light">
                <div class="action-card h-100 d-flex flex-column justify-content-center align-items-center p-5">
                    <div style="font-size: 3.5rem;" class="mb-3">✍️</div>
                    <h3 class="text-info font-weight-bold mb-2">134-Day Daily Target Tracker</h3>
                    <p class="text-muted">Full Page Table View: Day 1 to Day 134 daily lectures, HW, Case Laws & Revision tracker.</p>
                    <span class="btn btn-info mt-2 fw-bold">Open 134-Day Routine Tracker ➔</span>
                </div>
            </a>
        </div>
    </div>
''' + SHARED_LAYOUT_FOOTER

FULL_LECTURES_TEMPLATE = SHARED_LAYOUT_HEADER + '''
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="text-warning m-0">📚 Chapter & Lecture Planner (Full Page)</h4>
        <a href="/personal_planner" class="btn btn-outline-warning btn-sm">⬅️ Back to Personal Dashboard</a>
    </div>

    {% for subject, units in syllabus.items() %}
    {% set s_idx = loop.index %}
    <div class="subject-card p-4">
        <h5 class="text-warning mb-3">📌 {{ subject }}</h5>
        <div class="accordion" id="accordion-personal-{{ s_idx }}">
            {% for unit_data in units %}
            {% set u_idx = loop.index %}
            {% set group_id = 'group-p-' ~ s_idx ~ '-' ~ u_idx %}
            <div class="accordion-item" id="{{ group_id }}">
                <h2 class="accordion-header d-flex align-items-center justify-content-between pe-3">
                    <button class="accordion-button collapsed flex-grow-1" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-p-{{ s_idx }}-{{ u_idx }}">
                        {{ unit_data.unit }}
                    </button>
                    <button class="btn btn-sm btn-outline-warning ms-2" type="button" onclick="toggleGroupCheckboxes('{{ group_id }}')">
                        Select All ✅
                    </button>
                </h2>
                <div id="collapse-p-{{ s_idx }}-{{ u_idx }}" class="accordion-collapse collapse">
                    <div class="accordion-body">
                        <div class="row">
                            {% for lec in unit_data.lectures %}
                            {% set lec_key = subject ~ '_' ~ unit_data.unit ~ '_' ~ lec %}
                            <div class="col-md-4 col-sm-6 mb-2">
                                <div class="form-check">
                                    <input class="form-check-input lec-checkbox" type="checkbox" data-key="{{ lec_key }}" id="chk-p-{{ s_idx }}-{{ u_idx }}-{{ loop.index }}" {% if user_progress.get(lec_key) == 1 %}checked{% endif %}>
                                    <label class="form-check-label text-light" for="chk-p-{{ s_idx }}-{{ u_idx }}-{{ loop.index }}">
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
''' + SHARED_LAYOUT_FOOTER

FULL_ROUTINE_TEMPLATE = SHARED_LAYOUT_HEADER + '''
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="text-info m-0">✍️ Day 1 to Day 134 Target Routine Planner</h4>
        <a href="/personal_planner" class="btn btn-outline-warning btn-sm">⬅️ Back to Personal Dashboard</a>
    </div>

    <div class="table-responsive subject-card p-3">
        <table class="table table-dark table-bordered table-custom">
            <thead>
                <tr>
                    <th style="min-width: 90px;">Day</th>
                    <th>1. Accounts Lec</th>
                    <th>2. Law Lec</th>
                    <th>3. Quants Lec</th>
                    <th>4. Eco Lec</th>
                    <th>5. Accounts HW</th>
                    <th>6. Law HW</th>
                    <th>7. Quants HW</th>
                    <th>8. Eco HW</th>
                    <th>9. 2 Case Laws</th>
                    <th>10. 10m LR Practice</th>
                    <th>11. 30m Law Rev</th>
                </tr>
            </thead>
            <tbody>
                {% for day in range(1, 135) %}
                <tr>
                    <td class="fw-bold text-warning">Day {{ day }}</td>
                    
                    {% set k1 = 'day_' ~ day ~ '_accounts_lec' %}
                    <td><input class="form-check-input lec-checkbox" type="checkbox" data-key="{{ k1 }}" {% if user_progress.get(k1) == 1 %}checked{% endif %}></td>
                    
                    {% set k2 = 'day_' ~ day ~ '_law_lec' %}
                    <td><input class="form-check-input lec-checkbox" type="checkbox" data-key="{{ k2 }}" {% if user_progress.get(k2) == 1 %}checked{% endif %}></td>
                    
                    {% set k3 = 'day_' ~ day ~ '_quants_lec' %}
                    <td><input class="form-check-input lec-checkbox" type="checkbox" data-key="{{ k3 }}" {% if user_progress.get(k3) == 1 %}checked{% endif %}></td>
                    
                    {% set k4 = 'day_' ~ day ~ '_eco_lec' %}
                    <td><input class="form-check-input lec-checkbox" type="checkbox" data-key="{{ k4 }}" {% if user_progress.get(k4) == 1 %}checked{% endif %}></td>
                    
                    {% set k5 = 'day_' ~ day ~ '_accounts_hw' %}
                    <td><input class="form-check-input lec-checkbox" type="checkbox" data-key="{{ k5 }}" {% if user_progress.get(k5) == 1 %}checked{% endif %}></td>
                    
                    {% set k6 = 'day_' ~ day ~ '_law_hw' %}
                    <td><input class="form-check-input lec-checkbox" type="checkbox" data-key="{{ k6 }}" {% if user_progress.get(k6) == 1 %}checked{% endif %}></td>
                    
                    {% set k7 = 'day_' ~ day ~ '_quants_hw' %}
                    <td><input class="form-check-input lec-checkbox" type="checkbox" data-key="{{ k7 }}" {% if user_progress.get(k7) == 1 %}checked{% endif %}></td>
                    
                    {% set k8 = 'day_' ~ day ~ '_eco_hw' %}
                    <td><input class="form-check-input lec-checkbox" type="checkbox" data-key="{{ k8 }}" {% if user_progress.get(k8) == 1 %}checked{% endif %}></td>
                    
                    {% set k9 = 'day_' ~ day ~ '_caselaws' %}
                    <td><input class="form-check-input lec-checkbox" type="checkbox" data-key="{{ k9 }}" {% if user_progress.get(k9) == 1 %}checked{% endif %}></td>
                    
                    {% set k10 = 'day_' ~ day ~ '_lr_practice' %}
                    <td><input class="form-check-input lec-checkbox" type="checkbox" data-key="{{ k10 }}" {% if user_progress.get(k10) == 1 %}checked{% endif %}></td>
                    
                    {% set k11 = 'day_' ~ day ~ '_law_revision' %}
                    <td><input class="form-check-input lec-checkbox" type="checkbox" data-key="{{ k11 }}" {% if user_progress.get(k11) == 1 %}checked{% endif %}></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="pro-tip-box shadow p-4 mt-3 mb-4">
        <h5 class="text-warning mb-2">🔥 Daily Execution Strategy</h5>
        <p class="m-0 text-light fs-6">
            "Har din ke 11 targets tick karke poora Day Complete karo. Consistency hi CA Foundation pass karwayegi! Krishna bhai, target clear hai!" 💪
        </p>
    </div>
''' + SHARED_LAYOUT_FOOTER

CHAT_PAGE_TEMPLATE = SHARED_LAYOUT_HEADER + '''
    <h4 class="text-warning mb-3">💬 Student Discussion Forum (Media & Links Enabled)</h4>
    <div class="chat-box mb-3" id="chatWindow">
        {% for msg in chat_messages %}
        <div class="chat-msg">
            <div class="d-flex justify-content-between">
                <strong class="text-warning">👤 {{ msg.user_name }}</strong>
                <small class="text-muted">{{ msg.timestamp }}</small>
            </div>
            {% if msg.message %}
                <p class="m-0 text-light mt-1">{{ msg.message }}</p>
            {% endif %}
            {% if msg.media_url %}
                {% if msg.media_url.endswith('.mp4') or msg.media_url.endswith('.webm') %}
                    <video src="{{ msg.media_url }}" controls class="media-preview mt-2"></video>
                {% else %}
                    <img src="{{ msg.media_url }}" class="media-preview mt-2" alt="Chat Media">
                {% endif %}
            {% endif %}
        </div>
        {% endfor %}
    </div>

    <form action="/send_chat" method="POST" class="d-flex flex-column gap-2">
        <input type="text" name="message" class="form-control gold-input" placeholder="Type message or paste link..." autocomplete="off">
        <input type="text" name="media_url" class="form-control bg-dark text-light border-secondary" placeholder="Optional: Direct Image / Short Video Link URL (.jpg, .png, .mp4)">
        <button type="submit" class="btn btn-warning font-weight-bold py-2">Send Message / Media 🚀</button>
    </form>
    <script>
        const chatWin = document.getElementById('chatWindow');
        chatWin.scrollTop = chatWin.scrollHeight;
    </script>
''' + SHARED_LAYOUT_FOOTER

ADMIN_PANEL_TEMPLATE = SHARED_LAYOUT_HEADER + '''
    <h4 class="text-warning mb-3">🛡️ Admin Control Panel</h4>
    <div class="table-responsive bg-dark p-3 rounded border border-secondary">
        <table class="table table-dark table-hover align-middle">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Student Name</th>
                    <th>Mobile Number</th>
                    <th>DOB</th>
                    <th>Progress (%)</th>
                    <th>Status Action</th>
                </tr>
            </thead>
            <tbody>
                {% for u in users_list %}
                <tr>
                    <td>{{ u.id }}</td>
                    <td class="text-warning font-weight-bold">{{ u.name }}</td>
                    <td>{{ u.mobile }}</td>
                    <td>{{ u.dob }}</td>
                    <td><span class="badge bg-success fs-6">{{ u.progress }}%</span></td>
                    <td>
                        {% if u.is_blocked %}
                            <a href="/toggle_block/{{ u.id }}" class="btn btn-sm btn-outline-success">Unblock User</a>
                        {% else %}
                            <a href="/toggle_block/{{ u.id }}" class="btn btn-sm btn-outline-danger">Block User 🚫</a>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
''' + SHARED_LAYOUT_FOOTER

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Student Portal</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #080c14; color: #ffffff; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px 0; font-family: 'Segoe UI', Roboto, sans-serif; }
        .login-card { background-color: #111827; border: 2px solid #3b82f6; border-radius: 16px; width: 100%; max-width: 420px; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5); }
        .form-label { color: #f1f5f9 !important; font-weight: 600; font-size: 0.95rem; margin-bottom: 6px; }
        .custom-input { background-color: #0f172a !important; color: #ffffff !important; border: 1px solid #374151 !important; border-radius: 8px; padding: 12px; font-size: 1rem; }
        .custom-input:focus { border-color: #38bdf8 !important; box-shadow: 0 0 8px rgba(56, 189, 248, 0.4) !important; }
        .btn-custom { background: linear-gradient(135deg, #f59e0b, #d97706); border: none; color: #000000; font-weight: 700; padding: 12px; border-radius: 8px; font-size: 1.05rem; }
    </style>
</head>
<body>
    <div class="login-card p-4 shadow-lg">
        <h3 class="text-center text-warning mb-1 fw-bold">🎓 Student Portal</h3>
        <p class="text-center text-light mb-4" style="font-size: 0.85rem;">CA Foundation Jan 2027 Target Planner</p>

        {% if error %}
            <div class="alert alert-danger p-2 text-center fw-bold" style="font-size: 0.9rem;">{{ error }}</div>
        {% endif %}

        <form method="POST">
            <div class="mb-3">
                <label class="form-label">📱 Mobile Number</label>
                <input type="text" id="mobileInput" name="mobile" class="form-control custom-input" placeholder="Enter Mobile Number" required autocomplete="off" oninput="checkAdmin()">
            </div>

            <div class="mb-3">
                <label class="form-label">👤 Full Name <span class="text-warning" style="font-size: 0.75rem;">(New Student)</span></label>
                <input type="text" name="name" class="form-control custom-input" placeholder="Enter your full name" autocomplete="off">
            </div>

            <div class="mb-3">
                <label class="form-label">🎂 Date of Birth</label>
                <input type="text" name="dob" class="form-control custom-input" placeholder="DD/MM/YYYY (e.g. 15/08/2005)" autocomplete="off">
            </div>

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
            if (mob === '9693471716') {
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
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT name, mobile, dob, is_blocked FROM users WHERE id = %s", (session['user_id'],))
        row = cursor.fetchone()
        
        if row and row['is_blocked'] == 1:
            session.clear()
            cursor.close()
            conn.close()
            return render_template_string(LOGIN_TEMPLATE, error="Your account has been blocked by Admin!")

        user_name = row['name'] if row else 'Student'
        user_mobile = row['mobile'] if row else ''
        user_dob = row['dob'] if row else ''

        cursor.execute("SELECT item_id, status FROM user_progress WHERE user_id = %s", (session['user_id'],))
        progress_data = {r['item_id']: r['status'] for r in cursor.fetchall()}
        cursor.close()
        conn.close()
        
        is_admin = (user_mobile == '9693471716')
        return render_template_string(
            ICAI_PAGE_TEMPLATE, 
            active_page='icai',
            is_admin=is_admin,
            user_name=user_name, 
            user_mobile=user_mobile, 
            user_dob=user_dob,
            syllabus=ICAI_SYLLABUS, 
            user_progress=progress_data
        )

    if request.method == 'POST':
        mobile = request.form.get('mobile', '').strip()
        name = request.form.get('name', '').strip()
        dob = request.form.get('dob', '').strip()
        pin = request.form.get('pin', '').strip()
        admin_pass = request.form.get('admin_pass', '').strip()

        if mobile == '9693471716' and admin_pass != 'RajubangyaCA@380':
            return render_template_string(LOGIN_TEMPLATE, error="Invalid Admin Security Password!")

        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, pin, is_blocked FROM users WHERE mobile = %s", (mobile,))
        user = cursor.fetchone()

        if user:
            if user['is_blocked'] == 1:
                cursor.close()
                conn.close()
                return render_template_string(LOGIN_TEMPLATE, error="Your account has been blocked by Admin!")

            if str(user['pin']) == str(pin):
                session.permanent = True
                session['user_id'] = user['id']
                cursor.close()
                conn.close()
                return redirect(url_for('home'))
            else:
                cursor.close()
                conn.close()
                return render_template_string(LOGIN_TEMPLATE, error="Invalid PIN! Please check and try again.")
        else:
            if not name:
                cursor.close()
                conn.close()
                return render_template_string(LOGIN_TEMPLATE, error="Please enter your Name to register new account!")
            cursor.execute("INSERT INTO users (mobile, name, dob, pin) VALUES (%s, %s, %s, %s) RETURNING id", (mobile, name, dob, pin))
            user_id = cursor.fetchone()['id']
            conn.commit()
            session.permanent = True
            session['user_id'] = user_id
            cursor.close()
            conn.close()
            return redirect(url_for('home'))

    return render_template_string(LOGIN_TEMPLATE)

@app.route('/personal_planner')
def personal_planner():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT name, mobile, dob FROM users WHERE id = %s", (session['user_id'],))
    row = cursor.fetchone()
    
    user_name = row['name'] if row else 'Student'
    user_mobile = row['mobile'] if row else ''
    user_dob = row['dob'] if row else ''

    cursor.execute("SELECT item_id, status FROM user_progress WHERE user_id = %s", (session['user_id'],))
    progress_data = {r['item_id']: r['status'] for r in cursor.fetchall()}
    cursor.close()
    conn.close()
    
    is_admin = (user_mobile == '9693471716')
    return render_template_string(
        PERSONAL_PAGE_TEMPLATE, 
        active_page='personal',
        is_admin=is_admin,
        user_name=user_name, 
        user_mobile=user_mobile, 
        user_dob=user_dob,
        user_progress=progress_data
    )

@app.route('/view_lectures')
def view_lectures():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT name, mobile, dob FROM users WHERE id = %s", (session['user_id'],))
    row = cursor.fetchone()
    
    user_name = row['name'] if row else 'Student'
    user_mobile = row['mobile'] if row else ''
    user_dob = row['dob'] if row else ''

    cursor.execute("SELECT item_id, status FROM user_progress WHERE user_id = %s", (session['user_id'],))
    progress_data = {r['item_id']: r['status'] for r in cursor.fetchall()}
    cursor.close()
    conn.close()
    
    is_admin = (user_mobile == '9693471716')
    return render_template_string(
        FULL_LECTURES_TEMPLATE, 
        active_page='personal',
        is_admin=is_admin,
        user_name=user_name, 
        user_mobile=user_mobile, 
        user_dob=user_dob,
        syllabus=PERSONAL_SYLLABUS, 
        user_progress=progress_data
    )

@app.route('/view_routine')
def view_routine():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT name, mobile, dob FROM users WHERE id = %s", (session['user_id'],))
    row = cursor.fetchone()
    
    user_name = row['name'] if row else 'Student'
    user_mobile = row['mobile'] if row else ''
    user_dob = row['dob'] if row else ''

    cursor.execute("SELECT item_id, status FROM user_progress WHERE user_id = %s", (session['user_id'],))
    progress_data = {r['item_id']: r['status'] for r in cursor.fetchall()}
    cursor.close()
    conn.close()
    
    is_admin = (user_mobile == '9693471716')
    return render_template_string(
        FULL_ROUTINE_TEMPLATE, 
        active_page='personal',
        is_admin=is_admin,
        user_name=user_name, 
        user_mobile=user_mobile, 
        user_dob=user_dob,
        user_progress=progress_data
    )

@app.route('/community_chat')
def community_chat():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT name, mobile, dob, is_blocked FROM users WHERE id = %s", (session['user_id'],))
    row = cursor.fetchone()
    
    if row and row['is_blocked'] == 1:
        session.clear()
        cursor.close()
        conn.close()
        return redirect(url_for('home'))

    user_name = row['name'] if row else 'Student'
    user_mobile = row['mobile'] if row else ''
    user_dob = row['dob'] if row else ''

    cursor.execute("SELECT user_name, message, media_url, timestamp FROM group_chats ORDER BY id ASC")
    chat_messages = cursor.fetchall()
    cursor.close()
    conn.close()

    is_admin = (user_mobile == '9693471716')
    return render_template_string(
        CHAT_PAGE_TEMPLATE,
        active_page='chat',
        is_admin=is_admin,
        user_name=user_name,
        user_mobile=user_mobile,
        user_dob=user_dob,
        chat_messages=chat_messages
    )

@app.route('/send_chat', methods=['POST'])
def send_chat():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT name, is_blocked FROM users WHERE id = %s", (session['user_id'],))
    u = cursor.fetchone()

    if u and u['is_blocked'] == 1:
        cursor.close()
        conn.close()
        session.clear()
        return redirect(url_for('home'))

    message = request.form.get('message', '').strip()
    media_url = request.form.get('media_url', '').strip()

    if message or media_url:
        user_name = u['name'] if u else 'Student'
        now_str = datetime.now().strftime("%I:%M %p, %d %b")

        cursor.execute("INSERT INTO group_chats (user_id, user_name, message, media_url, timestamp) VALUES (%s, %s, %s, %s, %s)",
                       (session['user_id'], user_name, message, media_url, now_str))
        conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('community_chat'))

@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT mobile, name, dob FROM users WHERE id = %s", (session['user_id'],))
    row = cursor.fetchone()

    if not row or row['mobile'] != '9693471716':
        cursor.close()
        conn.close()
        return redirect(url_for('home'))

    cursor.execute("SELECT id, name, mobile, dob, is_blocked FROM users")
    users = cursor.fetchall()
    
    users_list = []
    for u in users:
        cursor.execute("SELECT COUNT(*) as cnt FROM user_progress WHERE user_id = %s AND status = 1", (u['id'],))
        done = cursor.fetchone()['cnt']
        progress_pct = min(100, int((done / 350) * 100)) if done > 0 else 0
        users_list.append({
            "id": u['id'],
            "name": u['name'],
            "mobile": u['mobile'],
            "dob": u['dob'],
            "is_blocked": u['is_blocked'],
            "progress": progress_pct
        })

    cursor.close()
    conn.close()
    return render_template_string(
        ADMIN_PANEL_TEMPLATE,
        active_page='admin',
        is_admin=True,
        user_name=row['name'],
        user_mobile=row['mobile'],
        user_dob=row['dob'],
        users_list=users_list
    )

@app.route('/toggle_block/<int:target_user_id>')
def toggle_block(target_user_id):
    if 'user_id' not in session:
        return redirect(url_for('home'))

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT mobile FROM users WHERE id = %s", (session['user_id'],))
    admin_row = cursor.fetchone()

    if admin_row and admin_row['mobile'] == '9693471716':
        cursor.execute("SELECT is_blocked FROM users WHERE id = %s", (target_user_id,))
        usr = cursor.fetchone()
        if usr:
            new_status = 0 if usr['is_blocked'] == 1 else 1
            cursor.execute("UPDATE users SET is_blocked = %s WHERE id = %s", (new_status, target_user_id))
            conn.commit()

    cursor.close()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/bulk_update_progress', methods=['POST'])
def bulk_update_progress():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    items = data.get('items', [])

    conn = get_db()
    cursor = conn.cursor()
    for item in items:
        cursor.execute('''
            INSERT INTO user_progress (user_id, item_id, status)
            VALUES (%s, %s, %s)
            ON CONFLICT(user_id, item_id) DO UPDATE SET status=EXCLUDED.status
        ''', (session['user_id'], item['item_id'], item['status']))
    
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

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
        VALUES (%s, %s, %s)
        ON CONFLICT(user_id, item_id) DO UPDATE SET status=EXCLUDED.status
    ''', (session['user_id'], item_id, status))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
