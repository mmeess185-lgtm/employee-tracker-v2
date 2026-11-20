import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from pymongo import MongoClient
from bson import ObjectId
import auth

MONGO_URI = os.environ['MONGO_URI']
client = MongoClient(MONGO_URI)
db = client['employee_tracker']
collection = db['employees']                 # household labor
wareef_collection = db['wareef_employees']   # Wareef company employees (separate list)
COLLECTIONS = {'employees': collection, 'wareef': wareef_collection}

def load_employees(col=collection):
    docs = list(col.find())
    result = []
    for d in docs:
        d['_id'] = str(d['_id'])
        result.append(d)
    return result

def add_employee(emp, col=collection):
    emp.pop('_id', None)
    col.insert_one(emp)

def update_employee(doc_id, emp, col=collection):
    emp.pop('_id', None)
    col.update_one({'_id': ObjectId(doc_id)}, {'$set': emp})

def delete_employee(doc_id, col=collection):
    col.delete_one({'_id': ObjectId(doc_id)})

def api_collection(path):
    """'/api/wareef' -> (collection, None); '/api/wareef/<id>' -> (collection, id)."""
    parts = path.split('/')
    if len(parts) in (3, 4) and parts[1] == 'api' and parts[2] in COLLECTIONS:
        return COLLECTIONS[parts[2]], (parts[3] if len(parts) == 4 else None)
    return None, None

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Employee Tracker</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{--bg:#f5f4f0;--surface:#fff;--surface2:#f0efe9;--border:#e2e0d8;--border2:#cccac0;--text:#1a1916;--text2:#6b6860;--text3:#9e9c96;--accent:#1a6b4a;--accent-bg:#e8f4ee;--amber:#92500a;--amber-bg:#fdf0e0;--red:#8b2020;--red-bg:#fdeaea;--blue:#1a4a7a;--blue-bg:#e8f0fa;--purple:#5b3a8e;--purple-bg:#f0eaf9;--radius:8px;--radius-lg:12px;--font:'IBM Plex Sans',sans-serif;--mono:'IBM Plex Mono',monospace}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font);background:var(--bg);color:var(--text);min-height:100vh}
.app{max-width:1550px;margin:0 auto;padding:2rem 1.5rem}
.header{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:2rem;flex-wrap:wrap;gap:1rem}
.header-left h1{font-size:22px;font-weight:600;letter-spacing:-.3px}
.header-left p{font-size:13px;color:var(--text2);margin-top:3px}
.header-right{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:1.5rem}
.stat-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px 16px}
.stat-card .lbl{font-size:11px;color:var(--text3);font-weight:500;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px}
.stat-card .val{font-size:24px;font-weight:600;color:var(--text);line-height:1}
.stat-card .val.sm{font-size:15px;margin-top:3px}
.toolbar{display:flex;align-items:center;gap:10px;margin-bottom:1rem;flex-wrap:wrap}
.search-wrap{position:relative;flex:1;min-width:200px}
.search-wrap svg{position:absolute;left:11px;top:50%;transform:translateY(-50%);width:15px;height:15px;color:var(--text3);pointer-events:none}
#searchInput,#hrSearch{width:100%;padding:9px 12px 9px 36px;font-size:13px;font-family:var(--font);border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);color:var(--text);outline:none}
#searchInput:focus,#hrSearch:focus{border-color:var(--border2)}
select.filter{font-size:13px;font-family:var(--font);padding:8px 12px;border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);color:var(--text);cursor:pointer;outline:none}
.btn{display:inline-flex;align-items:center;gap:6px;font-size:13px;font-family:var(--font);font-weight:500;padding:8px 16px;border-radius:var(--radius);border:1px solid var(--border);background:var(--surface);color:var(--text);cursor:pointer;transition:background .15s;white-space:nowrap}
.btn:hover{background:var(--surface2)}
.btn:disabled{opacity:.5;cursor:not-allowed}
.btn-primary{background:var(--text);color:var(--bg);border-color:var(--text)}
.btn-primary:hover{opacity:.85;background:var(--text)}
.btn-icon{padding:5px;width:28px;height:28px;justify-content:center;font-size:14px}
.btn-xs{padding:4px 10px;font-size:11px}
.table-wrap{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px;min-width:1250px}
thead th{background:var(--surface2);padding:10px 12px;text-align:left;font-weight:500;font-size:11px;color:var(--text2);border-bottom:1px solid var(--border);white-space:nowrap;cursor:pointer;user-select:none}
thead th:hover{color:var(--text)}
tbody tr{border-bottom:1px solid var(--border);transition:background .1s}
tbody tr:last-child{border-bottom:none}
tbody tr:hover{background:#fafaf7}
td{padding:10px 12px;vertical-align:middle;white-space:nowrap}
.td-name{font-weight:500;font-size:13px}
.td-mono{font-family:var(--mono);font-size:11px;color:var(--text2)}
.badge{display:inline-flex;align-items:center;font-size:10.5px;font-weight:500;padding:2px 8px;border-radius:20px}
.badge-green{background:var(--accent-bg);color:var(--accent)}
.badge-amber{background:var(--amber-bg);color:var(--amber)}
.badge-red{background:var(--red-bg);color:var(--red)}
.badge-blue{background:var(--blue-bg);color:var(--blue)}
.badge-gray{background:var(--surface2);color:var(--text2);border:1px solid var(--border)}
.row-actions{display:flex;gap:4px}
.state-box{text-align:center;padding:4rem 2rem;color:var(--text2)}
.state-box p{font-size:14px}
.state-box .sub{font-size:12px;color:var(--text3);margin-top:6px}
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:200;align-items:center;justify-content:center;padding:1rem}
.overlay.open{display:flex}
.modal{background:var(--surface);border-radius:var(--radius-lg);border:1px solid var(--border);padding:1.75rem;width:100%;max-width:580px;max-height:92vh;overflow-y:auto}
.modal-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem}
.modal-header h2{font-size:16px;font-weight:600}
.section-sep{font-size:10px;font-weight:600;color:var(--text3);text-transform:uppercase;letter-spacing:.08em;margin:1.25rem 0 10px;padding-bottom:6px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.fg{display:flex;flex-direction:column;gap:4px}
.fg.full{grid-column:1/-1}
.fg label{font-size:11px;font-weight:500;color:var(--text2)}
.fg input{font-size:13px;font-family:var(--font);padding:8px 10px;border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);color:var(--text);outline:none}
.fg select{font-size:13px;font-family:var(--font);padding:8px 10px;border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);color:var(--text);outline:none}
.fg input:focus{border-color:var(--border2)}
.modal-actions{display:flex;gap:8px;margin-top:1.5rem;justify-content:flex-end}
.d-header{display:flex;align-items:center;gap:14px;margin-bottom:1.25rem;padding-bottom:1.25rem;border-bottom:1px solid var(--border)}
.avatar{width:52px;height:52px;border-radius:50%;background:var(--blue-bg);color:var(--blue);display:flex;align-items:center;justify-content:center;font-weight:600;font-size:16px;flex-shrink:0}
.d-name{font-size:17px;font-weight:600}
.d-sub{font-size:12px;color:var(--text2);margin-top:3px;font-family:var(--mono)}
.hl{border-radius:var(--radius);padding:14px 16px;margin-bottom:10px}
.hl-green{background:var(--accent-bg)}
.hl-amber{background:var(--amber-bg)}
.hl-red{background:var(--red-bg)}
.hl-purple{background:var(--purple-bg)}
.hl-label{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px}
.hl-green .hl-label{color:var(--accent)}
.hl-amber .hl-label{color:var(--amber)}
.hl-red .hl-label{color:var(--red)}
.hl-purple .hl-label{color:var(--purple)}
.hl-value{font-size:14px;font-weight:600}
.hl-green .hl-value{color:#0f4a30}
.hl-amber .hl-value{color:#5a3000}
.hl-red .hl-value{color:var(--red)}
.hl-purple .hl-value{color:var(--purple)}
.hl-sub{font-size:12px;margin-top:3px}
.hl-green .hl-sub{color:var(--accent)}
.hl-amber .hl-sub{color:var(--amber)}
.hl-red .hl-sub{color:var(--red)}
.hl-purple .hl-sub{color:var(--purple)}
.d-grid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;margin-bottom:10px}
.d-cell{background:var(--surface);padding:10px 12px}
.d-cell-lbl{font-size:10px;font-weight:500;color:var(--text3);text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px}
.d-cell-val{font-size:13px;font-weight:500;color:var(--text)}
.toast{position:fixed;bottom:2rem;right:2rem;background:var(--text);color:var(--bg);font-size:13px;padding:10px 18px;border-radius:var(--radius);z-index:999;opacity:0;transform:translateY(10px);transition:all .25s;pointer-events:none;max-width:340px}
.toast.show{opacity:1;transform:translateY(0)}
.toast.error{background:var(--red)}
.sync-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px;background:var(--accent)}
.history-list{display:flex;flex-direction:column;gap:6px;margin-bottom:10px}
.history-row{display:flex;align-items:center;justify-content:space-between;background:var(--surface2);border-radius:var(--radius);padding:8px 12px;font-size:12px}
.history-row .h-main{font-weight:500}
.history-row .h-sub{color:var(--text2);font-size:11px}
.history-empty{font-size:12px;color:var(--text3);padding:8px 0}
.salary-add-row{display:flex;gap:8px;align-items:flex-end;margin-top:8px}
.salary-add-row .fg{flex:1}

.tabs{display:flex;gap:4px;border-bottom:1px solid var(--border);margin-bottom:1.5rem;overflow-x:auto}
.tab{font:500 13px var(--font);padding:9px 16px;border:none;background:none;color:var(--text2);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;white-space:nowrap}
.tab:hover{color:var(--text)}
.tab.active{color:var(--text);border-bottom-color:var(--text)}
tfoot td{background:var(--surface2);font-weight:600;border-top:1px solid var(--border);font-size:12px}
.form-hint{font-size:11px;color:var(--text3);margin-top:8px;line-height:1.5}
.fg input[readonly]{background:var(--surface2);color:var(--text2)}
.calc-box{background:var(--surface2);border-radius:var(--radius);padding:12px 14px;margin-top:14px;font-size:12px;display:grid;grid-template-columns:1fr auto;gap:5px 16px}
.calc-box .c-strong{font-weight:600;font-size:13px}
.num{text-align:right;font-variant-numeric:tabular-nums}
@media(max-width:600px){.form-grid{grid-template-columns:1fr}.fg.full{grid-column:1}.app{padding:1rem}}
.report-section{margin-bottom:18px}
.report-section h3{font-size:13px;font-weight:600;color:var(--text);margin-bottom:8px;padding-bottom:6px;border-bottom:2px solid var(--border)}
.report-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:6px}
.report-field{font-size:12px}
.report-field .rf-lbl{color:var(--text3);font-size:10px;text-transform:uppercase;letter-spacing:.04em;margin-bottom:2px}
.report-field .rf-val{font-weight:500;color:var(--text)}
.report-table{width:100%;min-width:0;border-collapse:collapse;font-size:12px;margin-top:6px}
.report-table th{background:var(--surface2);padding:6px 10px;text-align:left;font-weight:500;font-size:11px;color:var(--text2);border-bottom:1px solid var(--border)}
.report-table td{padding:6px 10px;border-bottom:1px solid var(--border)}
.report-header{text-align:center;margin-bottom:20px;padding-bottom:14px;border-bottom:2px solid var(--text)}
.report-header h1{font-size:18px;font-weight:600}
.report-header p{font-size:12px;color:var(--text2);margin-top:4px}
@media print{
  body *{visibility:hidden}
  #reportPrintArea, #reportPrintArea *{visibility:visible}
  #reportPrintArea{position:absolute;left:0;top:0;width:100%;padding:20px}
  .overlay{position:static!important;background:none!important}
  .modal{box-shadow:none!important;border:none!important;max-width:100%!important;max-height:none!important}
  .modal-header{display:none!important}
}
</style>
</head>
<body>
<div class="app">
  <div class="header">
    <div class="header-left">
      <h1>&#128101; Employee Tracker</h1>
      <p><span class="sync-dot"></span>Data saved in cloud database</p>
    </div>
    <div class="header-right">
      <button class="btn" onclick="loadData();loadWareef()">&#8635; Refresh</button>
      <button class="btn btn-primary" id="addBtn" onclick="addForTab()">+ Add household worker</button>
    </div>
  </div>
  <div class="tabs">
    <button class="tab active" data-tab="employees" onclick="switchTab('employees')">&#127968; Household labor</button>
    <button class="tab" data-tab="hr" onclick="switchTab('hr')">&#127970; Wareef employees</button>
  </div>
  <div id="tab-employees">
  <div class="stats" id="statsRow"></div>
  <div class="toolbar">
    <div class="search-wrap">
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
      <input id="searchInput" placeholder="Search by name, ID, border number, phone…" oninput="renderTable()">
    </div>
    <select class="filter" id="filterVac" onchange="renderTable()">
      <option value="">All vacation</option>
      <option value="onvac">On vacation now</option>
      <option value="upcoming">Upcoming (30d)</option>
      <option value="none">Not scheduled</option>
    </select>
    <select class="filter" id="filterLoan" onchange="renderTable()">
      <option value="">All loans</option>
      <option value="has">Has active loan</option>
      <option value="none">No loan</option>
    </select>
    <select class="filter" id="filterId" onchange="renderTable()">
      <option value="">All ID status</option>
      <option value="expired">ID expired</option>
      <option value="soon">ID expiring soon (60d)</option>
      <option value="ok">ID valid</option>
    </select>
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th style="width:32px">#</th>
          <th onclick="sortBy('name')">Name &#8597;</th>
          <th onclick="sortBy('empId')">Emp ID &#8597;</th>
          <th onclick="sortBy('borderNo')">Border No. &#8597;</th>
          <th>Phone</th>
          <th onclick="sortBy('joiningDate')">Joining date &#8597;</th>
          <th>Employer</th>
          <th onclick="sortBy('idExpiry')">ID expiry &#8597;</th>
          <th>ID status</th>
          <th onclick="sortBy('currentSalary')">Salary &#8597;</th>
          <th onclick="sortBy('nextVacStart')">Next vacation &#8597;</th>
          <th>Vac. status</th>
          <th onclick="sortBy('loanRemaining')">Loan remaining &#8597;</th>
          <th>Loan status</th>
          <th style="width:84px"></th>
        </tr>
      </thead>
      <tbody id="tableBody"></tbody>
    </table>
  </div>
  </div>

  <div id="tab-hr" style="display:none">
    <div class="stats" id="hrStatsRow"></div>
    <div class="toolbar">
      <div class="search-wrap">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input id="hrSearch" placeholder="Search by name, ID, job title, Iqama, insurance, bank…" oninput="renderHR()">
      </div>
      <select class="filter" id="filterNat" onchange="renderHR()">
        <option value="">All nationalities</option>
        <option value="Saudi">Saudi</option>
        <option value="Non-Saudi">Non-Saudi</option>
      </select>
      <select class="filter" id="filterHrId" onchange="renderHR()">
        <option value="">All ID status</option>
        <option value="expired">ID expired</option>
        <option value="soon">ID expiring soon (60d)</option>
      </select>
      <select class="filter" id="filterIns" onchange="renderHR()">
        <option value="">All insurance</option>
        <option value="expired">Insurance expired</option>
        <option value="soon">Insurance expiring (60d)</option>
        <option value="none">No insurance</option>
      </select>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th style="width:32px">#</th>
            <th>Name / job title</th>
            <th>Iqama / ID</th>
            <th class="num">Basic</th>
            <th class="num">Allowances</th>
            <th class="num">Gross</th>
            <th class="num">GOSI (emp.)</th>
            <th class="num">Other ded.</th>
            <th class="num">Net pay</th>
            <th class="num">GOSI (employer)</th>
            <th>Medical insurance</th>
            <th class="num">Fees / year</th>
            <th class="num">Cost to company / mo</th>
            <th style="width:96px"></th>
          </tr>
        </thead>
        <tbody id="hrBody"></tbody>
        <tfoot id="hrFoot"></tfoot>
      </table>
    </div>
    <p class="form-hint">Wareef employees are a separate list from household labor. Other ded. = loan/advance + other deductions. Cost to company = gross + GOSI employer share + yearly fees &divide; 12.</p>
  </div>
</div>

<div class="overlay" id="hrModal">
  <div class="modal">
    <div class="modal-header">
      <h2 id="hrModalTitle">Add Wareef employee</h2>
      <button class="btn btn-icon" onclick="closeHR()">&#10005;</button>
    </div>
    <div class="section-sep">Personal &amp; job</div>
    <div class="form-grid">
      <div class="fg full"><label>Full name *</label><input id="h_name" placeholder="e.g. Khalid Al-Otaibi"></div>
      <div class="fg"><label>Employee ID *</label><input id="h_empId" placeholder="e.g. WR-001"></div>
      <div class="fg"><label>Nationality</label><select id="h_nationality" onchange="natChanged()"><option value="Non-Saudi">Non-Saudi</option><option value="Saudi">Saudi</option></select></div>
      <div class="fg"><label>Job title</label><input id="h_jobTitle" placeholder="e.g. Accountant"></div>
      <div class="fg"><label>Department</label><input id="h_department" placeholder="e.g. Finance"></div>
      <div class="fg"><label>Phone number</label><input id="h_phone" placeholder="e.g. +966501234567"></div>
      <div class="fg"><label>Iqama / national ID number</label><input id="h_idNumber"></div>
      <div class="fg"><label>ID expiry date</label><input type="date" id="h_idExpiry"></div>
      <div class="fg"><label>Joining date</label><input type="date" id="h_joiningDate"></div>
    </div>

    <div class="section-sep">Salary &amp; allowances (monthly, SAR)</div>
    <div class="form-grid">
      <div class="fg"><label>Basic salary</label><input type="number" id="h_basic" min="0" placeholder="0"></div>
      <div class="fg"><label>Housing allowance</label><input type="number" id="h_housing" min="0" placeholder="0"></div>
      <div class="fg"><label>Transport allowance</label><input type="number" id="h_transport" min="0" placeholder="0"></div>
      <div class="fg"><label>Other allowances</label><input type="number" id="h_otherAllow" min="0" placeholder="0"></div>
    </div>

    <div class="section-sep">GOSI (social insurance)</div>
    <div class="form-grid">
      <div class="fg"><label>Employee share %</label><input type="number" id="h_gosiEmpPct" min="0" step="0.01" placeholder="0"></div>
      <div class="fg"><label>Employer share %</label><input type="number" id="h_gosiErPct" min="0" step="0.01" placeholder="0"></div>
    </div>
    <p class="form-hint">Calculated on basic + housing (max SAR 45,000). Picking a nationality fills common rates (non-Saudi 0% / 2%, Saudi 9.75% / 11.75%). Check current GOSI rates.</p>

    <div class="section-sep">Monthly deductions</div>
    <div class="form-grid">
      <div class="fg"><label>Loan / advance (SAR / month)</label><input type="number" id="h_loanDed" min="0" placeholder="0"></div>
      <div class="fg"><label>Other deductions (SAR / month)</label><input type="number" id="h_otherDed" min="0" placeholder="0"></div>
      <div class="fg full"><label>Deduction note</label><input id="h_otherDedNote" placeholder="e.g. absence, advance"></div>
    </div>

    <div class="section-sep">Medical insurance</div>
    <div class="form-grid">
      <div class="fg"><label>Provider</label><input id="h_insProvider" placeholder="e.g. Bupa, Tawuniya"></div>
      <div class="fg"><label>Class</label><input id="h_insClass" placeholder="e.g. A, B, C"></div>
      <div class="fg"><label>Policy / card number</label><input id="h_insPolicy"></div>
      <div class="fg"><label>Expiry date</label><input type="date" id="h_insExpiry"></div>
      <div class="fg full"><label>Annual premium (SAR)</label><input type="number" id="h_medicalIns" min="0" placeholder="0"></div>
    </div>

    <div class="section-sep">Government fees (per year, SAR)</div>
    <div class="form-grid">
      <div class="fg"><label>Iqama renewal fee</label><input type="number" id="h_iqamaFee" min="0" placeholder="0"></div>
      <div class="fg"><label>Work permit fee</label><input type="number" id="h_workPermitFee" min="0" placeholder="0"></div>
      <div class="fg full"><label>Other yearly fees</label><input type="number" id="h_otherFees" min="0" placeholder="0"></div>
    </div>

    <div class="section-sep">Bank</div>
    <div class="form-grid">
      <div class="fg"><label>Bank name</label><input id="h_bankName" placeholder="e.g. Al Rajhi"></div>
      <div class="fg"><label>IBAN</label><input id="h_iban" placeholder="SA…"></div>
    </div>

    <div class="calc-box" id="hrCalcBox"></div>

    <div class="modal-actions">
      <button class="btn" onclick="closeHR()">Cancel</button>
      <button class="btn btn-primary" id="hrSaveBtn" onclick="saveHR()">Save employee</button>
    </div>
  </div>
</div>

<div class="overlay" id="formModal">
  <div class="modal">
    <div class="modal-header">
      <h2 id="formModalTitle">Add employee</h2>
      <button class="btn btn-icon" onclick="closeModal()">&#10005;</button>
    </div>
    <div class="section-sep">Personal &amp; identity</div>
    <div class="form-grid">
      <div class="fg full"><label>Full name *</label><input id="f_name" placeholder="e.g. Ahmad Al-Rashidi"></div>
      <div class="fg"><label>Employee ID *</label><input id="f_empId" placeholder="e.g. EMP-001"></div>
      <div class="fg"><label>Phone number</label><input id="f_phone" placeholder="e.g. +966501234567"></div>
      <div class="fg"><label>Border number</label><input id="f_borderNo" placeholder="e.g. 2300000001"></div>
      <div class="fg"><label>ID expiry date</label><input type="date" id="f_idExpiry"></div>
      <div class="fg"><label>Joining date</label><input type="date" id="f_joiningDate"></div>
      <div class="fg"><label>Employer name</label><input id="f_employerName" placeholder="e.g. Al-Rashidi Trading Co."></div>
      <div class="fg"><label>Employer ID</label><input id="f_employerId" placeholder="e.g. CR-1234567890"></div>
    </div>

    <div class="section-sep">Vacation</div>
    <div class="form-grid">
      <div class="fg"><label>Last vacation start</label><input type="date" id="f_lv_start"></div>
      <div class="fg"><label>Last vacation end</label><input type="date" id="f_lv_end"></div>
      <div class="fg"><label>Next vacation start</label><input type="date" id="f_nv_start"></div>
      <div class="fg"><label>Next vacation end</label><input type="date" id="f_nv_end"></div>
    </div>
    <div id="vacHistorySection" style="display:none">
      <div class="section-sep" style="margin-top:14px">Vacation history</div>
      <div class="history-list" id="vacHistoryList"></div>
    </div>

    <div class="section-sep">Loan</div>
    <div class="form-grid">
      <div class="fg"><label>Loan amount (SAR)</label><input type="number" id="f_loan" placeholder="0 = no loan" min="0"></div>
      <div class="fg"><label>Loan remaining (SAR)</label><input type="number" id="f_loan_rem" placeholder="0" min="0"></div>
      <div class="fg full"><label>Monthly payment (SAR)</label><input type="number" id="f_loan_pay" placeholder="0" min="0"></div>
    </div>

    <div class="section-sep">Salary</div>
    <div class="form-grid">
      <div class="fg full"><label>Current salary (SAR)</label><input type="number" id="f_salary" placeholder="0" min="0"></div>
    </div>
    <div id="salaryHistorySection" style="display:none">
      <div class="history-list" id="salaryHistoryList"></div>
    </div>
    <div class="salary-add-row">
      <div class="fg"><label>Add salary change date</label><input type="date" id="f_salaryChangeDate"></div>
      <div class="fg"><label>New amount (SAR)</label><input type="number" id="f_salaryChangeAmount" placeholder="0" min="0"></div>
      <button class="btn btn-xs" onclick="addSalaryHistoryEntry()">+ Add</button>
    </div>

    <div class="modal-actions">
      <button class="btn" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" id="saveBtn" onclick="saveEmployee()">Save employee</button>
    </div>
  </div>
</div>

<div class="overlay" id="detailModal">
  <div class="modal" style="max-width:520px">
    <div class="modal-header">
      <h2>Employee details</h2>
      <button class="btn btn-icon" onclick="closeDetail()">&#10005;</button>
    </div>
    <div id="detailContent"></div>
    <div class="modal-actions">
      <button class="btn" onclick="closeDetail()">Close</button>
      <button class="btn btn-primary" onclick="openReportFromDetail()">&#128203; Full report</button>
    </div>
  </div>
</div>

<div class="overlay" id="reportModal">
  <div class="modal" style="max-width:640px">
    <div class="modal-header" style="display:flex;justify-content:space-between;align-items:center">
      <h2>Employee Report</h2>
      <div style="display:flex;gap:8px">
        <button class="btn btn-primary" onclick="printReport()">&#128424; Download / Print PDF</button>
        <button class="btn btn-icon" onclick="closeReport()">&#10005;</button>
      </div>
    </div>
    <div id="reportContent"></div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const TODAY=new Date();TODAY.setHours(0,0,0,0);
let employees=[],sortField='name',sortDir=1,editIdx=null;
let currentVacHistory=[],currentSalaryHistory=[];

function dFmt(d){if(!d)return'—';const p=d.split('-');return`${p[2]}/${p[1]}/${p[0]}`}
function daysDiff(d){if(!d)return null;const dt=new Date(d);dt.setHours(0,0,0,0);return Math.round((dt-TODAY)/86400000)}
function yearsFrom(d){if(!d)return null;return((TODAY-new Date(d))/31557600000).toFixed(1)}
function initials(n){return n.split(' ').map(w=>w[0]||'').join('').toUpperCase().slice(0,2)}
function fmtSAR(n){return'SAR '+Number(n).toLocaleString()}

function idStatus(e){
  const ds=daysDiff(e.idExpiry);
  if(!e.idExpiry)return{label:'No date',cls:'badge-gray'};
  if(ds<0)return{label:'Expired',cls:'badge-red'};
  if(ds<=60)return{label:`${ds}d left`,cls:'badge-amber'};
  return{label:'Valid',cls:'badge-green'};
}
function vacStatus(e){
  const ds=daysDiff(e.nextVacStart),de=daysDiff(e.nextVacEnd);
  if(!e.nextVacStart)return{label:'Not scheduled',cls:'badge-gray'};
  if(ds<=0&&de>=0)return{label:'On vacation',cls:'badge-blue'};
  if(ds>0&&ds<=30)return{label:`In ${ds}d`,cls:'badge-amber'};
  if(ds>0)return{label:`In ${ds}d`,cls:'badge-green'};
  return{label:'Past',cls:'badge-gray'};
}
function loanStatus(e){
  if(!e.loanAmount||e.loanAmount<=0)return{label:'No loan',cls:'badge-gray'};
  if(!e.loanRemaining||e.loanRemaining<=0)return{label:'Paid off',cls:'badge-green'};
  const pct=Math.round((e.loanRemaining/e.loanAmount)*100);
  if(pct>60)return{label:`${pct}% left`,cls:'badge-red'};
  if(pct>20)return{label:`${pct}% left`,cls:'badge-amber'};
  return{label:`${pct}% left`,cls:'badge-green'};
}
function showToast(msg,isErr=false){const t=document.getElementById('toast');t.textContent=msg;t.className='toast'+(isErr?' error':'');void t.offsetWidth;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3500)}

async function loadData(){
  try{const res=await fetch('/api/employees');employees=await res.json();renderTable();}
  catch(e){showToast('Could not load data',true)}
}

function sortBy(f){sortField===f?sortDir*=-1:(sortField=f,sortDir=1);renderTable()}

function renderTable(){
  const q=document.getElementById('searchInput').value.toLowerCase();
  const fv=document.getElementById('filterVac').value;
  const fl=document.getElementById('filterLoan').value;
  const fi=document.getElementById('filterId').value;
  let rows=[...employees];
  if(q)rows=rows.filter(e=>[e.name,e.empId,e.borderNo,e.employerName,e.phone].join(' ').toLowerCase().includes(q));
  if(fv==='onvac')rows=rows.filter(e=>{const ds=daysDiff(e.nextVacStart),de=daysDiff(e.nextVacEnd);return ds<=0&&de>=0});
  if(fv==='upcoming')rows=rows.filter(e=>{const ds=daysDiff(e.nextVacStart);return ds>0&&ds<=30});
  if(fv==='none')rows=rows.filter(e=>!e.nextVacStart);
  if(fl==='has')rows=rows.filter(e=>e.loanAmount>0&&e.loanRemaining>0);
  if(fl==='none')rows=rows.filter(e=>!e.loanAmount||e.loanAmount<=0);
  if(fi==='expired')rows=rows.filter(e=>e.idExpiry&&daysDiff(e.idExpiry)<0);
  if(fi==='soon')rows=rows.filter(e=>{const ds=daysDiff(e.idExpiry);return ds>=0&&ds<=60});
  if(fi==='ok')rows=rows.filter(e=>e.idExpiry&&daysDiff(e.idExpiry)>60);
  rows.sort((a,b)=>{let av=a[sortField]||'',bv=b[sortField]||'';if(['loanAmount','loanRemaining','loanMonthly','currentSalary'].includes(sortField)){av=Number(av);bv=Number(bv)}return av>bv?sortDir:av<bv?-sortDir:0});
  const tbody=document.getElementById('tableBody');
  if(!rows.length){tbody.innerHTML=`<tr><td colspan="15"><div class="state-box"><p>&#128100; No employees found</p><p class="sub">Add your first employee using the button above</p></div></td></tr>`;renderStats();return}
  tbody.innerHTML=rows.map((e,i)=>{
    const vs=vacStatus(e),ls=loanStatus(e),is=idStatus(e),oi=employees.indexOf(e),yr=yearsFrom(e.joiningDate);
    return`<tr>
      <td style="color:var(--text3);font-size:11px">${i+1}</td>
      <td class="td-name">${e.name}</td>
      <td class="td-mono">${e.empId||'—'}</td>
      <td class="td-mono">${e.borderNo||'—'}</td>
      <td style="font-size:12px">${e.phone||'—'}</td>
      <td><span style="font-size:12px">${dFmt(e.joiningDate)}</span>${yr?`<span style="font-size:10px;color:var(--text3);margin-left:5px">${yr}y</span>`:''}</td>
      <td><div style="font-size:12px;font-weight:500">${e.employerName||'—'}</div><div class="td-mono" style="font-size:10px;margin-top:1px">${e.employerId||''}</div></td>
      <td style="font-size:12px">${dFmt(e.idExpiry)}</td>
      <td><span class="badge ${is.cls}">${is.label}</span></td>
      <td style="font-size:12px;font-weight:500">${e.currentSalary?fmtSAR(e.currentSalary):'—'}</td>
      <td style="font-size:11px">${e.nextVacStart?dFmt(e.nextVacStart)+(e.nextVacEnd?' – '+dFmt(e.nextVacEnd):''):'—'}</td>
      <td><span class="badge ${vs.cls}">${vs.label}</span></td>
      <td style="font-size:12px">${e.loanRemaining>0?fmtSAR(e.loanRemaining):'—'}</td>
      <td><span class="badge ${ls.cls}">${ls.label}</span></td>
      <td><div class="row-actions">
        <button class="btn btn-icon" onclick="openDetail(${oi})">&#128065;</button>
        <button class="btn btn-icon" onclick="openReport(${oi})" title="Full report">&#128203;</button>
        <button class="btn btn-icon" onclick="openEdit(${oi})">&#9998;</button>
        <button class="btn btn-icon" onclick="deleteEmp(${oi})" style="color:var(--red)">&#128465;</button>
      </div></td>
    </tr>`;
  }).join('');
  renderStats();
}

function renderStats(){
  const onVac=employees.filter(e=>{const ds=daysDiff(e.nextVacStart),de=daysDiff(e.nextVacEnd);return ds<=0&&de>=0}).length;
  const upcoming=employees.filter(e=>{const ds=daysDiff(e.nextVacStart);return ds>0&&ds<=30}).length;
  const withLoan=employees.filter(e=>e.loanAmount>0&&e.loanRemaining>0).length;
  const totalLoan=employees.reduce((s,e)=>s+(Number(e.loanRemaining)||0),0);
  const totalSalary=employees.reduce((s,e)=>s+(Number(e.currentSalary)||0),0);
  const expiredId=employees.filter(e=>e.idExpiry&&daysDiff(e.idExpiry)<0).length;
  const expiringId=employees.filter(e=>{const ds=daysDiff(e.idExpiry);return ds>=0&&ds<=60}).length;
  document.getElementById('statsRow').innerHTML=`
    <div class="stat-card"><div class="lbl">Employees</div><div class="val">${employees.length}</div></div>
    <div class="stat-card"><div class="lbl">On vacation</div><div class="val">${onVac}</div></div>
    <div class="stat-card"><div class="lbl">Vacation in 30d</div><div class="val">${upcoming}</div></div>
    <div class="stat-card"><div class="lbl">Active loans</div><div class="val">${withLoan}</div></div>
    <div class="stat-card"><div class="lbl">Total loan left</div><div class="val sm">SAR ${totalLoan.toLocaleString()}</div></div>
    <div class="stat-card"><div class="lbl">Total monthly payroll</div><div class="val sm">SAR ${totalSalary.toLocaleString()}</div></div>
    <div class="stat-card" style="${expiredId>0?'border-color:var(--red);background:var(--red-bg)':''}"><div class="lbl">ID expired</div><div class="val" style="${expiredId>0?'color:var(--red)':''}">${expiredId}</div></div>
    <div class="stat-card" style="${expiringId>0?'border-color:var(--amber);background:var(--amber-bg)':''}"><div class="lbl">ID expiring 60d</div><div class="val" style="${expiringId>0?'color:var(--amber)':''}">${expiringId}</div></div>
  `;
}

function openAdd(){
  editIdx=null;clearForm();
  currentVacHistory=[];currentSalaryHistory=[];
  document.getElementById('vacHistorySection').style.display='none';
  document.getElementById('salaryHistorySection').style.display='none';
  document.getElementById('formModalTitle').textContent='Add employee';
  document.getElementById('saveBtn').textContent='Save employee';
  document.getElementById('formModal').classList.add('open');
}
function openEdit(i){
  editIdx=i;
  const e=employees[i];
  fillForm(e);
  currentVacHistory=Array.isArray(e.vacHistory)?[...e.vacHistory]:[];
  currentSalaryHistory=Array.isArray(e.salaryHistory)?[...e.salaryHistory]:[];
  renderVacHistory();
  renderSalaryHistory();
  document.getElementById('formModalTitle').textContent='Edit employee';
  document.getElementById('saveBtn').textContent='Update employee';
  document.getElementById('formModal').classList.add('open');
}
function closeModal(){document.getElementById('formModal').classList.remove('open')}
function clearForm(){['f_name','f_empId','f_phone','f_borderNo','f_idExpiry','f_joiningDate','f_employerName','f_employerId','f_lv_start','f_lv_end','f_nv_start','f_nv_end','f_loan','f_loan_rem','f_loan_pay','f_salary','f_salaryChangeDate','f_salaryChangeAmount'].forEach(id=>document.getElementById(id).value='')}
function fillForm(e){
  document.getElementById('f_name').value=e.name||'';
  document.getElementById('f_empId').value=e.empId||'';
  document.getElementById('f_phone').value=e.phone||'';
  document.getElementById('f_borderNo').value=e.borderNo||'';
  document.getElementById('f_idExpiry').value=e.idExpiry||'';
  document.getElementById('f_joiningDate').value=e.joiningDate||'';
  document.getElementById('f_employerName').value=e.employerName||'';
  document.getElementById('f_employerId').value=e.employerId||'';
  document.getElementById('f_lv_start').value=e.lastVacStart||'';
  document.getElementById('f_lv_end').value=e.lastVacEnd||'';
  document.getElementById('f_nv_start').value=e.nextVacStart||'';
  document.getElementById('f_nv_end').value=e.nextVacEnd||'';
  document.getElementById('f_loan').value=e.loanAmount||'';
  document.getElementById('f_loan_rem').value=e.loanRemaining||'';
  document.getElementById('f_loan_pay').value=e.loanMonthly||'';
  document.getElementById('f_salary').value=e.currentSalary||'';
}

function renderVacHistory(){
  const sec=document.getElementById('vacHistorySection');
  const list=document.getElementById('vacHistoryList');
  if(!currentVacHistory.length){sec.style.display='none';return}
  sec.style.display='block';
  list.innerHTML=currentVacHistory.slice().reverse().map((v,ri)=>{
    const i=currentVacHistory.length-1-ri;
    return`<div class="history-row"><div><div class="h-main">${dFmt(v.start)} – ${dFmt(v.end)}</div></div><button class="btn btn-icon btn-xs" onclick="removeVacHistory(${i})">&#10005;</button></div>`;
  }).join('');
}
function removeVacHistory(i){currentVacHistory.splice(i,1);renderVacHistory()}

function renderSalaryHistory(){
  const sec=document.getElementById('salaryHistorySection');
  const list=document.getElementById('salaryHistoryList');
  if(!currentSalaryHistory.length){sec.style.display='none';return}
  sec.style.display='block';
  const sorted=currentSalaryHistory.map((s,i)=>({...s,_i:i})).sort((a,b)=>new Date(b.date)-new Date(a.date));
  list.innerHTML=sorted.map(s=>`<div class="history-row"><div><div class="h-main">${fmtSAR(s.amount)}</div><div class="h-sub">${dFmt(s.date)}</div></div><button class="btn btn-icon btn-xs" onclick="removeSalaryHistory(${s._i})">&#10005;</button></div>`).join('');
}
function addSalaryHistoryEntry(){
  const date=document.getElementById('f_salaryChangeDate').value;
  const amount=Number(document.getElementById('f_salaryChangeAmount').value);
  if(!date||!amount){showToast('Enter both date and amount for salary history',true);return}
  currentSalaryHistory.push({date,amount});
  document.getElementById('f_salaryChangeDate').value='';
  document.getElementById('f_salaryChangeAmount').value='';
  renderSalaryHistory();
}
function removeSalaryHistory(i){currentSalaryHistory.splice(i,1);renderSalaryHistory()}

async function saveEmployee(){
  const newLvStart=document.getElementById('f_lv_start').value;
  const newLvEnd=document.getElementById('f_lv_end').value;

  if(editIdx!==null){
    const old=employees[editIdx];
    if(old.lastVacStart && (old.lastVacStart!==newLvStart || old.lastVacEnd!==newLvEnd)){
      const alreadyIn=currentVacHistory.some(v=>v.start===old.lastVacStart&&v.end===old.lastVacEnd);
      if(!alreadyIn)currentVacHistory.push({start:old.lastVacStart,end:old.lastVacEnd});
    }
  }

  const newSalary=Number(document.getElementById('f_salary').value)||0;
  if(editIdx!==null){
    const old=employees[editIdx];
    if(old.currentSalary && old.currentSalary!==newSalary){
      const alreadyIn=currentSalaryHistory.some(s=>s.amount===old.currentSalary && s.date===(old._lastSalaryDate||old.joiningDate));
      if(!alreadyIn)currentSalaryHistory.push({date:old._lastSalaryDate||old.joiningDate||'',amount:old.currentSalary});
    }
  }

  const emp={
    name:document.getElementById('f_name').value.trim(),
    empId:document.getElementById('f_empId').value.trim(),
    phone:document.getElementById('f_phone').value.trim(),
    borderNo:document.getElementById('f_borderNo').value.trim(),
    idExpiry:document.getElementById('f_idExpiry').value,
    joiningDate:document.getElementById('f_joiningDate').value,
    employerName:document.getElementById('f_employerName').value.trim(),
    employerId:document.getElementById('f_employerId').value.trim(),
    lastVacStart:newLvStart,
    lastVacEnd:newLvEnd,
    nextVacStart:document.getElementById('f_nv_start').value,
    nextVacEnd:document.getElementById('f_nv_end').value,
    loanAmount:Number(document.getElementById('f_loan').value)||0,
    loanRemaining:Number(document.getElementById('f_loan_rem').value)||0,
    loanMonthly:Number(document.getElementById('f_loan_pay').value)||0,
    currentSalary:newSalary,
    vacHistory:currentVacHistory,
    salaryHistory:currentSalaryHistory,
    _lastSalaryDate: new Date().toISOString().split('T')[0],
  };
  if(!emp.name||!emp.empId){showToast('Name and Employee ID are required.',true);return}
  const btn=document.getElementById('saveBtn');btn.textContent='Saving…';btn.disabled=true;
  try{
    if(editIdx!==null){await fetch(`/api/employees/${employees[editIdx]._id}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(emp)});showToast('Employee updated ✓');}
    else{await fetch('/api/employees',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(emp)});showToast('Employee added ✓');}
    closeModal();await loadData();
  }catch(e){showToast('Save failed',true)}
  finally{btn.textContent=editIdx!==null?'Update employee':'Save employee';btn.disabled=false}
}

async function deleteEmp(i){
  if(!confirm(`Delete ${employees[i].name}?`))return;
  try{await fetch(`/api/employees/${employees[i]._id}`,{method:'DELETE'});showToast('Employee deleted');await loadData();}
  catch(e){showToast('Delete failed',true)}
}

function openDetail(i){
  reportEmpIdx=i;
  const e=employees[i],vs=vacStatus(e),ls=loanStatus(e),is=idStatus(e);
  const lv=e.lastVacStart?(dFmt(e.lastVacStart)+(e.lastVacEnd?' – '+dFmt(e.lastVacEnd):'')):'Not recorded';
  const nv=e.nextVacStart?(dFmt(e.nextVacStart)+(e.nextVacEnd?' – '+dFmt(e.nextVacEnd):'')):'Not scheduled';
  const nd=e.nextVacStart&&daysDiff(e.nextVacStart)>0?`In ${daysDiff(e.nextVacStart)} days`:(e.nextVacStart?vs.label:'');
  const loanPaid=e.loanAmount>0?e.loanAmount-e.loanRemaining:0;
  const monthsLeft=e.loanMonthly>0&&e.loanRemaining>0?Math.ceil(e.loanRemaining/e.loanMonthly):null;
  const tenure=yearsFrom(e.joiningDate);
  const idDs=daysDiff(e.idExpiry);
  const idHlClass=!e.idExpiry?'hl-green':idDs<0?'hl-red':idDs<=60?'hl-amber':'hl-green';
  const idHlText=!e.idExpiry?'No expiry date set':idDs<0?`Expired ${Math.abs(idDs)} days ago`:idDs<=60?`Expiring in ${idDs} days`:`Valid — expires ${dFmt(e.idExpiry)}`;

  const vacHistory=Array.isArray(e.vacHistory)?e.vacHistory:[];
  const vacHistoryHtml=vacHistory.length
    ?vacHistory.slice().reverse().map(v=>`<div class="history-row"><div class="h-main">${dFmt(v.start)} – ${dFmt(v.end)}</div></div>`).join('')
    :'<div class="history-empty">No past vacation history recorded yet.</div>';

  const salaryHistory=Array.isArray(e.salaryHistory)?e.salaryHistory:[];
  const salaryHistorySorted=salaryHistory.slice().sort((a,b)=>new Date(b.date)-new Date(a.date));
  const salaryHistoryHtml=salaryHistorySorted.length
    ?salaryHistorySorted.map(s=>`<div class="history-row"><div class="h-main">${fmtSAR(s.amount)}</div><div class="h-sub">${dFmt(s.date)}</div></div>`).join('')
    :'<div class="history-empty">No salary change history recorded yet.</div>';

  document.getElementById('detailContent').innerHTML=`
    <div class="d-header">
      <div class="avatar">${initials(e.name)}</div>
      <div><div class="d-name">${e.name}</div><div class="d-sub">${e.empId||''}${e.borderNo?' · Border: '+e.borderNo:''}</div></div>
    </div>
    <div class="d-grid">
      <div class="d-cell"><div class="d-cell-lbl">Phone</div><div class="d-cell-val">${e.phone||'—'}</div></div>
      <div class="d-cell"><div class="d-cell-lbl">Border number</div><div class="d-cell-val" style="font-family:var(--mono);font-size:12px">${e.borderNo||'—'}</div></div>
      <div class="d-cell"><div class="d-cell-lbl">Joining date</div><div class="d-cell-val">${dFmt(e.joiningDate)}${tenure?' ('+tenure+'y)':''}</div></div>
      <div class="d-cell"><div class="d-cell-lbl">Employer</div><div class="d-cell-val">${e.employerName||'—'}</div></div>
      <div class="d-cell"><div class="d-cell-lbl">Employer ID</div><div class="d-cell-val" style="font-family:var(--mono);font-size:12px">${e.employerId||'—'}</div></div>
      <div class="d-cell"><div class="d-cell-lbl">ID status</div><div class="d-cell-val"><span class="badge ${is.cls}">${is.label}</span></div></div>
    </div>

    <div class="hl ${idHlClass}">
      <div class="hl-label">&#128196; ID / Iqama expiry</div>
      <div class="hl-value">${dFmt(e.idExpiry)}</div>
      <div class="hl-sub">${idHlText}</div>
    </div>

    <div class="hl hl-purple">
      <div class="hl-label">&#128176; Current salary</div>
      <div class="hl-value">${e.currentSalary?fmtSAR(e.currentSalary):'Not set'}</div>
    </div>
    <div class="section-sep" style="margin-top:14px">Salary history</div>
    <div class="history-list">${salaryHistoryHtml}</div>

    <div class="hl hl-green">
      <div class="hl-label">&#127958; Vacation</div>
      <div class="hl-value">${nv}</div>
      <div class="hl-sub">${nd?nd+' · ':''} Last: ${lv}</div>
    </div>
    <div class="section-sep" style="margin-top:14px">Vacation history</div>
    <div class="history-list">${vacHistoryHtml}</div>

    ${e.loanAmount>0?`<div class="hl hl-amber">
      <div class="hl-label">&#128181; Loan</div>
      <div class="hl-value">${fmtSAR(e.loanRemaining||0)} remaining</div>
      <div class="hl-sub">Total: ${fmtSAR(e.loanAmount)} · Paid: ${fmtSAR(loanPaid)}${monthsLeft?' · ~'+monthsLeft+' months left':''}</div>
    </div>`:''}
    <div class="d-grid" style="margin-top:0">
      <div class="d-cell"><div class="d-cell-lbl">Vacation status</div><div class="d-cell-val"><span class="badge ${vs.cls}">${vs.label}</span></div></div>
      <div class="d-cell"><div class="d-cell-lbl">Loan status</div><div class="d-cell-val"><span class="badge ${ls.cls}">${ls.label}</span></div></div>
      ${e.loanMonthly>0?`<div class="d-cell"><div class="d-cell-lbl">Monthly payment</div><div class="d-cell-val">${fmtSAR(e.loanMonthly)}</div></div>`:'<div class="d-cell"></div>'}
      ${monthsLeft?`<div class="d-cell"><div class="d-cell-lbl">Months to payoff</div><div class="d-cell-val">${monthsLeft} months</div></div>`:'<div class="d-cell"></div>'}
    </div>
  `;
  document.getElementById('detailModal').classList.add('open');
}
let reportEmpIdx=null;

function openReport(i){
  reportEmpIdx=i;
  renderReport(employees[i]);
  document.getElementById('reportModal').classList.add('open');
}
function openReportFromDetail(){
  if(reportEmpIdx===null && employees.length){
    // fallback: find currently open detail employee via name match isn't reliable, so this is triggered only via openDetail flow
  }
  closeDetail();
  if(reportEmpIdx!==null){
    renderReport(employees[reportEmpIdx]);
    document.getElementById('reportModal').classList.add('open');
  }
}
function closeReport(){document.getElementById('reportModal').classList.remove('open')}
function printReport(){window.print()}

function renderReport(e){
  const vs=vacStatus(e),ls=loanStatus(e),is=idStatus(e);
  const tenure=yearsFrom(e.joiningDate);
  const loanPaid=e.loanAmount>0?e.loanAmount-e.loanRemaining:0;
  const monthsLeft=e.loanMonthly>0&&e.loanRemaining>0?Math.ceil(e.loanRemaining/e.loanMonthly):null;

  const vacHistory=Array.isArray(e.vacHistory)?e.vacHistory:[];
  const allVacations=[...vacHistory];
  if(e.lastVacStart)allVacations.push({start:e.lastVacStart,end:e.lastVacEnd,current:true});
  const vacSorted=allVacations.slice().sort((a,b)=>new Date(b.start)-new Date(a.start));
  const vacRows=vacSorted.length
    ?vacSorted.map(v=>{
        const days=v.start&&v.end?Math.round((new Date(v.end)-new Date(v.start))/86400000)+1:'—';
        return`<tr><td>${dFmt(v.start)}</td><td>${dFmt(v.end)}</td><td>${days}</td><td>${v.current?'Most recent':'Past'}</td></tr>`;
      }).join('')
    :'<tr><td colspan="4" style="text-align:center;color:var(--text3)">No vacation records</td></tr>';

  const salaryHistory=Array.isArray(e.salaryHistory)?e.salaryHistory:[];
  const allSalaries=[...salaryHistory];
  if(e.currentSalary)allSalaries.push({date:e._lastSalaryDate||'Current',amount:e.currentSalary,current:true});
  const salarySorted=allSalaries.slice().sort((a,b)=>new Date(b.date)-new Date(a.date));
  let salaryRows='';
  if(salarySorted.length){
    salaryRows=salarySorted.map((s,idx)=>{
      const prev=salarySorted[idx+1];
      const change=prev?(s.amount-prev.amount):null;
      const changeStr=change===null?'—':(change>0?`+${fmtSAR(change)}`:(change<0?`-${fmtSAR(Math.abs(change))}`:'No change'));
      const changeColor=change>0?'color:var(--accent)':change<0?'color:var(--red)':'color:var(--text3)';
      return`<tr><td>${dFmt(s.date)}</td><td>${fmtSAR(s.amount)}</td><td style="${changeColor}">${changeStr}</td><td>${s.current?'Current':'Past'}</td></tr>`;
    }).join('');
  }else{
    salaryRows='<tr><td colspan="4" style="text-align:center;color:var(--text3)">No salary records</td></tr>';
  }

  const idDs=daysDiff(e.idExpiry);
  const idText=!e.idExpiry?'No expiry date set':idDs<0?`Expired ${Math.abs(idDs)} days ago`:idDs<=60?`Expiring in ${idDs} days`:`Valid`;

  document.getElementById('reportContent').innerHTML=`
    <div id="reportPrintArea">
      <div class="report-header">
        <h1>Employee Report — ${e.name}</h1>
        <p>Generated on ${new Date().toLocaleDateString()} &middot; Employee ID: ${e.empId||'—'}</p>
      </div>

      <div class="report-section">
        <h3>Personal &amp; Identity</h3>
        <div class="report-grid">
          <div class="report-field"><div class="rf-lbl">Full name</div><div class="rf-val">${e.name}</div></div>
          <div class="report-field"><div class="rf-lbl">Employee ID</div><div class="rf-val">${e.empId||'—'}</div></div>
          <div class="report-field"><div class="rf-lbl">Phone</div><div class="rf-val">${e.phone||'—'}</div></div>
          <div class="report-field"><div class="rf-lbl">Border number</div><div class="rf-val">${e.borderNo||'—'}</div></div>
          <div class="report-field"><div class="rf-lbl">ID / Iqama expiry</div><div class="rf-val">${dFmt(e.idExpiry)} (${idText})</div></div>
          <div class="report-field"><div class="rf-lbl">Joining date</div><div class="rf-val">${dFmt(e.joiningDate)}${tenure?' — '+tenure+' years tenure':''}</div></div>
          <div class="report-field"><div class="rf-lbl">Employer</div><div class="rf-val">${e.employerName||'—'}</div></div>
          <div class="report-field"><div class="rf-lbl">Employer ID</div><div class="rf-val">${e.employerId||'—'}</div></div>
        </div>
      </div>

      <div class="report-section">
        <h3>Salary History (Full Record)</h3>
        <table class="report-table">
          <thead><tr><th>Date</th><th>Amount</th><th>Change</th><th>Status</th></tr></thead>
          <tbody>${salaryRows}</tbody>
        </table>
      </div>

      <div class="report-section">
        <h3>Vacation History (Full Record)</h3>
        <table class="report-table">
          <thead><tr><th>Start</th><th>End</th><th>Days</th><th>Status</th></tr></thead>
          <tbody>${vacRows}</tbody>
        </table>
        <div class="report-field" style="margin-top:8px"><div class="rf-lbl">Next scheduled vacation</div><div class="rf-val">${e.nextVacStart?dFmt(e.nextVacStart)+' to '+dFmt(e.nextVacEnd):'Not scheduled'}</div></div>
      </div>

      <div class="report-section">
        <h3>Loan Summary</h3>
        <div class="report-grid">
          <div class="report-field"><div class="rf-lbl">Loan amount</div><div class="rf-val">${e.loanAmount?fmtSAR(e.loanAmount):'No loan'}</div></div>
          <div class="report-field"><div class="rf-lbl">Remaining balance</div><div class="rf-val">${e.loanRemaining?fmtSAR(e.loanRemaining):'—'}</div></div>
          <div class="report-field"><div class="rf-lbl">Amount paid</div><div class="rf-val">${e.loanAmount?fmtSAR(loanPaid):'—'}</div></div>
          <div class="report-field"><div class="rf-lbl">Monthly payment</div><div class="rf-val">${e.loanMonthly?fmtSAR(e.loanMonthly):'—'}</div></div>
          ${monthsLeft?`<div class="report-field"><div class="rf-lbl">Months to payoff</div><div class="rf-val">${monthsLeft} months</div></div>`:''}
        </div>
      </div>
    </div>
  `;
}

// ---------- Wareef employees (separate list, /api/wareef) ----------
const GOSI_CAP=45000;
const W_NUM=['basic','housing','transport','otherAllow','gosiEmpPct','gosiErPct','loanDed','otherDed','medicalIns','iqamaFee','workPermitFee','otherFees'];
const W_TXT=['name','empId','nationality','jobTitle','department','phone','idNumber','idExpiry','joiningDate','otherDedNote','insProvider','insClass','insPolicy','insExpiry','bankName','iban'];
const GOSI_RATES={'Saudi':[9.75,11.75],'Non-Saudi':[0,2]};
let wareef=[],hrIdx=null,activeTab='employees';
function num(v){return Number(v)||0}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function fmtM(n){return'SAR '+Number(n||0).toLocaleString(undefined,{minimumFractionDigits:0,maximumFractionDigits:2})}
function hrCalc(w){
  const basic=num(w.basic),housing=num(w.housing),transport=num(w.transport),otherAllow=num(w.otherAllow);
  const allowances=housing+transport+otherAllow,gross=basic+allowances;
  const gosiBase=Math.min(basic+housing,GOSI_CAP);
  const gosiEmp=gosiBase*num(w.gosiEmpPct)/100,gosiEr=gosiBase*num(w.gosiErPct)/100;
  const loan=num(w.loanDed),otherDed=num(w.otherDed),deductions=gosiEmp+loan+otherDed,net=gross-deductions;
  const annualFees=num(w.medicalIns)+num(w.iqamaFee)+num(w.workPermitFee)+num(w.otherFees);
  const costMonthly=gross+gosiEr+annualFees/12;
  return{basic,housing,transport,otherAllow,allowances,gross,gosiBase,gosiEmp,gosiEr,loan,otherDed,deductions,net,annualFees,costMonthly};
}
function insStatus(w){
  if(!w.insProvider&&!w.insExpiry)return{label:'None',cls:'badge-gray'};
  if(!w.insExpiry)return{label:'No date',cls:'badge-gray'};
  const ds=daysDiff(w.insExpiry);
  if(ds<0)return{label:'Expired',cls:'badge-red'};
  if(ds<=60)return{label:`${ds}d left`,cls:'badge-amber'};
  return{label:'Valid',cls:'badge-green'};
}
function switchTab(t){
  activeTab=t;
  document.getElementById('tab-employees').style.display=t==='employees'?'':'none';
  document.getElementById('tab-hr').style.display=t==='hr'?'':'none';
  document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active',b.dataset.tab===t));
  document.getElementById('addBtn').textContent=t==='hr'?'+ Add Wareef employee':'+ Add household worker';
  try{localStorage.setItem('et_tab',t)}catch(e){}
  if(t==='hr')renderHR();
}
function addForTab(){activeTab==='hr'?openHR(null):openAdd()}
async function loadWareef(){
  try{const res=await fetch('/api/wareef');if(!res.ok)throw new Error();wareef=await res.json();renderHR();}
  catch(e){showToast('Could not load Wareef employees',true)}
}
function renderHR(){
  const q=document.getElementById('hrSearch').value.toLowerCase();
  const fn=document.getElementById('filterNat').value;
  const fd=document.getElementById('filterHrId').value;
  const fi=document.getElementById('filterIns').value;
  let rows=[...wareef].sort((a,b)=>(a.name||'').localeCompare(b.name||''));
  if(q)rows=rows.filter(w=>[w.name,w.empId,w.jobTitle,w.department,w.idNumber,w.insProvider,w.bankName,w.iban,w.phone].join(' ').toLowerCase().includes(q));
  if(fn)rows=rows.filter(w=>(w.nationality||'Non-Saudi')===fn);
  if(fd==='expired')rows=rows.filter(w=>w.idExpiry&&daysDiff(w.idExpiry)<0);
  if(fd==='soon')rows=rows.filter(w=>{const ds=daysDiff(w.idExpiry);return w.idExpiry&&ds>=0&&ds<=60});
  if(fi==='expired')rows=rows.filter(w=>insStatus(w).cls==='badge-red');
  if(fi==='soon')rows=rows.filter(w=>insStatus(w).cls==='badge-amber');
  if(fi==='none')rows=rows.filter(w=>insStatus(w).label==='None');
  renderHRStats();
  const body=document.getElementById('hrBody'),foot=document.getElementById('hrFoot');
  if(!rows.length){body.innerHTML=`<tr><td colspan="14"><div class="state-box"><p>&#127970; No Wareef employees found</p><p class="sub">Add one with the "+ Add Wareef employee" button above</p></div></td></tr>`;foot.innerHTML='';return}
  const T={basic:0,allowances:0,gross:0,gosiEmp:0,otherAll:0,net:0,gosiEr:0,annualFees:0,costMonthly:0};
  body.innerHTML=rows.map((w,i)=>{
    const c=hrCalc(w),is=insStatus(w),ids=idStatus(w),oi=wareef.indexOf(w);
    c.otherAll=c.loan+c.otherDed;
    Object.keys(T).forEach(k=>T[k]+=c[k]);
    return`<tr>
      <td style="color:var(--text3);font-size:11px">${i+1}</td>
      <td><div class="td-name">${esc(w.name)}</div><div style="font-size:11px;color:var(--text2)">${esc(w.jobTitle||'')}${w.jobTitle&&w.empId?' · ':''}<span class="td-mono" style="font-size:10px">${esc(w.empId||'')}</span></div></td>
      <td><div class="td-mono">${esc(w.idNumber||'—')}</div><span class="badge ${ids.cls}" style="margin-top:3px">${ids.label}</span></td>
      <td class="num">${c.basic?fmtM(c.basic):'—'}</td>
      <td class="num">${c.allowances?fmtM(c.allowances):'—'}</td>
      <td class="num" style="font-weight:500">${fmtM(c.gross)}</td>
      <td class="num">${c.gosiEmp?fmtM(c.gosiEmp):'—'}</td>
      <td class="num">${c.otherAll?fmtM(c.otherAll):'—'}</td>
      <td class="num" style="font-weight:600;color:var(--accent)">${fmtM(c.net)}</td>
      <td class="num">${c.gosiEr?fmtM(c.gosiEr):'—'}</td>
      <td><div style="font-size:12px">${esc(w.insProvider||'—')}${w.insClass?' · '+esc(w.insClass):''}</div><span class="badge ${is.cls}" style="margin-top:3px">${is.label}${w.insExpiry&&is.cls!=='badge-gray'?' · '+dFmt(w.insExpiry):''}</span></td>
      <td class="num">${c.annualFees?fmtM(c.annualFees):'—'}</td>
      <td class="num" style="font-weight:600">${fmtM(c.costMonthly)}</td>
      <td><div class="row-actions">
        <button class="btn btn-icon" onclick="openWareefReport(${oi})" title="Report">&#128203;</button>
        <button class="btn btn-icon" onclick="openHR(${oi})" title="Edit">&#9998;</button>
        <button class="btn btn-icon" onclick="deleteWareef(${oi})" title="Delete" style="color:var(--red)">&#128465;</button>
      </div></td>
    </tr>`;
  }).join('');
  foot.innerHTML=`<tr><td></td><td>Total (${rows.length})</td><td></td>
    <td class="num">${fmtM(T.basic)}</td><td class="num">${fmtM(T.allowances)}</td><td class="num">${fmtM(T.gross)}</td>
    <td class="num">${fmtM(T.gosiEmp)}</td><td class="num">${fmtM(T.otherAll)}</td>
    <td class="num">${fmtM(T.net)}</td><td class="num">${fmtM(T.gosiEr)}</td><td></td>
    <td class="num">${fmtM(T.annualFees)}</td><td class="num">${fmtM(T.costMonthly)}</td><td></td></tr>`;
}
function renderHRStats(){
  const cs=wareef.map(hrCalc),sum=k=>cs.reduce((s,c)=>s+c[k],0);
  const saudi=wareef.filter(w=>w.nationality==='Saudi').length;
  const insExp=wareef.filter(w=>insStatus(w).cls==='badge-red').length;
  const insSoon=wareef.filter(w=>insStatus(w).cls==='badge-amber').length;
  const idExp=wareef.filter(w=>w.idExpiry&&daysDiff(w.idExpiry)<0).length;
  const idSoon=wareef.filter(w=>{const ds=daysDiff(w.idExpiry);return w.idExpiry&&ds>=0&&ds<=60}).length;
  const r=n=>Math.round(n).toLocaleString();
  const warn=(n,c)=>n>0?`border-color:var(--${c});background:var(--${c}-bg)`:'';
  document.getElementById('hrStatsRow').innerHTML=`
    <div class="stat-card"><div class="lbl">Wareef employees</div><div class="val">${wareef.length}</div></div>
    <div class="stat-card"><div class="lbl">Saudi / non-Saudi</div><div class="val sm">${saudi} / ${wareef.length-saudi}</div></div>
    <div class="stat-card"><div class="lbl">Gross payroll / mo</div><div class="val sm">SAR ${r(sum('gross'))}</div></div>
    <div class="stat-card"><div class="lbl">Net payroll / mo</div><div class="val sm">SAR ${r(sum('net'))}</div></div>
    <div class="stat-card"><div class="lbl">GOSI total / mo</div><div class="val sm">SAR ${r(sum('gosiEmp')+sum('gosiEr'))}</div></div>
    <div class="stat-card"><div class="lbl">Insurance &amp; fees / yr</div><div class="val sm">SAR ${r(sum('annualFees'))}</div></div>
    <div class="stat-card"><div class="lbl">Cost to company / mo</div><div class="val sm">SAR ${r(sum('costMonthly'))}</div></div>
    <div class="stat-card"><div class="lbl">Cost to company / yr</div><div class="val sm">SAR ${r(sum('costMonthly')*12)}</div></div>
    <div class="stat-card" style="${warn(idExp,'red')}"><div class="lbl">ID expired</div><div class="val">${idExp}</div></div>
    <div class="stat-card" style="${warn(idSoon,'amber')}"><div class="lbl">ID expiring 60d</div><div class="val">${idSoon}</div></div>
    <div class="stat-card" style="${warn(insExp,'red')}"><div class="lbl">Insurance expired</div><div class="val">${insExp}</div></div>
    <div class="stat-card" style="${warn(insSoon,'amber')}"><div class="lbl">Insurance expiring 60d</div><div class="val">${insSoon}</div></div>`;
}
function readHRForm(){
  const w={};
  W_NUM.forEach(k=>w[k]=num(document.getElementById('h_'+k).value));
  W_TXT.forEach(k=>w[k]=document.getElementById('h_'+k).value.trim());
  return w;
}
function updateHRCalc(){
  const c=hrCalc(readHRForm());
  document.getElementById('hrCalcBox').innerHTML=`
    <span>Gross salary</span><span class="num">${fmtM(c.gross)}</span>
    <span>GOSI employee share</span><span class="num">− ${fmtM(c.gosiEmp)}</span>
    <span>Loan / advance</span><span class="num">− ${fmtM(c.loan)}</span>
    <span>Other deductions</span><span class="num">− ${fmtM(c.otherDed)}</span>
    <span class="c-strong">Net pay / month</span><span class="num c-strong" style="color:var(--accent)">${fmtM(c.net)}</span>
    <span>GOSI employer share</span><span class="num">${fmtM(c.gosiEr)}</span>
    <span>Insurance &amp; fees (÷12)</span><span class="num">${fmtM(c.annualFees/12)}</span>
    <span class="c-strong">Cost to company / month</span><span class="num c-strong">${fmtM(c.costMonthly)}</span>`;
}
function natChanged(){
  const [e,r]=GOSI_RATES[document.getElementById('h_nationality').value]||[0,0];
  document.getElementById('h_gosiEmpPct').value=e;document.getElementById('h_gosiErPct').value=r;updateHRCalc();
}
function openHR(i){
  hrIdx=i;const w=i===null?{}:wareef[i];
  document.getElementById('hrModalTitle').textContent=i===null?'Add Wareef employee':'Edit — '+(w.name||'');
  document.getElementById('hrSaveBtn').textContent=i===null?'Save employee':'Update employee';
  W_NUM.forEach(k=>document.getElementById('h_'+k).value=w[k]||'');
  W_TXT.forEach(k=>document.getElementById('h_'+k).value=w[k]||'');
  if(!w.nationality)document.getElementById('h_nationality').value='Non-Saudi';
  if(i===null)natChanged();
  updateHRCalc();
  document.getElementById('hrModal').classList.add('open');
}
function closeHR(){document.getElementById('hrModal').classList.remove('open');hrIdx=null}
async function saveHR(){
  const w=readHRForm();
  if(!w.name||!w.empId){showToast('Name and Employee ID are required.',true);return}
  const btn=document.getElementById('hrSaveBtn'),editing=hrIdx!==null;btn.disabled=true;btn.textContent='Saving…';
  try{
    const res=editing
      ?await fetch(`/api/wareef/${wareef[hrIdx]._id}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(w)})
      :await fetch('/api/wareef',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(w)});
    if(!res.ok)throw new Error();
    showToast(editing?'Employee updated ✓':'Employee added ✓');closeHR();await loadWareef();
  }catch(e){showToast('Save failed',true)}
  finally{btn.disabled=false;btn.textContent=editing?'Update employee':'Save employee'}
}
async function deleteWareef(i){
  if(!confirm(`Delete ${wareef[i].name}?`))return;
  try{const res=await fetch(`/api/wareef/${wareef[i]._id}`,{method:'DELETE'});if(!res.ok)throw new Error();showToast('Employee deleted');await loadWareef();}
  catch(e){showToast('Delete failed',true)}
}
function openWareefReport(i){
  const w=wareef[i],c=hrCalc(w),tenure=yearsFrom(w.joiningDate),ids=idStatus(w),is=insStatus(w);
  const f=(l,v)=>`<div class="report-field"><div class="rf-lbl">${l}</div><div class="rf-val">${v}</div></div>`;
  document.getElementById('reportContent').innerHTML=`
    <div id="reportPrintArea">
      <div class="report-header"><h1>Wareef Employee Report — ${esc(w.name)}</h1><p>Generated on ${new Date().toLocaleDateString()} &middot; Employee ID: ${esc(w.empId||'—')}</p></div>
      <div class="report-section"><h3>Personal &amp; Job</h3><div class="report-grid">
        ${f('Full name',esc(w.name))}${f('Employee ID',esc(w.empId||'—'))}
        ${f('Nationality',esc(w.nationality||'—'))}${f('Job title / department',esc(w.jobTitle||'—')+(w.department?' · '+esc(w.department):''))}
        ${f('Phone',esc(w.phone||'—'))}${f('Iqama / ID number',esc(w.idNumber||'—'))}
        ${f('ID expiry',dFmt(w.idExpiry)+' ('+ids.label+')')}${f('Joining date',dFmt(w.joiningDate)+(tenure?' — '+tenure+' years':''))}
      </div></div>
      <div class="report-section"><h3>Salary &amp; Deductions (monthly)</h3><table class="report-table"><tbody>
        <tr><td>Basic salary</td><td class="num">${fmtM(c.basic)}</td></tr>
        <tr><td>Housing allowance</td><td class="num">${fmtM(c.housing)}</td></tr>
        <tr><td>Transport allowance</td><td class="num">${fmtM(c.transport)}</td></tr>
        <tr><td>Other allowances</td><td class="num">${fmtM(c.otherAllow)}</td></tr>
        <tr><td><b>Gross salary</b></td><td class="num"><b>${fmtM(c.gross)}</b></td></tr>
        <tr><td>GOSI employee share (${num(w.gosiEmpPct)}%)</td><td class="num">− ${fmtM(c.gosiEmp)}</td></tr>
        <tr><td>Loan / advance</td><td class="num">− ${fmtM(c.loan)}</td></tr>
        <tr><td>Other deductions${w.otherDedNote?' — '+esc(w.otherDedNote):''}</td><td class="num">− ${fmtM(c.otherDed)}</td></tr>
        <tr><td><b>Net pay</b></td><td class="num"><b>${fmtM(c.net)}</b></td></tr>
      </tbody></table></div>
      <div class="report-section"><h3>Employer Costs</h3><div class="report-grid">
        ${f('GOSI employer share ('+num(w.gosiErPct)+'%) / month',fmtM(c.gosiEr))}
        ${f('Medical insurance',esc(w.insProvider||'—')+(w.insClass?' · Class '+esc(w.insClass):'')+(w.insPolicy?' · '+esc(w.insPolicy):'')+' ('+is.label+(w.insExpiry?', exp. '+dFmt(w.insExpiry):'')+')')}
        ${f('Insurance premium / year',fmtM(w.medicalIns))}${f('Iqama renewal fee / year',fmtM(w.iqamaFee))}
        ${f('Work permit fee / year',fmtM(w.workPermitFee))}${f('Other fees / year',fmtM(w.otherFees))}
        ${f('Cost to company / month',fmtM(c.costMonthly))}${f('Cost to company / year',fmtM(c.costMonthly*12))}
      </div></div>
      <div class="report-section"><h3>Bank</h3><div class="report-grid">${f('Bank name',esc(w.bankName||'—'))}${f('IBAN',esc(w.iban||'—'))}</div></div>
    </div>`;
  document.getElementById('reportModal').classList.add('open');
}
document.getElementById('hrModal').addEventListener('input',updateHRCalc);
document.getElementById('hrModal').addEventListener('click',e=>{if(e.target===e.currentTarget)closeHR()});
try{if(localStorage.getItem('et_tab')==='hr')switchTab('hr')}catch(e){}
loadWareef();

function closeDetail(){document.getElementById('detailModal').classList.remove('open')}
document.getElementById('formModal').addEventListener('click',e=>{if(e.target===e.currentTarget)closeModal()});
document.getElementById('detailModal').addEventListener('click',e=>{if(e.target===e.currentTarget)closeDetail()});
document.getElementById('reportModal').addEventListener('click',e=>{if(e.target===e.currentTarget)closeReport()});
loadData();
</script>
</body>
</html>"""

HTML = auth.add_logout(HTML)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/' or path == '/index.html':
            body = HTML.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)
        elif api_collection(path)[0] is not None and api_collection(path)[1] is None:
            try:
                self.send_json(load_employees(api_collection(path)[0]))
            except Exception as ex:
                self.send_json({'error': str(ex)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        col, doc_id = api_collection(urlparse(self.path).path)
        if col is not None and doc_id is None:
            length = int(self.headers.get('Content-Length', 0))
            emp = json.loads(self.rfile.read(length))
            try:
                add_employee(emp, col)
                self.send_json({'status': 'ok'})
            except Exception as ex:
                self.send_json({'error': str(ex)}, 500)

    def do_PUT(self):
        col, doc_id = api_collection(urlparse(self.path).path)
        if col is not None and doc_id:
            length = int(self.headers.get('Content-Length', 0))
            emp = json.loads(self.rfile.read(length))
            try:
                update_employee(doc_id, emp, col)
                self.send_json({'status': 'ok'})
            except Exception as ex:
                self.send_json({'error': str(ex)}, 500)

    def do_DELETE(self):
        col, doc_id = api_collection(urlparse(self.path).path)
        if col is not None and doc_id:
            try:
                delete_employee(doc_id, col)
                self.send_json({'status': 'ok'})
            except Exception as ex:
                self.send_json({'error': str(ex)}, 500)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8500))
    server = HTTPServer(('0.0.0.0', port), auth.protect(Handler, 'Employee Tracker'))
    print(f'Employee Tracker running on port {port}')
    server.serve_forever()
