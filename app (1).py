import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'employees.json')

def load_employees():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_employees(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Employee Tracker</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{--bg:#f5f4f0;--surface:#fff;--surface2:#f0efe9;--border:#e2e0d8;--border2:#cccac0;--text:#1a1916;--text2:#6b6860;--text3:#9e9c96;--accent:#1a6b4a;--accent-bg:#e8f4ee;--amber:#92500a;--amber-bg:#fdf0e0;--red:#8b2020;--red-bg:#fdeaea;--blue:#1a4a7a;--blue-bg:#e8f0fa;--radius:8px;--radius-lg:12px;--font:'IBM Plex Sans',sans-serif;--mono:'IBM Plex Mono',monospace}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font);background:var(--bg);color:var(--text);min-height:100vh}
.app{max-width:1500px;margin:0 auto;padding:2rem 1.5rem}
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
#searchInput{width:100%;padding:9px 12px 9px 36px;font-size:13px;font-family:var(--font);border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);color:var(--text);outline:none}
#searchInput:focus{border-color:var(--border2)}
select.filter{font-size:13px;font-family:var(--font);padding:8px 12px;border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);color:var(--text);cursor:pointer;outline:none}
.btn{display:inline-flex;align-items:center;gap:6px;font-size:13px;font-family:var(--font);font-weight:500;padding:8px 16px;border-radius:var(--radius);border:1px solid var(--border);background:var(--surface);color:var(--text);cursor:pointer;transition:background .15s;white-space:nowrap}
.btn:hover{background:var(--surface2)}
.btn:disabled{opacity:.5;cursor:not-allowed}
.btn-primary{background:var(--text);color:var(--bg);border-color:var(--text)}
.btn-primary:hover{opacity:.85;background:var(--text)}
.btn-icon{padding:5px;width:28px;height:28px;justify-content:center;font-size:14px}
.table-wrap{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px;min-width:1200px}
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
.modal{background:var(--surface);border-radius:var(--radius-lg);border:1px solid var(--border);padding:1.75rem;width:100%;max-width:560px;max-height:92vh;overflow-y:auto}
.modal-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem}
.modal-header h2{font-size:16px;font-weight:600}
.section-sep{font-size:10px;font-weight:600;color:var(--text3);text-transform:uppercase;letter-spacing:.08em;margin:1.25rem 0 10px;padding-bottom:6px;border-bottom:1px solid var(--border)}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.fg{display:flex;flex-direction:column;gap:4px}
.fg.full{grid-column:1/-1}
.fg label{font-size:11px;font-weight:500;color:var(--text2)}
.fg input{font-size:13px;font-family:var(--font);padding:8px 10px;border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);color:var(--text);outline:none}
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
.hl-label{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px}
.hl-green .hl-label{color:var(--accent)}
.hl-amber .hl-label{color:var(--amber)}
.hl-red .hl-label{color:var(--red)}
.hl-value{font-size:14px;font-weight:600}
.hl-green .hl-value{color:#0f4a30}
.hl-amber .hl-value{color:#5a3000}
.hl-red .hl-value{color:var(--red)}
.hl-sub{font-size:12px;margin-top:3px}
.hl-green .hl-sub{color:var(--accent)}
.hl-amber .hl-sub{color:var(--amber)}
.hl-red .hl-sub{color:var(--red)}
.d-grid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;margin-bottom:10px}
.d-cell{background:var(--surface);padding:10px 12px}
.d-cell-lbl{font-size:10px;font-weight:500;color:var(--text3);text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px}
.d-cell-val{font-size:13px;font-weight:500;color:var(--text)}
.toast{position:fixed;bottom:2rem;right:2rem;background:var(--text);color:var(--bg);font-size:13px;padding:10px 18px;border-radius:var(--radius);z-index:999;opacity:0;transform:translateY(10px);transition:all .25s;pointer-events:none;max-width:340px}
.toast.show{opacity:1;transform:translateY(0)}
.toast.error{background:var(--red)}
.sync-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px;background:var(--accent)}
@media(max-width:600px){.form-grid{grid-template-columns:1fr}.fg.full{grid-column:1}.app{padding:1rem}}
</style>
</head>
<body>
<div class="app">
  <div class="header">
    <div class="header-left">
      <h1>&#128101; Employee Tracker</h1>
      <p><span class="sync-dot"></span>Data saved on server</p>
    </div>
    <div class="header-right">
      <button class="btn" onclick="loadData()">&#8635; Refresh</button>
      <button class="btn btn-primary" onclick="openAdd()">+ Add employee</button>
    </div>
  </div>
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
    <div class="section-sep">Loan</div>
    <div class="form-grid">
      <div class="fg"><label>Loan amount (SAR)</label><input type="number" id="f_loan" placeholder="0 = no loan" min="0"></div>
      <div class="fg"><label>Loan remaining (SAR)</label><input type="number" id="f_loan_rem" placeholder="0" min="0"></div>
      <div class="fg full"><label>Monthly payment (SAR)</label><input type="number" id="f_loan_pay" placeholder="0" min="0"></div>
    </div>
    <div class="modal-actions">
      <button class="btn" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" id="saveBtn" onclick="saveEmployee()">Save employee</button>
    </div>
  </div>
</div>

<div class="overlay" id="detailModal">
  <div class="modal" style="max-width:500px">
    <div class="modal-header">
      <h2>Employee details</h2>
      <button class="btn btn-icon" onclick="closeDetail()">&#10005;</button>
    </div>
    <div id="detailContent"></div>
    <div class="modal-actions">
      <button class="btn" onclick="closeDetail()">Close</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const TODAY=new Date();TODAY.setHours(0,0,0,0);
let employees=[],sortField='name',sortDir=1,editIdx=null;
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
  rows.sort((a,b)=>{let av=a[sortField]||'',bv=b[sortField]||'';if(['loanAmount','loanRemaining','loanMonthly'].includes(sortField)){av=Number(av);bv=Number(bv)}return av>bv?sortDir:av<bv?-sortDir:0});
  const tbody=document.getElementById('tableBody');
  if(!rows.length){tbody.innerHTML=`<tr><td colspan="14"><div class="state-box"><p>&#128100; No employees found</p><p class="sub">Add your first employee using the button above</p></div></td></tr>`;renderStats();return}
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
      <td style="font-size:11px">${e.nextVacStart?dFmt(e.nextVacStart)+(e.nextVacEnd?' – '+dFmt(e.nextVacEnd):''):'—'}</td>
      <td><span class="badge ${vs.cls}">${vs.label}</span></td>
      <td style="font-size:12px">${e.loanRemaining>0?fmtSAR(e.loanRemaining):'—'}</td>
      <td><span class="badge ${ls.cls}">${ls.label}</span></td>
      <td><div class="row-actions">
        <button class="btn btn-icon" onclick="openDetail(${oi})">&#128065;</button>
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
  const expiredId=employees.filter(e=>e.idExpiry&&daysDiff(e.idExpiry)<0).length;
  const expiringId=employees.filter(e=>{const ds=daysDiff(e.idExpiry);return ds>=0&&ds<=60}).length;
  document.getElementById('statsRow').innerHTML=`
    <div class="stat-card"><div class="lbl">Employees</div><div class="val">${employees.length}</div></div>
    <div class="stat-card"><div class="lbl">On vacation</div><div class="val">${onVac}</div></div>
    <div class="stat-card"><div class="lbl">Vacation in 30d</div><div class="val">${upcoming}</div></div>
    <div class="stat-card"><div class="lbl">Active loans</div><div class="val">${withLoan}</div></div>
    <div class="stat-card"><div class="lbl">Total loan left</div><div class="val sm">SAR ${totalLoan.toLocaleString()}</div></div>
    <div class="stat-card" style="${expiredId>0?'border-color:var(--red);background:var(--red-bg)':''}"><div class="lbl">ID expired</div><div class="val" style="${expiredId>0?'color:var(--red)':''}">${expiredId}</div></div>
    <div class="stat-card" style="${expiringId>0?'border-color:var(--amber);background:var(--amber-bg)':''}"><div class="lbl">ID expiring 60d</div><div class="val" style="${expiringId>0?'color:var(--amber)':''}">${expiringId}</div></div>
  `;
}

function openAdd(){editIdx=null;clearForm();document.getElementById('formModalTitle').textContent='Add employee';document.getElementById('saveBtn').textContent='Save employee';document.getElementById('formModal').classList.add('open')}
function openEdit(i){editIdx=i;fillForm(employees[i]);document.getElementById('formModalTitle').textContent='Edit employee';document.getElementById('saveBtn').textContent='Update employee';document.getElementById('formModal').classList.add('open')}
function closeModal(){document.getElementById('formModal').classList.remove('open')}
function clearForm(){['f_name','f_empId','f_phone','f_borderNo','f_idExpiry','f_joiningDate','f_employerName','f_employerId','f_lv_start','f_lv_end','f_nv_start','f_nv_end','f_loan','f_loan_rem','f_loan_pay'].forEach(id=>document.getElementById(id).value='')}
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
}

async function saveEmployee(){
  const emp={
    name:document.getElementById('f_name').value.trim(),
    empId:document.getElementById('f_empId').value.trim(),
    phone:document.getElementById('f_phone').value.trim(),
    borderNo:document.getElementById('f_borderNo').value.trim(),
    idExpiry:document.getElementById('f_idExpiry').value,
    joiningDate:document.getElementById('f_joiningDate').value,
    employerName:document.getElementById('f_employerName').value.trim(),
    employerId:document.getElementById('f_employerId').value.trim(),
    lastVacStart:document.getElementById('f_lv_start').value,
    lastVacEnd:document.getElementById('f_lv_end').value,
    nextVacStart:document.getElementById('f_nv_start').value,
    nextVacEnd:document.getElementById('f_nv_end').value,
    loanAmount:Number(document.getElementById('f_loan').value)||0,
    loanRemaining:Number(document.getElementById('f_loan_rem').value)||0,
    loanMonthly:Number(document.getElementById('f_loan_pay').value)||0,
  };
  if(!emp.name||!emp.empId){showToast('Name and Employee ID are required.',true);return}
  const btn=document.getElementById('saveBtn');btn.textContent='Saving…';btn.disabled=true;
  try{
    if(editIdx!==null){await fetch(`/api/employees/${editIdx}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(emp)});showToast('Employee updated ✓');}
    else{await fetch('/api/employees',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(emp)});showToast('Employee added ✓');}
    closeModal();await loadData();
  }catch(e){showToast('Save failed',true)}
  finally{btn.textContent=editIdx!==null?'Update employee':'Save employee';btn.disabled=false}
}

async function deleteEmp(i){
  if(!confirm(`Delete ${employees[i].name}?`))return;
  try{await fetch(`/api/employees/${i}`,{method:'DELETE'});showToast('Employee deleted');await loadData();}
  catch(e){showToast('Delete failed',true)}
}

function openDetail(i){
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
    <div class="hl hl-green">
      <div class="hl-label">&#127958; Vacation</div>
      <div class="hl-value">${nv}</div>
      <div class="hl-sub">${nd?nd+' · ':''} Last: ${lv}</div>
    </div>
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
function closeDetail(){document.getElementById('detailModal').classList.remove('open')}
document.getElementById('formModal').addEventListener('click',e=>{if(e.target===e.currentTarget)closeModal()});
document.getElementById('detailModal').addEventListener('click',e=>{if(e.target===e.currentTarget)closeDetail()});
loadData();
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
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
        elif path == '/api/employees':
            self.send_json(load_employees())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/employees':
            length = int(self.headers.get('Content-Length', 0))
            emp = json.loads(self.rfile.read(length))
            data = load_employees()
            data.append(emp)
            save_employees(data)
            self.send_json({'status': 'ok'})

    def do_PUT(self):
        path = urlparse(self.path).path
        parts = path.split('/')
        if len(parts) == 4 and parts[2] == 'employees':
            idx = int(parts[3])
            length = int(self.headers.get('Content-Length', 0))
            emp = json.loads(self.rfile.read(length))
            data = load_employees()
            if 0 <= idx < len(data):
                data[idx] = emp
                save_employees(data)
            self.send_json({'status': 'ok'})

    def do_DELETE(self):
        path = urlparse(self.path).path
        parts = path.split('/')
        if len(parts) == 4 and parts[2] == 'employees':
            idx = int(parts[3])
            data = load_employees()
            if 0 <= idx < len(data):
                data.pop(idx)
                save_employees(data)
            self.send_json({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8500))
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f'Employee Tracker running on port {port}')
    server.serve_forever()
