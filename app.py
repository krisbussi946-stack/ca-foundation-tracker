from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import sqlite3
import os
from datetime import date, timedelta
import math

app = Flask(__name__)
app.secret_key = "ca_foundation_jan27_secret_key"

# Database Path
DB_PATH = "/mnt/chromeos/shared/removable/1TB/ca_tracker_db/castudy.db"

# 🔑 ADMIN DETAILS
ADMIN_PHONE = "9693471716"        # <--- Yahan apna 10-digit Mobile Number daalein
ADMIN_PASSWORD = "RajubangyaCA@380"  # <--- Strong Admin Password

# Telegram Channel / DM Link
TELEGRAM_LINK = "https://t.me/+T00sbNCe1eU3ZWQ1" # <--- Yahan apna Telegram Link daalein

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dob TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            target_attempt TEXT,
            daily_hours TEXT,
            role TEXT DEFAULT 'student',
            onboarding_done INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chapter_id INTEGER,
            status TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, chapter_id)
        );
    ''')
    conn.commit()
    conn.close()

init_db()

# Full Official ICAI CA Foundation Syllabus
CHAPTERS = [
    # Paper 1: Accounting
    {"id": 1, "subject": "Paper 1: Accounting", "chapter": "Ch 1: Theoretical Framework", "name": "Unit 1: Meaning & Scope of Accounting"},
    {"id": 2, "subject": "Paper 1: Accounting", "chapter": "Ch 1: Theoretical Framework", "name": "Unit 2: Accounting Concepts, Principles & Conventions"},
    {"id": 3, "subject": "Paper 1: Accounting", "chapter": "Ch 1: Theoretical Framework", "name": "Unit 3: Capital & Revenue Expenditures and Receipts"},
    {"id": 4, "subject": "Paper 1: Accounting", "chapter": "Ch 1: Theoretical Framework", "name": "Unit 4: Contingent Assets & Contingent Liabilities"},
    {"id": 5, "subject": "Paper 1: Accounting", "chapter": "Ch 1: Theoretical Framework", "name": "Unit 5: Accounting Policies"},
    {"id": 6, "subject": "Paper 1: Accounting", "chapter": "Ch 1: Theoretical Framework", "name": "Unit 6: Accounting Estimates & Valuation Principles"},
    {"id": 7, "subject": "Paper 1: Accounting", "chapter": "Ch 1: Theoretical Framework", "name": "Unit 7: Accounting Standards (AS) & Ind AS"},

    {"id": 8, "subject": "Paper 1: Accounting", "chapter": "Ch 2: Accounting Process", "name": "Unit 1: Basic Accounting Procedures - Journal Entries"},
    {"id": 9, "subject": "Paper 1: Accounting", "chapter": "Ch 2: Accounting Process", "name": "Unit 2: Ledger Posting & Balancing"},
    {"id": 10, "subject": "Paper 1: Accounting", "chapter": "Ch 2: Accounting Process", "name": "Unit 3: Trial Balance Preparation"},
    {"id": 11, "subject": "Paper 1: Accounting", "chapter": "Ch 2: Accounting Process", "name": "Unit 4: Subsidiary Books (Purchase, Sales, Returns)"},
    {"id": 12, "subject": "Paper 1: Accounting", "chapter": "Ch 2: Accounting Process", "name": "Unit 5: Cash Book & Petty Cash Book"},
    {"id": 13, "subject": "Paper 1: Accounting", "chapter": "Ch 2: Accounting Process", "name": "Unit 6: Rectification of Errors"},

    {"id": 14, "subject": "Paper 1: Accounting", "chapter": "Ch 3: Bank Reconciliation Statement", "name": "Unit 1: BRS Preparation & Adjusted Cash Book"},
    {"id": 15, "subject": "Paper 1: Accounting", "chapter": "Ch 4: Inventories", "name": "Unit 1: Inventory Valuation (FIFO, LIFO, Weighted Avg)"},
    {"id": 16, "subject": "Paper 1: Accounting", "chapter": "Ch 5: Depreciation & Amortisation", "name": "Unit 1: Methods of Depreciation (SLM, WDV, Revaluation)"},
    {"id": 17, "subject": "Paper 1: Accounting", "chapter": "Ch 6: Bills of Exchange", "name": "Unit 1: Bills of Exchange & Promissory Notes Accounting"},

    {"id": 18, "subject": "Paper 1: Accounting", "chapter": "Ch 7: Final Accounts of Sole Proprietors", "name": "Unit 1: Final Accounts of Non-Manufacturing Entities"},
    {"id": 19, "subject": "Paper 1: Accounting", "chapter": "Ch 7: Final Accounts of Sole Proprietors", "name": "Unit 2: Final Accounts of Manufacturing Entities"},

    {"id": 20, "subject": "Paper 1: Accounting", "chapter": "Ch 8: Not-for-Profit Organisations (NPO)", "name": "Unit 1: Receipts & Payments, Income & Expenditure Accounts"},
    {"id": 21, "subject": "Paper 1: Accounting", "chapter": "Ch 9: Accounts from Incomplete Records", "name": "Unit 1: Single Entry System & Conversion Method"},

    {"id": 22, "subject": "Paper 1: Accounting", "chapter": "Ch 10: Partnership & LLP Accounts", "name": "Unit 1: Introduction & Profit Loss Appropriation"},
    {"id": 23, "subject": "Paper 1: Accounting", "chapter": "Ch 10: Partnership & LLP Accounts", "name": "Unit 2: Goodwill Valuation & Accounting"},
    {"id": 24, "subject": "Paper 1: Accounting", "chapter": "Ch 10: Partnership & LLP Accounts", "name": "Unit 3: Admission of a Partner"},
    {"id": 25, "subject": "Paper 1: Accounting", "chapter": "Ch 10: Partnership & LLP Accounts", "name": "Unit 4: Retirement of a Partner"},
    {"id": 26, "subject": "Paper 1: Accounting", "chapter": "Ch 10: Partnership & LLP Accounts", "name": "Unit 5: Death of a Partner & JLP/SLP Treatment"},
    {"id": 27, "subject": "Paper 1: Accounting", "chapter": "Ch 10: Partnership & LLP Accounts", "name": "Unit 6: Dissolution of Partnership Firms & LLPs"},

    {"id": 28, "subject": "Paper 1: Accounting", "chapter": "Ch 11: Company Accounts", "name": "Unit 1: Introduction to Company Accounts & Share Capital"},
    {"id": 29, "subject": "Paper 1: Accounting", "chapter": "Ch 11: Company Accounts", "name": "Unit 2: Issue, Forfeiture & Re-issue of Shares"},
    {"id": 30, "subject": "Paper 1: Accounting", "chapter": "Ch 11: Company Accounts", "name": "Unit 3: Issue of Debentures"},
    {"id": 31, "subject": "Paper 1: Accounting", "chapter": "Ch 11: Company Accounts", "name": "Unit 4: Accounting for Bonus Issue & Right Issue"},
    {"id": 32, "subject": "Paper 1: Accounting", "chapter": "Ch 11: Company Accounts", "name": "Unit 5: Redemption of Preference Shares"},
    {"id": 33, "subject": "Paper 1: Accounting", "chapter": "Ch 11: Company Accounts", "name": "Unit 6: Redemption of Debentures"},

    # Paper 2: Business Laws
    {"id": 34, "subject": "Paper 2: Business Laws", "chapter": "Ch 1: Regulatory Framework", "name": "Unit 1: Indian Regulatory Framework & Legal Structure"},

    {"id": 35, "subject": "Paper 2: Business Laws", "chapter": "Ch 2: The Indian Contract Act, 1872", "name": "Unit 1: Nature & Types of Contracts"},
    {"id": 36, "subject": "Paper 2: Business Laws", "chapter": "Ch 2: The Indian Contract Act, 1872", "name": "Unit 2: Offer, Acceptance & Consideration"},
    {"id": 37, "subject": "Paper 2: Business Laws", "chapter": "Ch 2: The Indian Contract Act, 1872", "name": "Unit 3: Capacity to Contract & Free Consent"},
    {"id": 38, "subject": "Paper 2: Business Laws", "chapter": "Ch 2: The Indian Contract Act, 1872", "name": "Unit 4: Performance of Contract"},
    {"id": 39, "subject": "Paper 2: Business Laws", "chapter": "Ch 2: The Indian Contract Act, 1872", "name": "Unit 5: Breach of Contract & Remedies"},
    {"id": 40, "subject": "Paper 2: Business Laws", "chapter": "Ch 2: The Indian Contract Act, 1872", "name": "Unit 6: Contingent & Quasi Contracts"},
    {"id": 41, "subject": "Paper 2: Business Laws", "chapter": "Ch 2: The Indian Contract Act, 1872", "name": "Unit 7: Contract of Indemnity & Guarantee"},
    {"id": 42, "subject": "Paper 2: Business Laws", "chapter": "Ch 2: The Indian Contract Act, 1872", "name": "Unit 8: Bailment & Pledge"},
    {"id": 43, "subject": "Paper 2: Business Laws", "chapter": "Ch 2: The Indian Contract Act, 1872", "name": "Unit 9: Law of Agency"},

    {"id": 44, "subject": "Paper 2: Business Laws", "chapter": "Ch 3: The Sale of Goods Act, 1930", "name": "Unit 1: Formation of Contract of Sale"},
    {"id": 45, "subject": "Paper 2: Business Laws", "chapter": "Ch 3: The Sale of Goods Act, 1930", "name": "Unit 2: Conditions & Warranties"},
    {"id": 46, "subject": "Paper 2: Business Laws", "chapter": "Ch 3: The Sale of Goods Act, 1930", "name": "Unit 3: Transfer of Ownership & Delivery of Goods"},
    {"id": 47, "subject": "Paper 2: Business Laws", "chapter": "Ch 3: The Sale of Goods Act, 1930", "name": "Unit 4: Unpaid Seller & Rights against Goods"},

    {"id": 48, "subject": "Paper 2: Business Laws", "chapter": "Ch 4: The Indian Partnership Act, 1932", "name": "Unit 1: General Nature of Partnership"},
    {"id": 49, "subject": "Paper 2: Business Laws", "chapter": "Ch 4: The Indian Partnership Act, 1932", "name": "Unit 2: Mutual Relations of Partners"},
    {"id": 50, "subject": "Paper 2: Business Laws", "chapter": "Ch 4: The Indian Partnership Act, 1932", "name": "Unit 3: Registration & Dissolution of Firm"},

    {"id": 51, "subject": "Paper 2: Business Laws", "chapter": "Ch 5: The LLP Act, 2008", "name": "Unit 1: Limited Liability Partnership Concept & Features"},

    {"id": 52, "subject": "Paper 2: Business Laws", "chapter": "Ch 6: The Companies Act, 2013", "name": "Unit 1: Incorporation of Company & Types of Companies"},

    {"id": 53, "subject": "Paper 2: Business Laws", "chapter": "Ch 7: Negotiable Instruments Act, 1881", "name": "Unit 1: Promissory Notes, Cheques & Dishonour"},

    # Paper 3: Quantitative Aptitude
    {"id": 54, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Business Mathematics", "name": "Maths Ch 1: Ratio, Proportion, Indices & Logarithms"},
    {"id": 55, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Business Mathematics", "name": "Maths Ch 2: Linear, Quadratic & Simultaneous Equations"},
    {"id": 56, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Business Mathematics", "name": "Maths Ch 3: Linear Inequalities with Graphs"},
    {"id": 57, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Business Mathematics", "name": "Maths Ch 4: Mathematics of Finance (SI, CI, Annuity, Perpetuity)"},
    {"id": 58, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Business Mathematics", "name": "Maths Ch 5: Basic Permutations & Combinations"},
    {"id": 59, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Business Mathematics", "name": "Maths Ch 6: Sequence & Series (AP & GP)"},
    {"id": 60, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Business Mathematics", "name": "Maths Ch 7: Sets, Relations, Functions, Limits & Continuity"},
    {"id": 61, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Business Mathematics", "name": "Maths Ch 8: Differential & Integral Calculus Applications"},

    {"id": 62, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Logical Reasoning", "name": "LR Ch 9: Number Series, Coding-Decoding & Odd Man Out"},
    {"id": 63, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Logical Reasoning", "name": "LR Ch 10: Direction Sense Test"},
    {"id": 64, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Logical Reasoning", "name": "LR Ch 11: Seating Arrangements (Linear & Circular)"},
    {"id": 65, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Logical Reasoning", "name": "LR Ch 12: Blood Relations"},

    {"id": 66, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Statistics", "name": "Stats Ch 13 - Unit 1: Statistical Description of Data"},
    {"id": 67, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Statistics", "name": "Stats Ch 13 - Unit 2: Sampling Methods & Data Collection"},
    {"id": 68, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Statistics", "name": "Stats Ch 14 - Unit 1: Measures of Central Tendency (Mean, Median, Mode)"},
    {"id": 69, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Statistics", "name": "Stats Ch 14 - Unit 2: Measures of Dispersion (SD, QD, MD, Variance)"},
    {"id": 70, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Statistics", "name": "Stats Ch 15: Probability Concepts & Bayes Theorem"},
    {"id": 71, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Statistics", "name": "Stats Ch 16: Theoretical Distributions (Binomial, Poisson, Normal)"},
    {"id": 72, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Statistics", "name": "Stats Ch 17: Correlation Coefficient & Regression Lines"},
    {"id": 73, "subject": "Paper 3: Quantitative Aptitude", "chapter": "Statistics", "name": "Stats Ch 18: Index Numbers & Time Series Analysis"},

    # Paper 4: Business Economics
    {"id": 74, "subject": "Paper 4: Business Economics", "chapter": "Ch 1: Scope of Business Economics", "name": "Unit 1: Introduction, Nature & Scope of Business Economics"},
    {"id": 75, "subject": "Paper 4: Business Economics", "chapter": "Ch 1: Scope of Business Economics", "name": "Unit 2: Basic Problems of an Economy & Role of Price Mechanism"},

    {"id": 76, "subject": "Paper 4: Business Economics", "chapter": "Ch 2: Utility, Demand & Supply", "name": "Unit 1: Law of Demand & Elasticity of Demand"},
    {"id": 77, "subject": "Paper 4: Business Economics", "chapter": "Ch 2: Utility, Demand & Supply", "name": "Unit 2: Consumer Behaviour (Cardinal & Indifference Curve)"},
    {"id": 78, "subject": "Paper 4: Business Economics", "chapter": "Ch 2: Utility, Demand & Supply", "name": "Unit 3: Supply Analysis & Elasticity of Supply"},

    {"id": 79, "subject": "Paper 4: Business Economics", "chapter": "Ch 3: Production & Cost", "name": "Unit 1: Theory of Production (Law of Variable Proportions & Returns)"},
    {"id": 80, "subject": "Paper 4: Business Economics", "chapter": "Ch 3: Production & Cost", "name": "Unit 2: Theory of Cost (Short Run & Long Run Cost Curves)"},

    {"id": 81, "subject": "Paper 4: Business Economics", "chapter": "Ch 4: Price Determination in Markets", "name": "Unit 1: Meaning & Classification of Market Forms"},
    {"id": 82, "subject": "Paper 4: Business Economics", "chapter": "Ch 4: Price Determination in Markets", "name": "Unit 2: Determination of Prices in General Equilibrium"},
    {"id": 83, "subject": "Paper 4: Business Economics", "chapter": "Ch 4: Price Determination in Markets", "name": "Unit 3: Price-Output Determination (Perfect Comp, Monopoly, Monop, Oligopoly)"},

    {"id": 84, "subject": "Paper 4: Business Economics", "chapter": "Ch 5: Business Cycles", "name": "Unit 1: Phases of Business Cycles & Economic Indicators"},
    {"id": 85, "subject": "Paper 4: Business Economics", "chapter": "Ch 6: National Income", "name": "Unit 1: National Income Aggregates & Measurement Methods"},
    {"id": 86, "subject": "Paper 4: Business Economics", "chapter": "Ch 6: National Income", "name": "Unit 2: Keynesian Theory of National Income Determination"},

    {"id": 87, "subject": "Paper 4: Business Economics", "chapter": "Ch 7: Public Finance", "name": "Unit 1: Fiscal Functions & Allocation of Resources"},
    {"id": 88, "subject": "Paper 4: Business Economics", "chapter": "Ch 7: Public Finance", "name": "Unit 2: Market Failure & Government Interventions"},
    {"id": 89, "subject": "Paper 4: Business Economics", "chapter": "Ch 7: Public Finance", "name": "Unit 3: Budget Making Process & Types of Budgets"},
    {"id": 90, "subject": "Paper 4: Business Economics", "chapter": "Ch 7: Public Finance", "name": "Unit 4: Fiscal Policy Objectives & Instruments"},

    {"id": 91, "subject": "Paper 4: Business Economics", "chapter": "Ch 8: Money Market", "name": "Unit 1: Concept of Demand for Money"},
    {"id": 92, "subject": "Paper 4: Business Economics", "chapter": "Ch 8: Money Market", "name": "Unit 2: Concept of Money Supply & Multiplier"},
    {"id": 93, "subject": "Paper 4: Business Economics", "chapter": "Ch 8: Money Market", "name": "Unit 3: Monetary Policy & RBI Functions"},

    {"id": 94, "subject": "Paper 4: Business Economics", "chapter": "Ch 9: International Trade", "name": "Unit 1: Theories of International Trade (Adam Smith, Ricardo, Heckscher-Ohlin)"},
    {"id": 95, "subject": "Paper 4: Business Economics", "chapter": "Ch 9: International Trade", "name": "Unit 2: Trade Policy Instruments (Tariffs & Non-Tariff Barriers)"},
    {"id": 96, "subject": "Paper 4: Business Economics", "chapter": "Ch 9: International Trade", "name": "Unit 3: Trade Negotiations & World Trade Organisation (WTO)"},
    {"id": 97, "subject": "Paper 4: Business Economics", "chapter": "Ch 9: International Trade", "name": "Unit 4: Exchange Rate Determination & Regime Types"},
    {"id": 98, "subject": "Paper 4: Business Economics", "chapter": "Ch 9: International Trade", "name": "Unit 5: Foreign Capital Movements (FDI & FPI)"},

    {"id": 99, "subject": "Paper 4: Business Economics", "chapter": "Ch 10: Indian Economy", "name": "Unit 1: Overview of Indian Economy, Reforms & Current Performance"}
]

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CA Foundation Jan 2027 Portal - Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #0f172a; color: #ffffff; font-family: 'Segoe UI', system-ui, sans-serif; display: flex; align-items: center; justify-content: justify; min-height: 100vh; }
        .login-card { background-color: #1e293b; border: 1px solid #475569; border-radius: 20px; width: 100%; max-width: 420px; padding: 2rem; margin: auto; }
        .form-control, .form-select { background-color: #0f172a !important; color: #ffffff !important; border-color: #475569 !important; }
        .form-control::placeholder { color: #94a3b8 !important; }
        label { color: #cbd5e1 !important; font-weight: 600; }
    </style>
</head>
<body>
    <div class="login-card text-center shadow-lg">
        <h2 class="fw-bold text-info mb-1">🎯 CA Foundation</h2>
        <p class="text-light small mb-4" style="color: #94a3b8 !important;">Jan 2027 Student Tracker Portal</p>
        
        {% if error %}
            <div class="alert alert-danger py-2 small fw-bold">{{ error }}</div>
        {% endif %}

        <form action="/login" method="POST" class="text-start">
            <div class="mb-3">
                <label class="form-label small">Full Name (without CA prefix)</label>
                <input type="text" name="name" class="form-control" placeholder="e.g. Krishna" required>
            </div>
            <div class="mb-3">
                <label class="form-label small">Date of Birth</label>
                <input type="date" name="dob" class="form-control" required>
            </div>
            <div class="mb-3">
                <label class="form-label small">Mobile Number</label>
                <input type="tel" name="phone" id="phone-input" class="form-control" placeholder="10 Digit Phone Number" pattern="[0-9]{10}" required>
            </div>
            
            <div class="mb-4" id="admin-password-box" style="display: none;">
                <label class="form-label text-warning small">🔑 Admin Secret Password</label>
                <input type="password" name="admin_password" class="form-control border-warning" placeholder="Enter Password">
            </div>

            <button type="submit" class="btn btn-info w-100 fw-bold py-2 mt-2">Start Tracking 🚀</button>
        </form>

        <div class="mt-4 pt-3 border-top border-secondary text-center">
            <small class="d-block mb-2" style="color: #cbd5e1;">Need help or study doubts?</small>
            <a href="{{ telegram_link }}" target="_blank" class="btn btn-sm btn-outline-info rounded-pill px-3 fw-bold">
                ✈️ Join Telegram Channel / DM Admin
            </a>
        </div>
    </div>

    <script>
        document.getElementById('phone-input').addEventListener('input', function() {
            if (this.value === "{{ admin_phone }}") {
                document.getElementById('admin-password-box').style.display = 'block';
            } else {
                document.getElementById('admin-password-box').style.display = 'none';
            }
        });
    </script>
</body>
</html>
"""

ONBOARDING_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Profile Setup - CA Foundation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #0f172a; color: #ffffff; font-family: 'Segoe UI', system-ui, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .setup-card { background-color: #1e293b; border: 1px solid #475569; border-radius: 20px; width: 100%; max-width: 480px; padding: 2.5rem; margin: auto; }
        .form-select { background-color: #0f172a !important; color: #ffffff !important; border-color: #475569 !important; }
        option { background-color: #0f172a !important; color: #ffffff !important; }
        label { color: #cbd5e1 !important; font-weight: 600; }
    </style>
</head>
<body>
    <div class="setup-card shadow-lg">
        <h3 class="fw-bold text-info mb-1">📝 Manifestation & Target Setup</h3>
        <p class="small mb-4" style="color: #94a3b8 !important;">Set your study target details for Jan 2027 Attempt</p>

        <form action="/save_onboarding" method="POST">
            <div class="mb-3">
                <label class="form-label small">Target Attempt</label>
                <select name="target_attempt" class="form-select">
                    <option value="Jan 2027">Jan 2027 (Primary Target)</option>
                    <option value="June 2027">June 2027</option>
                </select>
            </div>
            <div class="mb-4">
                <label class="form-label small">Daily Target Study Hours</label>
                <select name="daily_hours" class="form-select">
                    <option value="4 Hours">4 Hours / Day</option>
                    <option value="6 Hours" selected>6 Hours / Day</option>
                    <option value="8 Hours">8 Hours / Day</option>
                    <option value="10+ Hours">10+ Hours / Day</option>
                </select>
            </div>
            <button type="submit" class="btn btn-success w-100 fw-bold py-2">Save & Continue to Tracker 🎯</button>
        </form>
    </div>
</body>
</html>
"""

TRACKER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CA Foundation Companion</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', system-ui, sans-serif; }
        .card { background-color: #1e293b; border: 1px solid #334155; border-radius: 16px; }
        .completed-text { text-decoration: line-through; color: #34d399 !important; font-weight: 600; }
        .unit-title { color: #f1f5f9; font-weight: 500; }
        .predictor-card { background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%); border: none; }
        .accordion-button { background-color: #1e293b; color: #38bdf8; font-weight: 600; font-size: 1.1rem; }
        .accordion-button:not(.collapsed) { background-color: #0f172a; color: #38bdf8; box-shadow: none; }
        .accordion-button::after { filter: invert(1); }
        .accordion-body { background-color: #0f172a; border-top: 1px solid #334155; }
        .unit-item { border-bottom: 1px solid #1e293b; transition: all 0.2s; cursor: pointer; }
        .unit-item:hover { background-color: #1e293b; }
        .form-check-input { width: 1.25em; height: 1.25em; cursor: pointer; }
        .form-check-input:checked { background-color: #10b981; border-color: #10b981; }
        .text-subtle { color: #cbd5e1 !important; }
    </style>
</head>
<body class="py-4">
    <div class="container" style="max-width: 900px;">
        
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h2 class="fw-bold text-info m-0">🎯 CA Foundation Tracker</h2>
                <small class="text-subtle">Target: {{ user.target_attempt }} | Daily Target: {{ user.daily_hours }}</small>
            </div>
            <div>
                {% if user.role == 'admin' %}
                    <a href="/admin" class="btn btn-warning btn-sm fw-bold me-2"><i class="bi bi-shield-lock-fill me-1"></i>👑 Admin Panel</a>
                {% endif %}
                <a href="/logout" class="btn btn-outline-danger btn-sm"><i class="bi bi-box-arrow-right me-1"></i>Logout</a>
            </div>
        </div>

        <div class="card predictor-card p-4 mb-4 shadow-lg text-white">
            <div class="d-flex justify-content-between align-items-center mb-3 border-bottom border-light border-opacity-25 pb-2">
                <h5 class="fw-bold text-warning mb-0"><i class="bi bi-person-badge-fill me-2"></i>CA {{ user.name }} {% if user.role == 'admin' %}(Admin){% endif %}</h5>
                <span class="badge bg-danger px-3 py-2 rounded-pill fs-6"><i class="bi bi-hourglass-split me-1"></i>{{ days_left }} Days Left</span>
            </div>
            
            <div class="row text-center my-3">
                <div class="col-4">
                    <span class="text-subtle small">Total Units</span>
                    <h3 class="fw-bold m-0 text-light" id="stat-total">{{ total_chapters }}</h3>
                </div>
                <div class="col-4 border-start border-end border-light border-opacity-25">
                    <span class="text-subtle small">Completed</span>
                    <h3 class="fw-bold m-0" style="color: #34d399;" id="stat-completed">{{ completed_count }}</h3>
                </div>
                <div class="col-4">
                    <span class="text-subtle small">Remaining</span>
                    <h3 class="fw-bold m-0" style="color: #fbbf24;" id="stat-remaining">{{ remaining_count }}</h3>
                </div>
            </div>

            <div class="row bg-black bg-opacity-25 p-3 rounded-3 align-items-center g-2 my-2">
                <div class="col-md-7 text-start">
                    <label class="form-label mb-0 fw-semibold text-light fs-6">Aap daily kitne Units padhenge?</label>
                    <small class="d-block text-subtle">(Ex: 1 = Daily 1 Unit, 2 = Daily 2 Units)</small>
                </div>
                <div class="col-md-5">
                    <div class="input-group">
                        <input type="number" step="0.1" min="0.1" id="daily-speed" class="form-control text-center fw-bold fs-5 bg-dark text-white border-secondary" value="1.0">
                        <span class="input-group-text bg-warning text-dark fw-bold">Unit / Day</span>
                    </div>
                </div>
            </div>

            <div class="p-3 bg-black bg-opacity-30 rounded-3 text-center mt-3">
                <p class="m-0 fs-6" id="personalized-msg">
                    🎯 <b>CA {{ user.name }}</b>, aapke <b id="msg-remaining" class="text-warning">{{ remaining_count }} Units remaining</b> hain.<br>
                    Is pace par aapka complete syllabus <b class="text-warning fs-5" id="predicted-date">{{ estimated_finish_date }}</b> tak finish hoga!
                </p>
            </div>
        </div>

        <div class="card p-3 mb-4">
            <div class="d-flex justify-content-between mb-2">
                <span class="fw-bold text-light"><i class="bi bi-graph-up-arrow me-2 text-info"></i>Overall Progress</span>
                <span class="fw-bold text-info fs-6" id="progress-text">{{ progress_percent }}% Completed</span>
            </div>
            <div class="progress" style="height: 20px; background-color: #0f172a;">
                <div id="progress-bar" class="progress-bar progress-bar-striped progress-bar-animated bg-success" 
                     role="progressbar" style="width: {{ progress_percent }}%;">
                </div>
            </div>
        </div>

        <div class="accordion mb-4" id="syllabuAccordion">
            {% for subject, chapters_dict in structured_syllabus.items() %}
                {% set outer_loop = loop %}
                <div class="accordion-item card mb-3">
                    <h2 class="accordion-header" id="heading{{ outer_loop.index }}">
                        <button class="accordion-button {{ 'collapsed' if not loop.first else '' }}" type="button" data-bs-toggle="collapse" data-bs-target="#collapse{{ outer_loop.index }}">
                            <i class="bi bi-journal-bookmark-fill me-2 text-primary"></i> {{ subject }}
                        </button>
                    </h2>
                    <div id="collapse{{ outer_loop.index }}" class="accordion-collapse collapse {{ 'show' if loop.first else '' }}" data-bs-parent="#syllabuAccordion">
                        <div class="accordion-body">
                            {% for ch_title, units in chapters_dict.items() %}
                                <div class="mb-3">
                                    <h6 class="fw-bold border-bottom border-secondary pb-2 mt-3" style="color: #fbbf24;">
                                        <i class="bi bi-folder2-open me-2"></i>{{ ch_title }}
                                    </h6>
                                    <div class="list-group list-group-flush">
                                        {% for u in units %}
                                            <label class="list-group-item unit-item d-flex align-items-center py-2 px-3 bg-transparent border-0">
                                                <input class="form-check-input me-3 chapter-checkbox" type="checkbox" 
                                                       value="{{ u.id }}" {{ 'checked' if u.id in completed_ids else '' }}>
                                                <span class="unit-title {{ 'completed-text' if u.id in completed_ids else '' }}">
                                                    {{ u.name }}
                                                </span>
                                            </label>
                                        {% endfor %}
                                    </div>
                                </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            {% endfor %}
        </div>

        <div class="card p-3 text-center mb-5 border-info bg-dark">
            <div class="d-flex align-items-center justify-content-between flex-wrap gap-2">
                <span class="text-light small">💬 Any doubts or support needed? Join our official community!</span>
                <a href="{{ telegram_link }}" target="_blank" class="btn btn-sm btn-info fw-bold">
                    <i class="bi bi-telegram me-1"></i> Telegram Channel / DM Admin
                </a>
            </div>
        </div>

    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function recalculatePrediction() {
            const speed = parseFloat(document.getElementById('daily-speed').value) || 1.0;
            const remaining = parseInt(document.getElementById('stat-remaining').innerText);
            
            if (speed <= 0 || remaining <= 0) {
                document.getElementById('predicted-date').innerText = "Syllabus Finished! 🎉";
                return;
            }

            const daysNeeded = Math.ceil(remaining / speed);
            const targetDate = new Date();
            targetDate.setDate(targetDate.getDate() + daysNeeded);

            const options = { day: 'numeric', month: 'short', year: 'numeric' };
            document.getElementById('predicted-date').innerText = targetDate.toLocaleDateString('en-GB', options);
        }

        document.getElementById('daily-speed').addEventListener('input', recalculatePrediction);

        document.querySelectorAll('.chapter-checkbox').forEach(box => {
            box.addEventListener('change', function() {
                const chapterId = this.value;
                const status = this.checked ? 'completed' : 'pending';
                const labelSpan = this.nextElementSibling;

                if (this.checked) {
                    labelSpan.classList.add('completed-text');
                } else {
                    labelSpan.classList.remove('completed-text');
                }

                fetch('/update_progress', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ chapter_id: chapterId, status: status })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('progress-bar').style.width = data.progress_percent + '%';
                        document.getElementById('progress-text').innerText = data.progress_percent + '% Completed';
                        document.getElementById('stat-completed').innerText = data.completed_count;
                        document.getElementById('stat-remaining').innerText = data.remaining_count;
                        document.getElementById('msg-remaining').innerText = data.remaining_count + ' Units remaining';
                        
                        recalculatePrediction();
                    }
                });
            });
        });
    </script>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>👑 Admin Control Panel</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <style>
        body { background-color: #0f172a; color: #ffffff; font-family: 'Segoe UI', system-ui, sans-serif; }
        .card { background-color: #1e293b; border: 1px solid #334155; border-radius: 16px; }
    </style>
</head>
<body class="py-4">
    <div class="container" style="max-width: 1000px;">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h2 class="fw-bold text-warning m-0"><i class="bi bi-shield-lock-fill me-2"></i>👑 Admin Control Panel</h2>
                <small class="text-light">Manage all CA Foundation Jan 2027 Students</small>
            </div>
            <div>
                <a href="/" class="btn btn-outline-info btn-sm me-2"><i class="bi bi-house-door me-1"></i>My Tracker</a>
                <a href="/logout" class="btn btn-outline-danger btn-sm"><i class="bi bi-box-arrow-right me-1"></i>Logout</a>
            </div>
        </div>

        <div class="card p-4 shadow-lg mb-4">
            <h5 class="fw-bold text-info mb-3"><i class="bi bi-people-fill me-2"></i>Registered Students ({{ students|length }})</h5>
            
            <div class="table-responsive">
                <table class="table table-dark table-hover align-middle border-secondary">
                    <thead>
                        <tr class="text-warning">
                            <th>ID</th>
                            <th>Student Name</th>
                            <th>DOB</th>
                            <th>Mobile</th>
                            <th>Target</th>
                            <th>Hours</th>
                            <th>Progress %</th>
                            <th>Joined On</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for s in students %}
                            <tr>
                                <td>{{ s.user_id }}</td>
                                <td class="fw-bold text-light">CA {{ s.name }}</td>
                                <td>{{ s.dob }}</td>
                                <td>{{ s.phone }}</td>
                                <td><span class="badge bg-info text-dark fw-bold">{{ s.target_attempt }}</span></td>
                                <td>{{ s.daily_hours }}</td>
                                <td>
                                    <div class="d-flex align-items-center">
                                        <span class="me-2 small fw-bold text-success">{{ s.progress_percent }}%</span>
                                        <div class="progress w-100" style="height: 8px;">
                                            <div class="progress-bar bg-success" style="width: {{ s.progress_percent }}%;"></div>
                                        </div>
                                    </div>
                                </td>
                                <td class="small text-light">{{ s.created_at }}</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    if 'user_id' not in session:
        return render_template_string(LOGIN_HTML, admin_phone=ADMIN_PHONE, telegram_link=TELEGRAM_LINK)

    user_id = session['user_id']
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    
    # Check if Onboarding is done
    if user and user['onboarding_done'] == 0:
        conn.close()
        return render_template_string(ONBOARDING_HTML)

    rows = conn.execute("SELECT chapter_id FROM user_progress WHERE user_id = ? AND status = 'completed'", (user_id,)).fetchall()
    conn.close()

    completed_ids = [row['chapter_id'] for row in rows]
    total_chapters = len(CHAPTERS)
    completed_count = len(completed_ids)
    remaining_count = total_chapters - completed_count
    progress_percent = round((completed_count / total_chapters) * 100) if total_chapters > 0 else 0

    days_needed = math.ceil(remaining_count / 1.0)
    estimated_finish_date = (date.today() + timedelta(days=days_needed)).strftime("%d %b %Y")

    structured_syllabus = {}
    for ch in CHAPTERS:
        subj = ch['subject']
        chap = ch['chapter']
        structured_syllabus.setdefault(subj, {}).setdefault(chap, []).append(ch)

    exam_date = date(2027, 1, 15)
    days_left = (exam_date - date.today()).days

    return render_template_string(TRACKER_HTML, 
                                  user=user,
                                  structured_syllabus=structured_syllabus, 
                                  completed_ids=completed_ids, 
                                  progress_percent=progress_percent,
                                  total_chapters=total_chapters,
                                  completed_count=completed_count,
                                  remaining_count=remaining_count,
                                  estimated_finish_date=estimated_finish_date,
                                  days_left=days_left,
                                  telegram_link=TELEGRAM_LINK)

@app.route('/login', methods=['POST'])
def login():
    name = request.form.get('name').strip()
    dob = request.form.get('dob')
    phone = request.form.get('phone').strip()
    admin_password = request.form.get('admin_password', '').strip()

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE phone = ?", (phone,)).fetchone()

    if phone == ADMIN_PHONE:
        if admin_password != ADMIN_PASSWORD:
            conn.close()
            return render_template_string(LOGIN_HTML, admin_phone=ADMIN_PHONE, telegram_link=TELEGRAM_LINK, error="Invalid Admin Secret Password!")
        
        if not user:
            cursor = conn.execute("INSERT INTO users (name, dob, phone, role) VALUES (?, ?, ?, 'admin')", (name, dob, phone))
            conn.commit()
            user_id = cursor.lastrowid
        else:
            conn.execute("UPDATE users SET role = 'admin' WHERE phone = ?", (phone,))
            conn.commit()
            user_id = user['user_id']
    else:
        if not user:
            cursor = conn.execute("INSERT INTO users (name, dob, phone, role) VALUES (?, ?, ?, 'student')", (name, dob, phone))
            conn.commit()
            user_id = cursor.lastrowid
        else:
            user_id = user['user_id']

    conn.close()
    session['user_id'] = user_id
    return redirect(url_for('home'))

@app.route('/save_onboarding', methods=['POST'])
def save_onboarding():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    target_attempt = request.form.get('target_attempt')
    daily_hours = request.form.get('daily_hours')

    conn = get_db_connection()
    conn.execute("UPDATE users SET target_attempt = ?, daily_hours = ?, onboarding_done = 1 WHERE user_id = ?", 
                 (target_attempt, daily_hours, session['user_id']))
    conn.commit()
    conn.close()

    return redirect(url_for('home'))

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    conn = get_db_connection()
    current_user = conn.execute("SELECT * FROM users WHERE user_id = ?", (session['user_id'],)).fetchone()

    if not current_user or current_user['role'] != 'admin':
        conn.close()
        return "Access Denied! Admin only area.", 403

    users = conn.execute("SELECT * FROM users").fetchall()
    total_units = len(CHAPTERS)

    students_data = []
    for u in users:
        p_rows = conn.execute("SELECT chapter_id FROM user_progress WHERE user_id = ? AND status = 'completed'", (u['user_id'],)).fetchall()
        c_count = len(p_rows)
        p_percent = round((c_count / total_units) * 100) if total_units > 0 else 0
        
        u_dict = dict(u)
        u_dict['completed_units'] = c_count
        u_dict['progress_percent'] = p_percent
        students_data.append(u_dict)

    conn.close()
    return render_template_string(ADMIN_HTML, students=students_data)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/update_progress', methods=['POST'])
def update_progress():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    user_id = session['user_id']
    data = request.get_json()
    chapter_id = int(data.get('chapter_id'))
    status = data.get('status')

    conn = get_db_connection()
    if status == 'completed':
        conn.execute('''
            INSERT INTO user_progress (user_id, chapter_id, status) 
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, chapter_id) DO UPDATE SET status = 'completed', last_updated = CURRENT_TIMESTAMP
        ''', (user_id, chapter_id, status))
    else:
        conn.execute("DELETE FROM user_progress WHERE user_id = ? AND chapter_id = ?", (user_id, chapter_id))
    
    conn.commit()

    rows = conn.execute("SELECT chapter_id FROM user_progress WHERE user_id = ? AND status = 'completed'", (user_id,)).fetchall()
    conn.close()

    total_chapters = len(CHAPTERS)
    completed_count = len(rows)
    remaining_count = total_chapters - completed_count
    progress_percent = round((completed_count / total_chapters) * 100) if total_chapters > 0 else 0

    return jsonify({
        "success": True, 
        "progress_percent": progress_percent,
        "completed_count": completed_count,
        "remaining_count": remaining_count
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
