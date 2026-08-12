from flask import Flask, render_template_string, jsonify
import requests
import base64
import uuid
import time
import random
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# Данные из переменных окружения (безопасно!)
CLIENT_ID = os.environ.get("GIGACHAT_CLIENT_ID", "019ff6e9-d665-7748-b6e5-6a82ec00138a")
AUTH_KEY = os.environ.get("GIGACHAT_AUTH_KEY")
SCOPE = "GIGACHAT_API_PERS"
OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

_access_token = None
_token_expires_at = 0

def get_access_token():
    global _access_token, _token_expires_at
    if _access_token and time.time() < _token_expires_at - 60:
        return _access_token
    
    credentials = base64.b64encode(f"{CLIENT_ID}:{AUTH_KEY}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
        "RqUID": str(uuid.uuid4()),
        "Accept": "application/json"
    }
    data = f"scope={SCOPE}"
    
    response = requests.post(OAUTH_URL, headers=headers, data=data, timeout=30, verify=False)
    response.raise_for_status()
    result = response.json()
    _access_token = result["access_token"]
    _token_expires_at = result.get("expires_at", time.time() + 1800)
    return _access_token

FALLBACK_WISHES = [
    "Пусть сегодня каждый момент будет как теплый лучик солнца, который нежно касается щеки.",
    "Сегодня твой день - позволь себе быть немного счастливее, чем вчера.",
    "Пусть встречи сегодня будут теплыми, а расставания - легкими.",
    "Найди сегодня минутку, чтобы посмотреть на небо - оно улыбается тебе.",
    "Пусть сегодняшний день принесет тебе маленькое чудо, которое изменит все.",
    "Ты - главный герой своей истории. Сделай сегодняшнюю главу особенной.",
    "Пусть сегодня все сложится так, как ты мечтаешь, а если нет - значит, мечтаешь недостаточно смело.",
    "Сегодня - идеальный день, чтобы начать верить в себя чуть сильнее.",
    "Пусть твой путь сегодня усыпан приятными сюрпризами и добрыми словами.",
    "Сегодня Вселенная готовит для тебя что-то прекрасное - будь готов заметить это."
]

WISH_PROMPT = """Сгенерируй одно короткое позитивное пожелание на день. 

Требования:
- Длина: 1-2 предложения
- Тон: теплый, вдохновляющий, добрый
- Тематика: хороший день, успех, внутренняя гармония, мотивация, благодарность
- Без шаблонных фраз типа "хорошего дня", "удачи", "всего наилучшего"
- Каждое пожелание должно быть уникальным и неожиданным
- Используй метафоры, образы природы, легкую философию
- Без восклицательных знаков в конце - мягкий, размышляющий тон
- Ответ ТОЛЬКО текст пожелания, без кавычек, без пояснений, без приветствий"""

def generate_wish():
    try:
        token = get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "model": "GigaChat",
            "messages": [{"role": "user", "content": WISH_PROMPT}],
            "temperature": 0.9,
            "max_tokens": 120,
            "repetition_penalty": 1.1
        }
        
        response = requests.post(CHAT_URL, headers=headers, json=payload, timeout=30, verify=False)
        
        if response.status_code == 401:
            global _access_token
            _access_token = None
            token = get_access_token()
            headers["Authorization"] = f"Bearer {token}"
            response = requests.post(CHAT_URL, headers=headers, json=payload, timeout=30, verify=False)
            
        response.raise_for_status()
        result = response.json()
        wish = result["choices"][0]["message"]["content"].strip().strip('"').strip("'")
        return " ".join(wish.split())
        
    except Exception as e:
        print(f"Ошибка API: {e}")
        return random.choice(FALLBACK_WISHES)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Пожелание на день</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #ffeaa7, #fab1a0, #fd79a8, #e17055, #fdcb6e);
            background-size: 400% 400%;
            animation: gradientShift 15s ease infinite;
            padding: 20px;
        }
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .container { text-align: center; max-width: 600px; width: 100%; z-index: 2; }
        .title { font-size: 2.5rem; font-weight: 300; color: rgba(255,255,255,0.95); margin-bottom: 10px; text-shadow: 0 2px 20px rgba(0,0,0,0.1); }
        .subtitle { font-size: 1rem; color: rgba(255,255,255,0.8); margin-bottom: 50px; font-weight: 300; }
        .wish-btn {
            background: rgba(255,255,255,0.95); border: none; padding: 20px 60px;
            font-size: 1.3rem; font-weight: 500; color: #2d3436; border-radius: 50px;
            cursor: pointer; box-shadow: 0 10px 40px rgba(0,0,0,0.15);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            font-family: inherit; position: relative;
        }
        .wish-btn:hover { transform: translateY(-3px) scale(1.05); box-shadow: 0 15px 50px rgba(0,0,0,0.2); }
        .wish-btn:active { transform: translateY(0) scale(0.97); }
        .wish-btn:disabled { opacity: 0.7; cursor: not-allowed; transform: none; }
        .spinner { display: none; width: 20px; height: 20px; border: 2px solid #ddd; border-top-color: #e17055; border-radius: 50%; animation: spin 0.8s linear infinite; margin-left: 10px; vertical-align: middle; }
        .wish-btn.loading .btn-text { display: none; }
        .wish-btn.loading .spinner { display: inline-block; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .wish-card {
            margin-top: 40px; background: rgba(255,255,255,0.85); backdrop-filter: blur(20px);
            border-radius: 24px; padding: 35px 40px; box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            opacity: 0; transform: translateY(30px) scale(0.95);
            transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1); position: relative; overflow: hidden;
        }
        .wish-card.visible { opacity: 1; transform: translateY(0) scale(1); }
        .wish-card::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 4px; background: linear-gradient(90deg, #fd79a8, #e17055, #fdcb6e); border-radius: 24px 24px 0 0; }
        .wish-text { font-size: 1.35rem; line-height: 1.7; color: #2d3436; font-weight: 400; font-style: italic; }
        .wish-text::before { content: "\\201C"; font-size: 3rem; color: #fd79a8; opacity: 0.3; line-height: 0; vertical-align: -20px; margin-right: 5px; }
        .wish-actions { margin-top: 20px; display: flex; gap: 10px; justify-content: center; opacity: 0; transition: opacity 0.4s ease 0.3s; }
        .wish-card.visible .wish-actions { opacity: 1; }
        .action-btn { background: rgba(255,255,255,0.7); border: 1px solid rgba(0,0,0,0.08); padding: 8px 16px; border-radius: 20px; font-size: 0.85rem; color: #636e72; cursor: pointer; transition: all 0.3s ease; font-family: inherit; }
        .action-btn:hover { background: rgba(255,255,255,1); color: #e17055; transform: translateY(-1px); }
        .particles { position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1; overflow: hidden; }
        .particle { position: absolute; width: 6px; height: 6px; background: rgba(255,255,255,0.6); border-radius: 50%; animation: float 8s infinite ease-in-out; }
        @keyframes float { 0%,100% { transform: translateY(100vh) rotate(0deg); opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { transform: translateY(-10vh) rotate(720deg); opacity: 0; } }
        .footer { position: fixed; bottom: 20px; left: 0; right: 0; text-align: center; color: rgba(255,255,255,0.6); font-size: 0.85rem; font-weight: 300; z-index: 2; }
        .heart { color: #ff6b6b; animation: heartbeat 1.5s ease-in-out infinite; display: inline-block; }
        @keyframes heartbeat { 0%,100% { transform: scale(1); } 50% { transform: scale(1.15); } }
        .sparkle { position: absolute; pointer-events: none; animation: sparkleAnim 1s ease-out forwards; font-size: 1.5rem; z-index: 10; }
        @keyframes sparkleAnim { 0% { transform: translate(0,0) scale(0) rotate(0deg); opacity: 1; } 100% { transform: translate(var(--tx),var(--ty)) scale(1.5) rotate(180deg); opacity: 0; } }
        @media (max-width: 480px) { .title { font-size: 2rem; } .wish-btn { padding: 18px 45px; font-size: 1.1rem; } .wish-card { padding: 25px 20px; } .wish-text { font-size: 1.15rem; } }
    </style>
</head>
<body>
    <div class="particles" id="particles"></div>
    <div class="container">
        <h1 class="title">Пожелание на день</h1>
        <p class="subtitle">Нажми на кнопку - и получи свою порцию вдохновения</p>
        <button class="wish-btn" id="wishBtn" onclick="getWish(event)">
            <span class="btn-text">Пожелание</span>
            <span class="spinner"></span>
        </button>
        <div class="wish-card" id="wishCard">
            <p class="wish-text" id="wishText"></p>
            <div class="wish-actions">
                <button class="action-btn" onclick="copyWish()">Копировать</button>
                <button class="action-btn" onclick="shareWish()">Поделиться</button>
            </div>
        </div>
    </div>
    <div class="footer">Сделано с <span class="heart">❤️</span> для хорошего дня</div>
    <script>
        function createParticles() { const c=document.getElementById('particles'); for(let i=0;i<20;i++){const p=document.createElement('div');p.className='particle';p.style.left=Math.random()*100+'%';p.style.animationDelay=Math.random()*8+'s';p.style.animationDuration=(6+Math.random()*6)+'s';p.style.width=p.style.height=(3+Math.random()*6)+'px';c.appendChild(p);}} createParticles();
        function createSparkles(x,y){const em=['✨','⭐','🌟','💫','🔆'];for(let i=0;i<8;i++){const s=document.createElement('div');s.className='sparkle';s.textContent=em[Math.floor(Math.random()*em.length)];s.style.left=x+'px';s.style.top=y+'px';const a=(Math.PI*2*i)/8,d=50+Math.random()*80;s.style.setProperty('--tx',Math.cos(a)*d+'px');s.style.setProperty('--ty',Math.sin(a)*d+'px');document.body.appendChild(s);setTimeout(()=>s.remove(),1000);}}
        async function getWish(e){const b=document.getElementById('wishBtn'),c=document.getElementById('wishCard'),t=document.getElementById('wishText');const r=b.getBoundingClientRect();createSparkles(r.left+r.width/2,r.top+r.height/2);b.disabled=true;b.classList.add('loading');c.classList.remove('visible');try{const res=await fetch('/wish',{method:'POST',headers:{'Content-Type':'application/json'}});if(!res.ok)throw new Error('err');const data=await res.json();t.textContent=data.wish;setTimeout(()=>c.classList.add('visible'),200);}catch(err){t.textContent='Связь с Вселенной нарушена, попробуйте ещё раз';c.classList.add('visible');}finally{b.disabled=false;b.classList.remove('loading');}}
        function copyWish(){const t=document.getElementById('wishText').textContent;navigator.clipboard.writeText(t).then(()=>{const b=event.target,o=b.textContent;b.textContent='Скопировано!';setTimeout(()=>b.textContent=o,2000);});}
        function shareWish(){const t=document.getElementById('wishText').textContent;if(navigator.share){navigator.share({title:'Моё пожелание на день',text:t});}else{copyWish();}}
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/wish", methods=["POST"])
def wish():
    return jsonify({"wish": generate_wish()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
