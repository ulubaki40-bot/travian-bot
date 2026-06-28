import os
import time
import random
import logging
import requests
from flask import Flask, request, jsonify, render_template_string
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
scheduler = BackgroundScheduler()
scheduler.start()

SERVER_URL = "https://ts2.x1.international.travian.com"
USERNAME = os.environ.get("TRAVIAN_USERNAME", "")
PASSWORD = os.environ.get("TRAVIAN_PASSWORD", "")

state = {
    "farm_lists": [],
    "last_action": ""
}

HTML_PANEL = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Travian Bot — HUDUT</title>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#06060e;color:#d4c9a8;font-family:'Rajdhani',sans-serif;min-height:100vh;padding-bottom:40px}
  header{background:#0d0d1a;border-bottom:0.5px solid #1a1a2e;padding:14px 16px;position:sticky;top:0;z-index:100;display:flex;justify-content:space-between;align-items:center}
  .logo{font-family:'Cinzel',serif;font-size:18px;color:#f5c842;letter-spacing:2px}
  .logo span{font-size:10px;display:block;color:#6b6b8a;letter-spacing:3px;font-family:'Rajdhani',sans-serif;font-weight:600;margin-top:2px}
  .made-by{font-size:10px;color:#6b6b8a;text-align:right;letter-spacing:1px}
  .made-by strong{color:#f5c842}
  .container{max-width:480px;margin:0 auto;padding:16px}
  .section-title{font-size:11px;color:#6b6b8a;font-weight:600;letter-spacing:2px;text-transform:uppercase;margin:20px 0 10px}
  .card{background:#0d0d1a;border:0.5px solid #1e1e35;border-radius:12px;padding:14px;margin-bottom:10px}
  .lbl{font-size:11px;color:#6b6b8a;margin-bottom:4px;display:block;font-weight:600;letter-spacing:1px}
  input,textarea,select{width:100%;background:#0a0a14;border:0.5px solid #1e1e35;border-radius:8px;color:#d4c9a8;padding:9px 12px;font-size:13px;font-family:'Rajdhani',sans-serif;font-weight:600;outline:none;margin-bottom:10px}
  textarea{resize:none;height:60px}
  input:focus,textarea:focus,select:focus{border-color:#f5c842}
  select option{background:#0d0d1a}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
  .btn-gold{width:100%;background:#f5c842;color:#0a0a14;border:none;border-radius:8px;padding:10px;font-family:'Cinzel',serif;font-size:13px;font-weight:700;cursor:pointer;letter-spacing:1px;margin-top:4px}
  .farm-card{background:#0d0d1a;border:0.5px solid #1e1e35;border-radius:12px;padding:14px;margin-bottom:10px}
  .farm-card.night-on{border-color:#2a1a35}
  .fc-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
  .fc-name{font-weight:600;font-size:15px;color:#fff}
  .fc-id{font-size:12px;color:#6b6b8a;margin-top:2px}
  .badge{font-size:11px;padding:3px 8px;border-radius:6px;font-weight:500}
  .badge-active{background:rgba(78,203,113,0.15);color:#4ecb71}
  .badge-paused{background:#1e1e35;color:#6b6b8a}
  .badge-night{background:rgba(138,43,226,0.2);color:#b06aff}
  .next-send{border-radius:8px;padding:8px 12px;margin-bottom:10px}
  .ns-normal{background:rgba(245,200,66,0.08);border:0.5px solid rgba(245,200,66,0.2)}
  .ns-night{background:rgba(138,43,226,0.1);border:0.5px solid rgba(138,43,226,0.25)}
  .ns-paused{background:#0a0a14;border:0.5px solid #1e1e35}
  .ns-label{font-size:11px;color:#6b6b8a;margin-bottom:3px}
  .ns-label-night{font-size:11px;color:#9b6bd4;margin-bottom:3px}
  .ns-value{font-size:14px;font-weight:600;color:#f5c842}
  .ns-value-night{font-size:14px;font-weight:600;color:#b06aff}
  .ns-value-paused{font-size:14px;font-weight:600;color:#6b6b8a}
  .today-box{background:#0a0a14;border:0.5px solid #1e1e35;border-radius:8px;padding:8px 12px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center}
  .today-box.nb{border-color:rgba(138,43,226,0.2)}
  .today-label{font-size:11px;color:#6b6b8a}
  .today-label-night{font-size:11px;color:#9b6bd4}
  .today-value{font-size:13px;font-weight:600;color:#4ecb71}
  .night-schedule-box{background:#0a0a14;border:0.5px solid rgba(138,43,226,0.2);border-radius:8px;padding:10px 12px;margin-bottom:10px}
  .nst-title{font-size:11px;color:#9b6bd4;margin-bottom:6px;font-weight:600;letter-spacing:1px}
  .nst-item{font-size:12px;color:#b06aff;padding:2px 0}
  .night-row{display:flex;align-items:center;justify-content:space-between;padding:9px 0;border-top:0.5px solid #1e1e35;margin-bottom:10px}
  .night-left{display:flex;align-items:center;gap:8px;font-size:13px;color:#d4c9a8}
  .night-right{display:flex;align-items:center;gap:8px}
  .night-status{font-size:12px}
  .toggle{width:40px;height:22px;border-radius:11px;position:relative;cursor:pointer}
  .toggle-off{background:#1e1e35}
  .toggle-on{background:rgba(138,43,226,0.4)}
  .toggle-circle{width:18px;height:18px;border-radius:50%;position:absolute;top:2px}
  .toggle-circle-off{background:#6b6b8a;left:2px}
  .toggle-circle-on{background:#b06aff;right:2px}
  .night-panel{background:#0a0a14;border:0.5px solid rgba(138,43,226,0.2);border-radius:10px;padding:12px;margin-bottom:10px}
  .night-panel-title{font-size:11px;color:#9b6bd4;font-weight:600;letter-spacing:1px;margin-bottom:10px;text-transform:uppercase}
  .btn-purple{width:100%;background:rgba(138,43,226,0.15);color:#b06aff;border:0.5px solid rgba(138,43,226,0.3);border-radius:8px;padding:8px;font-size:12px;font-weight:600;cursor:pointer;margin-top:4px}
  .btn-row{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px}
  .btn-pause{background:rgba(224,85,85,0.12);color:#e05555;border:0.5px solid rgba(224,85,85,0.3);border-radius:8px;padding:8px;font-size:11px;font-weight:500;cursor:pointer}
  .btn-start{background:rgba(78,203,113,0.12);color:#4ecb71;border:0.5px solid rgba(78,203,113,0.3);border-radius:8px;padding:8px;font-size:11px;font-weight:500;cursor:pointer}
  .btn-copy{background:rgba(245,200,66,0.1);color:#f5c842;border:0.5px solid rgba(245,200,66,0.3);border-radius:8px;padding:8px;font-size:11px;font-weight:500;cursor:pointer}
  .btn-remove{background:transparent;color:#e05555;border:0.5px solid rgba(224,85,85,0.3);border-radius:8px;padding:8px;font-size:11px;font-weight:500;cursor:pointer}
  .last-action{font-size:12px;color:#6b6b8a;text-align:center;padding:8px;background:#0d0d1a;border-radius:8px;margin-bottom:12px;border:0.5px solid #1e1e35}
  .alert{padding:10px 14px;border-radius:8px;font-size:13px;font-weight:600;margin-bottom:10px;display:none}
  .alert-success{background:rgba(78,203,113,0.15);border:0.5px solid rgba(78,203,113,0.3);color:#4ecb71}
  .alert-error{background:rgba(224,85,85,0.15);border:0.5px solid rgba(224,85,85,0.3);color:#e05555}
  .empty{text-align:center;color:#6b6b8a;padding:24px;font-size:13px}
  .hidden{display:none}
</style>
</head>
<body>
<header>
  <div class="logo">⚔️ TRAVIAN BOT<span>YAĞMA PANELİ</span></div>
  <div class="made-by">Yapımcı<br><strong>HUDUT</strong></div>
</header>
<div class="container">
  <div id="alert" class="alert"></div>
  <div class="last-action" id="last-action">Bağlanıyor...</div>

  <div class="section-title">Yağma Listesi Ekle</div>
  <div class="card">
    <label class="lbl">Liste Adı</label>
    <input type="text" id="f-name" placeholder="Örnek: lejyoner">
    <label class="lbl">Liste ID</label>
    <input type="number" id="f-id" placeholder="Örnek: 2525">
    <label class="lbl">Hedef ID'leri (virgülle ayır)</label>
    <textarea id="f-targets" placeholder="55950, 55945, 60602, 60617..."></textarea>
    <div class="grid2">
      <div>
        <label class="lbl">Min dakika</label>
        <input type="number" id="f-min" value="45">
      </div>
      <div>
        <label class="lbl">Max dakika</label>
        <input type="number" id="f-max" value="90">
      </div>
    </div>
    <label class="lbl">Gönderim sayısı (0 = sınırsız)</label>
    <input type="number" id="f-daily" value="0">
    <button class="btn-gold" onclick="addFarmList()">⚔️ LİSTEYİ EKLE</button>
  </div>

  <div class="section-title">Aktif Listeler</div>
  <div id="farm-list"><div class="empty">Henüz liste yok</div></div>
</div>

<script>
function showAlert(msg, type) {
  const el = document.getElementById('alert');
  el.textContent = msg;
  el.className = 'alert ' + (type === 'success' ? 'alert-success' : 'alert-error');
  el.style.display = 'block';
  setTimeout(() => el.style.display = 'none', 3000);
}

function formatTime(seconds) {
  if (!seconds || seconds <= 0) return '—';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return h + ' saat ' + m + ' dk sonra';
  if (m > 0) return m + ' dk ' + s + ' sn sonra';
  return s + ' saniye sonra';
}

function renderFarmLists(lists) {
  const el = document.getElementById('farm-list');
  if (!lists || !lists.length) { el.innerHTML = '<div class="empty">Henüz liste yok</div>'; return; }
  el.innerHTML = lists.map(f => {
    const isNight = f.night_mode;
    const isPaused = f.paused;

    const badge = isPaused ? '<span class="badge badge-paused">Durduruldu</span>' :
                  isNight ? '<span class="badge badge-night">🌙 Gece</span>' :
                  '<span class="badge badge-active">Aktif</span>';

    const nsClass = isPaused ? 'next-send ns-paused' : isNight ? 'next-send ns-night' : 'next-send ns-normal';
    const nsLbl = isPaused ? '<div class="ns-label">Durum</div>' :
                  isNight ? '<div class="ns-label-night">Sonraki gönderim (gece modu)</div>' :
                  '<div class="ns-label">Sonraki gönderim</div>';
    const nsVal = isPaused ? '<div class="ns-value-paused">— Durduruldu</div>' :
                  isNight ? `<div class="ns-value-night">🌙 ${formatTime(f.next_seconds)}</div>` :
                  `<div class="ns-value">⏰ ${formatTime(f.next_seconds)}</div>`;

    const todayClass = 'today-box' + (isNight ? ' nb' : '');
    const todayLbl = isNight ? '<span class="today-label-night">Bugün gönderildi</span>' : '<span class="today-label">Bugün gönderildi</span>';

    // Gece planı
    let nightScheduleHtml = '';
    if (isNight && f.night_schedule && f.night_schedule.length) {
      const items = f.night_schedule.map(t => `<div class="nst-item">🕐 ${t}</div>`).join('');
      nightScheduleHtml = `<div class="night-schedule-box">
        <div class="nst-title">Gece Gönderim Planı</div>
        ${items}
      </div>`;
    }

    // Gece paneli
    const nightPanelHtml = isNight ? `
      <div class="night-panel" id="np-${f.job_id}">
        <div class="night-panel-title">🌙 Gece Modu Ayarları</div>
        <div class="grid2">
          <div>
            <label class="lbl">Başlangıç saati</label>
            <input type="time" id="ns-${f.job_id}" value="${f.night_start || '23:00'}">
          </div>
          <div>
            <label class="lbl">Bitiş saati</label>
            <input type="time" id="ne-${f.job_id}" value="${f.night_end || '07:00'}">
          </div>
        </div>
        <label class="lbl">Kaç kez göndersin</label>
        <input type="number" id="nc-${f.job_id}" value="${f.night_count || 5}" min="1">
        <button class="btn-purple" onclick="saveNight('${f.job_id}')">🌙 Gece Planını Kaydet</button>
      </div>
      ${nightScheduleHtml}` : '';

    return `<div class="farm-card ${isNight ? 'night-on' : ''}" id="card-${f.job_id}">
      <div class="fc-header">
        <div><div class="fc-name">⚔️ ${f.name}</div><div class="fc-id">ID: ${f.list_id}</div></div>
        ${badge}
      </div>
      <div class="${nsClass}">${nsLbl}${nsVal}</div>
      <div class="${todayClass}">${todayLbl}<span class="today-value">${f.today_count || 0} kez</span></div>
      ${nightPanelHtml}
      <div class="night-row">
        <div class="night-left">🌙 Gece modu</div>
        <div class="night-right">
          <span class="night-status" style="color:${isNight ? '#b06aff' : '#6b6b8a'}">${isNight ? 'Açık' : 'Kapalı'}</span>
          <div class="toggle ${isNight ? 'toggle-on' : 'toggle-off'}" onclick="toggleNight('${f.job_id}')">
            <div class="toggle-circle ${isNight ? 'toggle-circle-on' : 'toggle-circle-off'}"></div>
          </div>
        </div>
      </div>
      <div class="btn-row">
        <button class="btn-pause" onclick="pauseFarm('${f.job_id}')">⏸ Durdur</button>
        <button class="btn-start" onclick="startFarm('${f.job_id}')">▶ Başlat</button>
        <button class="btn-copy" onclick="copyFarm('${f.job_id}')">⧉ Kopya</button>
        <button class="btn-remove" onclick="removeFarm('${f.job_id}')">🗑 Kaldır</button>
      </div>
    </div>`;
  }).join('');
}

async function checkStatus() {
  try {
    const r = await fetch('/status');
    const d = await r.json();
    if (d.last_action) document.getElementById('last-action').textContent = '🕐 ' + d.last_action;
    renderFarmLists(d.farm_lists);
  } catch(e) {
    document.getElementById('last-action').textContent = 'Bağlantı yok';
  }
}

async function addFarmList() {
  const name = document.getElementById('f-name').value.trim();
  const listId = document.getElementById('f-id').value;
  const targetsStr = document.getElementById('f-targets').value.trim();
  const minInterval = parseInt(document.getElementById('f-min').value) || 45;
  const maxInterval = parseInt(document.getElementById('f-max').value) || 90;
  const dailyLimit = parseInt(document.getElementById('f-daily').value) || 0;
  if (!listId) { showAlert('Liste ID girin!', 'error'); return; }
  const targets = targetsStr.split(',').map(t => parseInt(t.trim())).filter(t => !isNaN(t));
  if (!targets.length) { showAlert('Hedef ID girin!', 'error'); return; }
  if (minInterval >= maxInterval) { showAlert('Min süre maksimumdan küçük olmalı!', 'error'); return; }
  const r = await fetch('/farmlist/add', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name: name || 'Liste ' + listId, list_id: parseInt(listId), targets, min_interval: minInterval, max_interval: maxInterval, daily_limit: dailyLimit})
  });
  const d = await r.json();
  if (d.success) { showAlert('✅ Liste eklendi!', 'success'); checkStatus(); }
}

async function pauseFarm(jobId) {
  await fetch('/farmlist/pause/' + jobId, {method: 'POST'});
  showAlert('⏸ Durduruldu', 'success'); checkStatus();
}

async function startFarm(jobId) {
  await fetch('/farmlist/start/' + jobId, {method: 'POST'});
  showAlert('▶ Başlatıldı', 'success'); checkStatus();
}

async function removeFarm(jobId) {
  await fetch('/farmlist/remove/' + jobId, {method: 'DELETE'});
  showAlert('🗑 Kaldırıldı', 'success'); checkStatus();
}

async function toggleNight(jobId) {
  await fetch('/farmlist/night/' + jobId, {method: 'POST'});
  checkStatus();
}

async function saveNight(jobId) {
  const start = document.getElementById('ns-' + jobId).value;
  const end = document.getElementById('ne-' + jobId).value;
  const count = parseInt(document.getElementById('nc-' + jobId).value) || 5;
  const r = await fetch('/farmlist/nightsave/' + jobId, {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({night_start: start, night_end: end, night_count: count})
  });
  const d = await r.json();
  if (d.success) { showAlert('🌙 Gece planı kaydedildi!', 'success'); checkStatus(); }
}

function copyFarm(jobId) {
  fetch('/status').then(r => r.json()).then(d => {
    const f = d.farm_lists.find(x => x.job_id === jobId);
    if (f) {
      document.getElementById('f-name').value = f.name + ' (kopya)';
      document.getElementById('f-id').value = f.list_id;
      document.getElementById('f-targets').value = f.targets.join(', ');
      document.getElementById('f-min').value = f.min_interval;
      document.getElementById('f-max').value = f.max_interval;
      document.getElementById('f-daily').value = f.daily_limit;
      window.scrollTo({top: 0, behavior: 'smooth'});
      showAlert('⧉ Liste forma kopyalandı!', 'success');
    }
  });
}

checkStatus();
setInterval(checkStatus, 10000);
</script>
</body>
</html>"""


def get_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    })
    return session


def login():
    try:
        wait = random.randint(3, 7)
        time.sleep(wait)
        session = get_session()
        session.headers.update({"Content-Type": "application/json"})
        resp = session.post(f"{SERVER_URL}/api/v1/auth/login", json={
            "name": USERNAME,
            "password": PASSWORD,
            "mobileOptimizations": False,
            "w": "1536:864"
        })
        if resp.status_code == 200:
            data = resp.json()
            redirect_to = data.get("redirectTo", "")
            if redirect_to:
                redirect_url = f"{SERVER_URL}{redirect_to}" if redirect_to.startswith("/") else redirect_to
                session.headers.pop("Content-Type", None)
                session.get(redirect_url)
            state["last_action"] = f"Giriş yapıldı - {datetime.now().strftime('%H:%M:%S')}"
            logger.info("✅ Giriş başarılı!")
            return session
        logger.error(f"Giriş başarısız: {resp.text[:100]}")
        return None
    except Exception as e:
        logger.error(f"Giriş hatası: {e}")
        return None


def logout(session):
    try:
        if session:
            session.headers.update({"Content-Type": "application/json"})
            session.post(f"{SERVER_URL}/api/v1/auth/logout", timeout=10)
        logger.info("✅ Çıkış yapıldı")
    except Exception as e:
        logger.error(f"Logout hatası: {e}")


def generate_night_schedule(night_start, night_end, count):
    fmt = "%H:%M"
    start_dt = datetime.strptime(night_start, fmt)
    end_dt = datetime.strptime(night_end, fmt)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    total_seconds = int((end_dt - start_dt).total_seconds())
    interval = total_seconds // count
    schedule = []
    current = start_dt
    for i in range(count):
        jitter = random.randint(-int(interval * 0.2), int(interval * 0.2))
        send_time = current + timedelta(seconds=max(0, interval * i + jitter))
        schedule.append(send_time.strftime(fmt))
    return schedule


def send_farm_list(farm_task):
    if farm_task.get("paused"):
        return

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    daily_limit = farm_task.get("daily_limit", 0)
    if daily_limit > 0:
        today_count = farm_task.get("daily_counts", {}).get(today, 0)
        if today_count >= daily_limit:
            logger.info(f"Günlük limit doldu: {farm_task['name']}")
            state["last_action"] = f"⏸ {farm_task['name']} günlük limit doldu"
            reschedule(farm_task)
            return

    session = login()
    if not session:
        reschedule(farm_task)
        return

    try:
        targets = farm_task.get("targets", [])
        payload = {
            "action": "farmList",
            "lists": [{"id": farm_task["list_id"], "targets": targets}],
            "startedAll": True
        }
        session.headers.update({"Content-Type": "application/json"})
        r = session.post(f"{SERVER_URL}/api/v1/farm-list/send", json=payload, timeout=15)
        session.headers.pop("Content-Type", None)
        logger.info(f"✅ Yağma: {farm_task['name']} - {r.status_code}")
        state["last_action"] = f"⚔️ {farm_task['name']} gönderildi - {now.strftime('%H:%M:%S')}"

        if "daily_counts" not in farm_task:
            farm_task["daily_counts"] = {}
        farm_task["daily_counts"][today] = farm_task["daily_counts"].get(today, 0) + 1
        farm_task["today_count"] = farm_task["daily_counts"][today]

    except Exception as e:
        logger.error(f"Yağma hatası: {e}")
    finally:
        logout(session)
        reschedule(farm_task)


def reschedule(farm_task):
    if farm_task.get("paused"):
        return

    now = datetime.now()
    is_night_mode = farm_task.get("night_mode", False)

    if is_night_mode:
        night_start = farm_task.get("night_start", "23:00")
        night_end = farm_task.get("night_end", "07:00")
        night_count = farm_task.get("night_count", 5)
        schedule = farm_task.get("night_schedule", [])

        if not schedule:
            schedule = generate_night_schedule(night_start, night_end, night_count)
            farm_task["night_schedule"] = schedule

        # Sonraki gönderimi bul
        fmt = "%H:%M"
        next_run = None
        for t in schedule:
            send_dt = datetime.strptime(t, fmt).replace(year=now.year, month=now.month, day=now.day)
            if send_dt <= now:
                send_dt += timedelta(days=1)
            if next_run is None or send_dt < next_run:
                next_run = send_dt

        if next_run is None:
            next_run = now + timedelta(hours=1)
    else:
        min_interval = farm_task.get("min_interval", 45)
        max_interval = farm_task.get("max_interval", 90)
        wait = random.randint(min_interval * 60, max_interval * 60)
        next_run = now + timedelta(seconds=wait)

    farm_task["next_run"] = next_run.isoformat()
    farm_task["next_seconds"] = int((next_run - now).total_seconds())

    try:
        scheduler.remove_job(farm_task["job_id"])
    except:
        pass
    scheduler.add_job(send_farm_list, "date", run_date=next_run, args=[farm_task], id=farm_task["job_id"])
    logger.info(f"Sonraki: {farm_task['name']} → {next_run.strftime('%H:%M:%S')}")


def update_timers():
    now = datetime.now()
    for f in state["farm_lists"]:
        if f.get("next_run") and not f.get("paused"):
            try:
                nr = datetime.fromisoformat(f["next_run"])
                f["next_seconds"] = max(0, int((nr - now).total_seconds()))
            except:
                pass


scheduler.add_job(update_timers, "interval", seconds=5, id="timer_update")


@app.route("/")
def index():
    return render_template_string(HTML_PANEL)


@app.route("/status")
def status():
    update_timers()
    return jsonify({"farm_lists": state["farm_lists"], "last_action": state["last_action"]})


@app.route("/farmlist/add", methods=["POST"])
def add_farm_list():
    data = request.json
    job_id = f"farm_{data['list_id']}_{int(time.time())}"
    farm_task = {
        "job_id": job_id,
        "name": data.get("name", "Liste"),
        "list_id": data["list_id"],
        "targets": data.get("targets", []),
        "min_interval": data.get("min_interval", 45),
        "max_interval": data.get("max_interval", 90),
        "daily_limit": data.get("daily_limit", 0),
        "night_mode": False,
        "night_start": "23:00",
        "night_end": "07:00",
        "night_count": 5,
        "night_schedule": [],
        "paused": False,
        "today_count": 0,
        "next_seconds": 0
    }
    state["farm_lists"].append(farm_task)
    send_farm_list(farm_task)
    return jsonify({"success": True, "job_id": job_id})


@app.route("/farmlist/pause/<job_id>", methods=["POST"])
def pause_farm(job_id):
    for f in state["farm_lists"]:
        if f["job_id"] == job_id:
            f["paused"] = True
            try:
                scheduler.remove_job(job_id)
            except:
                pass
    return jsonify({"success": True})


@app.route("/farmlist/start/<job_id>", methods=["POST"])
def start_farm(job_id):
    for f in state["farm_lists"]:
        if f["job_id"] == job_id:
            f["paused"] = False
            reschedule(f)
    return jsonify({"success": True})


@app.route("/farmlist/night/<job_id>", methods=["POST"])
def toggle_night(job_id):
    for f in state["farm_lists"]:
        if f["job_id"] == job_id:
            f["night_mode"] = not f.get("night_mode", False)
            if f["night_mode"]:
                f["night_schedule"] = generate_night_schedule(
                    f.get("night_start", "23:00"),
                    f.get("night_end", "07:00"),
                    f.get("night_count", 5)
                )
            else:
                f["night_schedule"] = []
            if not f.get("paused"):
                reschedule(f)
    return jsonify({"success": True})


@app.route("/farmlist/nightsave/<job_id>", methods=["POST"])
def save_night(job_id):
    data = request.json
    for f in state["farm_lists"]:
        if f["job_id"] == job_id:
            f["night_start"] = data.get("night_start", "23:00")
            f["night_end"] = data.get("night_end", "07:00")
            f["night_count"] = data.get("night_count", 5)
            f["night_schedule"] = generate_night_schedule(
                f["night_start"], f["night_end"], f["night_count"]
            )
            if not f.get("paused"):
                reschedule(f)
    return jsonify({"success": True})


@app.route("/farmlist/remove/<job_id>", methods=["DELETE"])
def remove_farm(job_id):
    state["farm_lists"] = [f for f in state["farm_lists"] if f["job_id"] != job_id]
    try:
        scheduler.remove_job(job_id)
    except:
        pass
    return jsonify({"success": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
