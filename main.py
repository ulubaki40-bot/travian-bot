import os
import time
import math
import logging
import requests
from flask import Flask, request, jsonify, render_template_string
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
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
    "session": None,
    "farm_lists": [],
    "logged_in": False,
    "last_action": "",
    "last_attack_count": 0
}

HTML_PANEL = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Travian Bot</title>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  :root{--gold:#f5c842;--dark:#0a0a14;--card:#111122;--border:rgba(245,200,66,0.2);--red:#e05555;--green:#4ecb71;--text:#d4c9a8;--muted:#6b6b8a}
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#06060e;color:var(--text);font-family:'Rajdhani',sans-serif;min-height:100vh;padding-bottom:40px}
  header{background:linear-gradient(180deg,#1a0a00,#0a0a14);border-bottom:1px solid var(--border);padding:18px 16px 14px;position:sticky;top:0;z-index:100;display:flex;justify-content:space-between;align-items:center}
  .logo{font-family:'Cinzel',serif;font-size:22px;color:var(--gold);letter-spacing:2px}
  .logo span{font-size:12px;display:block;color:var(--muted);letter-spacing:4px;font-family:'Rajdhani',sans-serif;font-weight:600}
  .dot{width:10px;height:10px;border-radius:50%;background:var(--red);display:inline-block;margin-right:6px}
  .dot.on{background:var(--green)}
  .container{max-width:480px;margin:0 auto;padding:16px}
  .stitle{font-family:'Cinzel',serif;font-size:13px;color:var(--gold);letter-spacing:3px;text-transform:uppercase;margin:24px 0 12px;display:flex;align-items:center;gap:10px}
  .stitle::after{content:'';flex:1;height:1px;background:var(--border)}
  .card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:12px}
  input,select{width:100%;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;color:var(--text);padding:11px 14px;font-size:15px;font-family:'Rajdhani',sans-serif;font-weight:600;outline:none;margin-bottom:10px}
  input:focus,select:focus{border-color:var(--gold)}
  select option{background:#1a1a30}
  .btn{width:100%;padding:13px;border:none;border-radius:10px;font-family:'Cinzel',serif;font-size:14px;font-weight:700;cursor:pointer;letter-spacing:1px}
  .bg{background:linear-gradient(135deg,#f5c842,#c9962a);color:#0a0a14}
  .br{background:rgba(224,85,85,0.15);border:1px solid rgba(224,85,85,0.4);color:var(--red);padding:8px;width:auto;font-size:12px;border-radius:8px}
  .qi{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:12px 14px;margin-bottom:8px;display:flex;align-items:center}
  .qn{width:36px;height:36px;border-radius:50%;background:var(--gold);color:#0a0a14;font-weight:700;font-size:11px;display:flex;align-items:center;justify-content:center;margin-right:10px;flex-shrink:0}
  .bn{font-weight:700;font-size:15px;color:#fff}
  .bd{font-size:12px;color:var(--muted);margin-top:2px}
  .tg{display:flex;gap:8px;margin-bottom:4px}
  .tab{flex:1;padding:10px;text-align:center;border:1px solid var(--border);border-radius:10px;font-family:'Cinzel',serif;font-size:12px;color:var(--muted);cursor:pointer;background:transparent;letter-spacing:1px}
  .tab.active{background:rgba(245,200,66,0.1);border-color:var(--gold);color:var(--gold)}
  .tc{display:none}.tc.active{display:block}
  .empty{text-align:center;color:var(--muted);padding:24px;font-size:14px}
  .lbl{font-size:12px;color:var(--muted);margin-bottom:4px;font-weight:600;letter-spacing:1px;display:block}
  .alert{padding:12px 16px;border-radius:10px;font-size:14px;font-weight:600;margin-bottom:12px;display:none}
  .as{background:rgba(78,203,113,0.15);border:1px solid rgba(78,203,113,0.3);color:var(--green)}
  .ae{background:rgba(224,85,85,0.15);border:1px solid rgba(224,85,85,0.3);color:var(--red)}
  .fi{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:12px 14px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center}
  .fn{font-weight:700;font-size:15px;color:#fff}
  .fd{font-size:12px;color:var(--muted);margin-top:2px}
  .last{font-size:12px;color:var(--muted);text-align:center;padding:8px;background:rgba(255,255,255,0.02);border-radius:8px;margin-bottom:12px}
  .loading{text-align:center;color:var(--gold);padding:24px;font-size:14px}
</style>
</head>
<body>
<header>
  <div class="logo">⚔️ TRAVIAN<span>BOT PANELİ</span></div>
  <div style="display:flex;align-items:center"><span class="dot" id="dot"></span><span id="stxt">Bağlanıyor...</span></div>
</header>
<div class="container">
  <div id="alert" class="alert"></div>
  <div class="last" id="last"></div>
  <div class="tg">
    <button class="tab active" onclick="switchTab('raids',this)">⚔️ YAĞMA</button>
    <button class="tab" onclick="switchTab('oasis',this)">🌿 VAHALAR</button>
  </div>

  <div class="tc active" id="tab-raids">
    <div class="stitle">Yağma Listesi Ekle</div>
    <div class="card">
      <label class="lbl">Liste Adı (hatırlatmak için)</label>
      <input type="text" id="farm-name" placeholder="Örnek: lejyoner">
      <label class="lbl">Liste ID (Travian'daki ID)</label>
      <input type="number" id="farm-id" placeholder="Örnek: 1890">
      <label class="lbl">Hedef ID'leri (virgülle ayır)</label>
      <input type="text" id="farm-targets" placeholder="55950,55945,55955,...">
      <label class="lbl">Minimum bekleme süresi (dakika)</label>
      <input type="number" id="farm-min" value="60" placeholder="Örnek: 60">
      <label class="lbl">Maksimum bekleme süresi (dakika)</label>
      <input type="number" id="farm-max" value="180" placeholder="Örnek: 180">
      <label class="lbl">Günlük maksimum gönderim (0 = sınırsız)</label>
      <input type="number" id="farm-daily" value="0" placeholder="Örnek: 6">
      <button class="btn bg" onclick="addFarmList()">⚔️ YAĞMA LİSTESİ EKLE</button>
    </div>
    <div class="stitle">Aktif Yağma Listeleri</div>
    <div id="farm-list"><div class="empty">Aktif yağma listesi yok</div></div>
  </div>

  <div class="tc" id="tab-oasis">
    <div class="stitle">Yakın Vahalar</div>
    <div class="card">
      <label class="lbl">Köy X Koordinatı</label>
      <input type="number" id="oasis-x" value="-17">
      <label class="lbl">Köy Y Koordinatı</label>
      <input type="number" id="oasis-y" value="49">
      <label class="lbl">Yarıçap (birim, max 70)</label>
      <input type="number" id="oasis-radius" value="70">
      <button class="btn bg" onclick="loadOasis()">🔍 VAHALARI GETİR</button>
    </div>
    <div class="stitle">Vaha Listesi</div>
    <div id="oasis-list"><div class="empty">Henüz yüklenmedi — butona bas!</div></div>
  </div>
</div>
<script>
  function switchTab(tab,el){document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.tc').forEach(t=>t.classList.remove('active'));document.getElementById('tab-'+tab).classList.add('active');el.classList.add('active')}
  function showAlert(msg,type){const el=document.getElementById('alert');el.textContent=msg;el.className='alert '+(type==='success'?'as':'ae');el.style.display='block';setTimeout(()=>el.style.display='none',3000)}
  async function checkStatus(){
    try{
      const r=await fetch('/status');const d=await r.json();
      document.getElementById('dot').className='dot'+(d.logged_in?' on':'');
      document.getElementById('stxt').textContent=d.logged_in?'Çevrimiçi':'Giriş yapılmadı';
      if(d.last_action)document.getElementById('last').textContent='🕐 '+d.last_action;
      renderFarmLists(d.farm_lists);
    }catch(e){document.getElementById('stxt').textContent='Bağlantı yok'}
  }
  function renderFarmLists(lists){
    const el=document.getElementById('farm-list');
    if(!lists||!lists.length){el.innerHTML='<div class="empty">Aktif yağma listesi yok</div>';return}
    el.innerHTML=lists.map(f=>`<div class="fi"><div><div class="fn">⚔️ ${f.name}</div><div class="fd">ID: ${f.list_id} · ${f.min_interval}-${f.max_interval} dk arası rastgele · Günlük: ${f.daily_limit||'Sınırsız'}</div></div><button class="br" onclick="removeFarmList('${f.job_id}')">Durdur</button></div>`).join('')
  }
  async function addFarmList(){
    const name=document.getElementById('farm-name').value.trim();
    const listId=document.getElementById('farm-id').value;
    if(!listId){showAlert('Liste ID girin!','error');return}
    const targetsStr=document.getElementById('farm-targets').value.trim();
    const targets=targetsStr.split(',').map(t=>parseInt(t.trim())).filter(t=>!isNaN(t));
    if(!targets.length){showAlert("Hedef ID lerini girin!","error");return}
    const minInterval=parseInt(document.getElementById('farm-min').value)||60;
    const maxInterval=parseInt(document.getElementById('farm-max').value)||180;
    const dailyLimit=parseInt(document.getElementById('farm-daily').value)||0;
    if(minInterval>=maxInterval){showAlert("Minimum sure maksimumdan kucuk olmali!","error");return}
    try{
      const r=await fetch('/farmlist/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:name||'Liste '+listId,list_id:parseInt(listId),targets,min_interval:minInterval,max_interval:maxInterval,daily_limit:dailyLimit})});
      const d=await r.json();
      if(d.success){showAlert('⚔️ Yağma listesi eklendi!','success');checkStatus()}
    }catch(e){showAlert('❌ Hata: '+e.message,'error')}
  }
  async function removeFarmList(jobId){
    await fetch('/farmlist/remove/'+jobId,{method:'DELETE'});
    showAlert('Yağma listesi durduruldu','success');checkStatus()
  }
  const ANIMAL_NAMES={31:'🐭 Sıçan',32:'🕷️ Örümcek',33:'🐍 Yılan',34:'🦇 Yarasa',35:'🐗 Yaban Domuzu',36:'🐺 Kurt',37:'🐻 Ayı',38:'🐊 Timsah',39:'🐯 Kaplan',40:'🐘 Fil',41:'🐺 Kurt Sürüsü'};
  async function loadOasis(){
    const x=document.getElementById('oasis-x').value;
    const y=document.getElementById('oasis-y').value;
    const radius=document.getElementById('oasis-radius').value;
    const el=document.getElementById('oasis-list');
    el.innerHTML='<div class="loading">⏳ Yükleniyor... Bu biraz sürebilir.</div>';
    try{
      const res=await fetch(`/oasis/nearby?x=${x}&y=${y}&radius=${radius}`);
      const d=await res.json();
      if(!d.success){el.innerHTML='<div class="empty">❌ Hata: '+d.error+'</div>';return}
      if(!d.oasis.length){el.innerHTML='<div class="empty">Yakında hayvan bulunan vaha yok</div>';return}
      el.innerHTML=`<div style="color:var(--muted);font-size:12px;text-align:center;margin-bottom:12px">${d.count} vaha bulundu</div>`+d.oasis.map(o=>{
        const animals=o.animals.map(a=>`${ANIMAL_NAMES[a.id]||'Hayvan'}: <b style="color:#fff">${a.count}</b>`).join(' &nbsp;');
        return `<div class="qi"><div class="qn">${o.dist}</div><div><div class="bn">(${o.x}|${o.y})</div><div class="bd">${animals}</div></div></div>`;
      }).join('');
    }catch(e){el.innerHTML='<div class="empty">❌ Bağlantı hatası</div>'}
  }
  checkStatus();setInterval(checkStatus,15000);
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
        session = get_session()
        session.headers.update({"Content-Type": "application/json"})
        resp = session.post(f"{SERVER_URL}/api/v1/auth/login", json={
            "name": USERNAME,
            "password": PASSWORD,
            "mobileOptimizations": False,
            "w": "1536:864"
        })
        logger.info(f"Login: {resp.status_code} - {resp.text[:200]}")

        if resp.status_code == 200:
            data = resp.json()
            redirect_to = data.get("redirectTo", "")
            if redirect_to:
                redirect_url = f"{SERVER_URL}{redirect_to}" if redirect_to.startswith("/") else redirect_to
                session.headers.pop("Content-Type", None)
                r2 = session.get(redirect_url)
                logger.info(f"Redirect: {r2.status_code} - {r2.url}")

            state["session"] = session
            state["logged_in"] = True
            state["last_action"] = f"Giriş başarılı - {datetime.now().strftime('%H:%M:%S')}"
            logger.info("✅ Giris basarili!")
            return True

        logger.error(f"Giris basarisiz: {resp.text[:200]}")
        return False
    except Exception as e:
        logger.error(f"Giris hatasi: {e}")
        return False

def logout():
    try:
        if state["session"]:
            session = state["session"]
            session.headers.update({"Content-Type": "application/json"})
            session.post(f"{SERVER_URL}/api/v1/auth/logout", timeout=10)
            session.headers.pop("Content-Type", None)
        state["logged_in"] = False
        state["session"] = None
        logger.info("✅ Cıkıs yapıldı")
    except Exception as e:
        logger.error(f"Logout hatasi: {e}")
        state["logged_in"] = False
        state["session"] = None

def ensure_logged_in():
    if not state["logged_in"] or state["session"] is None:
        return login()
    try:
        r = state["session"].get(f"{SERVER_URL}/dorf1.php", timeout=10)
        if "login" in r.url.lower():
            return login()
        return True
    except:
        return login()

def send_telegram(message):
    try:
        token = os.environ.get("TELEGRAM_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            return
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=10)
        logger.info(f"Telegram bildirimi gonderildi")
    except Exception as e:
        logger.error(f"Telegram hatasi: {e}")

def check_attacks():
    try:
        if not ensure_logged_in():
            return
        session = state["session"]
        r = session.get(f"{SERVER_URL}/dorf1.php", timeout=15)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        attacks = soup.find_all(class_=lambda x: x and "attack" in str(x).lower())
        attack_count = len(attacks)
        if attack_count > state.get("last_attack_count", 0):
            send_telegram(f"⚔️ SALDIRI GELİYOR!\n🚨 Travian'ı hemen kontrol et!\n⏰ {datetime.now().strftime('%H:%M:%S')}")
            logger.info(f"Saldiri bildirimi gonderildi!")
        state["last_attack_count"] = attack_count
    except Exception as e:
        logger.error(f"Saldiri kontrol hatasi: {e}")

def send_farm_list(farm_task):
    import random
    try:
        daily_limit = farm_task.get("daily_limit", 0)
        if daily_limit > 0:
            today = datetime.now().strftime("%Y-%m-%d")
            daily_count = farm_task.get("daily_counts", {}).get(today, 0)
            if daily_count >= daily_limit:
                logger.info(f"Gunluk limit doldu: {farm_task['name']} ({daily_count}/{daily_limit})")
                state["last_action"] = f"⏸️ {farm_task['name']} günlük limit doldu - {datetime.now().strftime('%H:%M:%S')}"
                return

        if not ensure_logged_in():
            return

        session = state["session"]
        targets = farm_task.get("targets", [])
        if not targets:
            logger.warning("Hedefler alinamadi!")
            return

        payload = {
            "action": "farmList",
            "lists": [{"id": farm_task["list_id"], "targets": targets}],
            "startedAll": True
        }
        session.headers.update({"Content-Type": "application/json"})
        r = session.post(f"{SERVER_URL}/api/v1/farm-list/send", json=payload, timeout=15)
        session.headers.pop("Content-Type", None)
        logger.info(f"✅ Yagma gonderildi: {farm_task['name']} - status {r.status_code}")
        state["last_action"] = f"⚔️ {farm_task['name']} gönderildi - {datetime.now().strftime('%H:%M:%S')}"

        logout()
        logger.info("Yagma sonrası cıkıs yapıldı")

        today = datetime.now().strftime("%Y-%m-%d")
        if "daily_counts" not in farm_task:
            farm_task["daily_counts"] = {}
        farm_task["daily_counts"][today] = farm_task["daily_counts"].get(today, 0) + 1

        min_interval = farm_task.get("min_interval", 60)
        max_interval = farm_task.get("max_interval", 180)
        next_minutes = random.randint(min_interval, max_interval)
        logger.info(f"Sonraki gonderim {next_minutes} dakika sonra")
        state["last_action"] += f" (sonraki: {next_minutes}dk)"

        import datetime as dt
        next_run = dt.datetime.now() + dt.timedelta(minutes=next_minutes)
        try:
            scheduler.remove_job(farm_task["job_id"])
        except:
            pass
        scheduler.add_job(
            send_farm_list,
            "date",
            run_date=next_run,
            args=[farm_task],
            id=farm_task["job_id"]
        )

    except Exception as e:
        logger.error(f"Yagma listesi hatasi: {e}")
        state["last_action"] = f"❌ Yağma hatası: {str(e)[:60]}"

scheduler.add_job(check_attacks, "interval", minutes=3, id="attack_check")

@app.route("/")
def index():
    return render_template_string(HTML_PANEL)

@app.route("/status")
def status():
    return jsonify({
        "logged_in": state["logged_in"],
        "farm_lists": state["farm_lists"],
        "last_action": state["last_action"]
    })

@app.route("/farmlist/add", methods=["POST"])
def add_farm_list():
    data = request.json
    name = data.get("name", "Liste")
    list_id = data.get("list_id")
    targets = data.get("targets", [])
    min_interval = data.get("min_interval", 60)
    max_interval = data.get("max_interval", 180)
    daily_limit = data.get("daily_limit", 0)

    if not list_id or not targets:
        return jsonify({"success": False, "error": "list_id ve targets gerekli"})

    job_id = f"farm_{list_id}_{int(time.time())}"
    farm_task = {
        "job_id": job_id,
        "name": name,
        "list_id": list_id,
        "targets": targets,
        "min_interval": min_interval,
        "max_interval": max_interval,
        "daily_limit": daily_limit
    }

    state["farm_lists"].append(farm_task)
    send_farm_list(farm_task)

    return jsonify({"success": True, "job_id": job_id})

@app.route("/farmlist/remove/<job_id>", methods=["DELETE"])
def remove_farm_list(job_id):
    state["farm_lists"] = [f for f in state["farm_lists"] if f["job_id"] != job_id]
    try:
        scheduler.remove_job(job_id)
    except:
        pass
    return jsonify({"success": True})

@app.route("/oasis/nearby")
def get_nearby_oasis():
    try:
        if not ensure_logged_in():
            return jsonify({"success": False, "error": "Giriş yapılamadı"})

        session = state["session"]
        player_x = int(request.args.get("x", -17))
        player_y = int(request.args.get("y", 49))
        radius = min(int(request.args.get("radius", 70)), 70)

        oasis_list = []
        seen = set()
        step = 7

        x_range = range(player_x - radius, player_x + radius + step, step)
        y_range = range(player_y - radius, player_y + radius + step, step)

        for cx in x_range:
            for cy in y_range:
                try:
                    r = session.get(
                        f"{SERVER_URL}/api/v1/map/info?x={cx}&y={cy}",
                        timeout=10
                    )
                    if r.status_code != 200:
                        continue
                    data = r.json()
                    tiles = data.get("data", {}).get("tiles", [])
                    for tile in tiles:
                        tx = tile.get("x", 0)
                        ty = tile.get("y", 0)
                        key = f"{tx}_{ty}"
                        if key in seen:
                            continue
                        seen.add(key)

                        cell_type = tile.get("type", 0)
                        if cell_type != 3:
                            continue

                        dist = math.sqrt((tx - player_x) ** 2 + (ty - player_y) ** 2)
                        if dist > radius:
                            continue

                        animals = tile.get("units", [])
                        if not animals:
                            continue

                        animal_list = []
                        for unit in animals:
                            unit_id = unit.get("unitId", 0)
                            count = unit.get("count", 0)
                            if count > 0:
                                animal_list.append({"id": unit_id, "count": count})

                        if animal_list:
                            oasis_list.append({
                                "x": tx,
                                "y": ty,
                                "dist": round(dist, 1),
                                "animals": animal_list
                            })
                except:
                    continue

        # Logout after oasis check
        logout()

        oasis_list.sort(key=lambda o: o["dist"])
        return jsonify({"success": True, "oasis": oasis_list, "count": len(oasis_list)})

    except Exception as e:
        logger.error(f"Oasis hatasi: {e}")
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Travian Bot baslatiliyor...")
    app.run(host="0.0.0.0", port=port)
