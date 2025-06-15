from flask import Flask, render_template_string, request, send_file, jsonify, session
import requests
from bs4 import BeautifulSoup
import io
import time
import re
from langdetect import detect, LangDetectException
from urllib.parse import urlparse, urljoin
import os
import openai

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for session

HTML_FORM = '''
<!doctype html>
<html lang="en">
<head>
<title>Flask Bot - Web Analyzer & Chat</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
<style>
  body {
    font-family: 'Montserrat', Arial, sans-serif;
    background: linear-gradient(120deg, #232526 0%, #414345 100%);
    color: #fff;
    min-height: 100vh;
    margin: 0;
    padding: 0;
  }
  .overlay {
    background: rgba(0,0,0,0.75);
    min-height: 100vh;
    padding: 40px 0 60px 0;
  }
  .container {
    max-width: 700px;
    margin: 40px auto;
    background: rgba(255,255,255,0.10);
    border-radius: 18px;
    box-shadow: 0 8px 32px 0 rgba(31,38,135,0.37);
    padding: 32px 36px 36px 36px;
    backdrop-filter: blur(6px);
    position: relative;
  }
  h2, h3 {
    color: #ffd700;
    margin-top: 0;
    font-weight: 700;
    letter-spacing: 1px;
  }
  form {
    margin-bottom: 28px;
  }
  input[type="text"], select {
    padding: 12px;
    border-radius: 8px;
    border: none;
    width: 60%;
    margin-right: 10px;
    font-size: 1em;
    background: #232526;
    color: #ffd700;
    outline: none;
    box-shadow: 0 2px 8px #0002;
  }
  input[type="submit"], button {
    padding: 12px 22px;
    border-radius: 8px;
    border: none;
    background: #ffd700;
    color: #232526;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.2s, color 0.2s;
    font-size: 1em;
    box-shadow: 0 2px 8px #0002;
  }
  input[type="submit"]:hover, button:hover {
    background: #fff;
    color: #232526;
  }
  .warning { color: #ff6347; font-weight: bold; }
  .section {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #ffd70033;
  }
  .icon {
    margin-right: 8px;
    color: #ffd700;
    font-size: 1.1em;
    vertical-align: middle;
  }
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  .floating-chat-btn {
    position: fixed;
    bottom: 32px;
    right: 32px;
    width: 64px;
    height: 64px;
    background: #10a37f;
    border-radius: 50%;
    box-shadow: 0 4px 24px rgba(0,0,0,0.25);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 1000;
    border: 3px solid #fff;
    transition: box-shadow 0.2s;
  }
  .floating-chat-btn:hover {
    box-shadow: 0 8px 32px rgba(0,0,0,0.35);
  }
  .floating-chat-btn svg {
    width: 38px;
    height: 38px;
    display: block;
  }
  .floating-chat-window {
    position: fixed;
    bottom: 110px;
    right: 32px;
    width: 370px;
    background: #343541;
    border-radius: 18px;
    box-shadow: 0 8px 32px 0 rgba(31,38,135,0.37);
    padding: 0;
    z-index: 1001;
    display: none;
    flex-direction: column;
    animation: fadeIn 0.4s;
    border: 1.5px solid #10a37f;
  }
  .floating-chat-window.open {
    display: flex;
  }
  .floating-chat-header {
    display: flex;
    align-items: center;
    background: #202123;
    border-radius: 18px 18px 0 0;
    padding: 12px 18px;
    border-bottom: 1px solid #10a37f;
  }
  .floating-chat-header span {
    font-family: 'Montserrat', Arial, sans-serif;
    font-size: 1.2em;
    font-weight: 700;
    color: #10a37f;
    margin-left: 10px;
  }
  .floating-close-btn {
    margin-left: auto;
    background: none;
    border: none;
    color: #10a37f;
    font-size: 1.3em;
    cursor: pointer;
  }
  .floating-chatbox {
    border: none;
    width: 100%;
    height: 180px;
    overflow-y: auto;
    padding: 16px;
    background: #444654;
    border-radius: 0 0 0 0;
    font-size: 1em;
    color: #fff;
  }
  .floating-chat-input-row {
    display: flex;
    align-items: center;
    background: #40414f;
    border-radius: 0 0 18px 18px;
    padding: 12px 18px;
    border-top: 1px solid #10a37f;
  }
  .floating-chat-input {
    width: 80%;
    padding: 10px;
    border-radius: 8px;
    border: none;
    background: #343541;
    color: #fff;
    font-size: 1em;
    outline: none;
    margin-right: 10px;
  }
  .floating-chat-window button {
    padding: 10px 18px;
    font-size: 1em;
    background: #10a37f;
    color: #fff;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 700;
    transition: background 0.2s;
  }
  .floating-chat-window button:hover {
    background: #13c08a;
  }
  .user-msg { color: #10a37f; }
  .bot-msg { color: #fff; }
  .floating-assist-popup {
    position: fixed;
    bottom: 110px;
    right: 110px;
    background: #343541;
    color: #fff;
    border-radius: 12px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.25);
    padding: 16px 22px;
    font-size: 1.08em;
    z-index: 1100;
    border: 1.5px solid #10a37f;
    display: none;
    animation: fadeIn 0.4s;
  }
  .floating-assist-popup.show {
    display: block;
  }
  .floating-assist-popup button {
    margin-left: 12px;
    padding: 6px 16px;
    border-radius: 8px;
    border: none;
    background: #10a37f;
    color: #fff;
    font-weight: 700;
    cursor: pointer;
    font-size: 1em;
    transition: background 0.2s;
  }
  .floating-assist-popup button:hover {
    background: #13c08a;
  }
</style>
<script>
function toggleMode() {
  document.body.classList.toggle('dark');
}
function sendChat() {
  var input = document.getElementById('chatinput');
  var msg = input.value.trim();
  if (!msg) return;
  var chatbox = document.getElementById('chatbox');
  chatbox.innerHTML += '<div class="user-msg"><b>You:</b> ' + msg + '</div>';
  input.value = '';
  fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: msg })
  })
  .then(r => r.json())
  .then data => {
    chatbox.innerHTML += '<div class="bot-msg"><b>Bot:</b> ' + data.reply + '</div>';
    chatbox.scrollTop = chatbox.scrollHeight;
  });
}
function toggleChat() {
  var chatSection = document.querySelector('.chat-section');
  chatSection.classList.toggle('open');
}
function toggleFloatingChat() {
  var chatWindow = document.getElementById('floating-chat-window');
  if (chatWindow) chatWindow.classList.toggle('open');
}
function sendFloatingChat() {
  var input = document.getElementById('floating-chatinput');
  var msg = input.value.trim();
  if (!msg) return;
  var chatbox = document.getElementById('floating-chatbox');
  chatbox.innerHTML += '<div class="user-msg"><b>You:</b> ' + msg + '</div>';
  input.value = '';
  fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: msg })
  })
  .then(r => r.json())
  .then(data => {
    chatbox.innerHTML += '<div class="bot-msg"><b>Bot:</b> ' + data.reply + '</div>';
    chatbox.scrollTop = chatbox.scrollHeight;
  });
}
let assistPopupTimeout;
function showAssistPopup() {
  var popup = document.getElementById('floating-assist-popup');
  if (popup) {
    popup.classList.add('show');
    clearTimeout(assistPopupTimeout);
    assistPopupTimeout = setTimeout(() => popup.classList.remove('show'), 6000);
  }
}
function hideAssistPopup() {
  var popup = document.getElementById('floating-assist-popup');
  if (popup) popup.classList.remove('show');
}
function acceptAssist() {
  hideAssistPopup();
  toggleFloatingChat();
}
document.addEventListener('DOMContentLoaded', function() {
  var input = document.getElementById('chatinput');
  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') sendChat();
  });
  var floatingInput = document.getElementById('floating-chatinput');
  if(floatingInput) {
    floatingInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') sendFloatingChat();
    });
  }
  var btn = document.querySelector('.floating-chat-btn');
  if(btn) {
    btn.addEventListener('mouseenter', showAssistPopup);
    btn.addEventListener('focus', showAssistPopup);
    btn.addEventListener('mouseleave', hideAssistPopup);
    btn.addEventListener('blur', hideAssistPopup);
  }
});
</script>
</head>
<body>
<div class="overlay">
<div class="container">
<button class="toggle-btn" onclick="toggleMode()">Toggle Dark/Light Mode</button>
<div class="section">
<h2><i class="fa-solid fa-globe icon"></i>Enter a URL to analyze:</h2>
<form method="post">
  <input type="text" name="url" placeholder="https://example.com" required>
  <select name="user_agent">
    <option value="browser">Browser</option>
    <option value="bot">Bot</option>
  </select>
  <input type="submit" value="Analyze">
</form>
</div>
{% if favicon %}
  <div class="section"><h3><i class="fa-solid fa-icons icon"></i>Favicon:</h3>
  <img src="{{ favicon }}" alt="Favicon"></div>
{% endif %}
{% if title %}
  <div class="section"><h3><i class="fa-solid fa-heading icon"></i>Page Title:</h3>
  <p>{{ title }}</p></div>
{% endif %}
{% if meta_desc %}
  <div class="section"><h3><i class="fa-solid fa-align-left icon"></i>Meta Description:</h3>
  <p>{{ meta_desc }}</p></div>
{% endif %}
{% if status_code %}
  <div class="section"><h3><i class="fa-solid fa-signal icon"></i>HTTP Status Code:</h3>
  <p>{{ status_code }}</p></div>
{% endif %}
{% if response_time %}
  <div class="section"><h3><i class="fa-solid fa-stopwatch icon"></i>Response Time:</h3>
  <p>{{ response_time }} ms</p></div>
{% endif %}
{% if not_https %}
  <div class="section"><p class="warning"><i class="fa-solid fa-triangle-exclamation icon"></i>Warning: This page does not use HTTPS!</p></div>
{% endif %}
{% if language %}
  <div class="section"><h3><i class="fa-solid fa-language icon"></i>Detected Language:</h3>
  <p>{{ language }}</p></div>
{% endif %}
{% if word_count is not none %}
  <div class="section"><h3><i class="fa-solid fa-font icon"></i>Word Count:</h3>
  <p>{{ word_count }}</p></div>
{% endif %}
{% if char_count is not none %}
  <div class="section"><h3><i class="fa-solid fa-keyboard icon"></i>Character Count:</h3>
  <p>{{ char_count }}</p></div>
{% endif %}
{% if headings %}
  <div class="section"><h3><i class="fa-solid fa-list-ol icon"></i>Headings:</h3>
  <ul>
    {% for h in headings %}
      <li>{{ h }}</li>
    {% endfor %}
  </ul></div>
{% endif %}
{% if images %}
  <div class="section"><h3><i class="fa-solid fa-image icon"></i>Images ({{ images|length }}):</h3>
  <div>
    {% for img in images %}
      <img src="{{ img }}" alt="Image">
    {% endfor %}
  </div></div>
{% endif %}
{% if links %}
  <div class="section"><h3><i class="fa-solid fa-link icon"></i>Links Found ({{ links|length }}):</h3>
  <ul>
    {% for link in links %}
      <li><a href="{{ link }}" target="_blank">{{ link }}</a></li>
    {% endfor %}
  </ul></div>
{% endif %}
{% if html_download %}
  <div class="section">
  <form method="post" style="display:inline-block;">
    <button type="submit"><i class="fa-solid fa-download icon"></i>Download Page HTML</button>
  </form>
  <form method="post" style="display:inline-block;">
    <button type="submit"><i class="fa-solid fa-file-export icon"></i>Export Results as JSON</button>
  </form>
  </div>
{% endif %}
{% if history %}
  <div class="section"><h3><i class="fa-solid fa-clock-rotate-left icon"></i>History (this session):</h3>
  <ul>
    {% for item in history %}
      <li>{{ item }}</li>
    {% endfor %}
  </ul></div>
{% endif %}
{% if error %}
  <div class="section"><p class="warning"><i class="fa-solid fa-circle-exclamation icon"></i>{{ error }}</p></div>
{% endif %}
</div>
</div>

<!-- Floating Chatbot Button and Window (Headphones Assistant style) -->
<div class="floating-chat-btn" onclick="toggleFloatingChat()" tabindex="0">
  <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="20" cy="20" r="18" stroke="#fff" stroke-width="2.5" fill="#343541"/>
    <!-- Headphones -->
    <path d="M10 24 Q10 14 20 14 Q30 14 30 24" stroke="#10a37f" stroke-width="2.5" fill="none"/>
    <rect x="8" y="24" width="4" height="7" rx="2" fill="#10a37f"/>
    <rect x="28" y="24" width="4" height="7" rx="2" fill="#10a37f"/>
    <!-- Head -->
    <circle cx="20" cy="22" r="5" fill="#fff" stroke="#10a37f" stroke-width="2"/>
  </svg>
</div>
<div id="floating-assist-popup" class="floating-assist-popup">
  <span>Need assistance?</span>
  <button onclick="acceptAssist()">Yes</button>
  <button onclick="hideAssistPopup()">No</button>
</div>
<div id="floating-chat-window" class="floating-chat-window">
  <div class="floating-chat-header">
    <svg viewBox="0 0 24 24" width="28" height="28" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" stroke="#fff" stroke-width="2" fill="#343541"/>
      <path d="M6 15 Q6 8 12 8 Q18 8 18 15" stroke="#10a37f" stroke-width="2" fill="none"/>
      <rect x="4.5" y="15" width="3" height="5" rx="1.5" fill="#10a37f"/>
      <rect x="16.5" y="15" width="3" height="5" rx="1.5" fill="#10a37f"/>
      <circle cx="12" cy="14" r="4" fill="#fff" stroke="#10a37f" stroke-width="1.5"/>
    </svg>
    <span>Flask Bot</span>
    <button class="floating-close-btn" onclick="toggleFloatingChat()">&times;</button>
  </div>
  <div id="floating-chatbox" class="floating-chatbox"></div>
  <div class="floating-chat-input-row">
    <input id="floating-chatinput" class="floating-chat-input" type="text" placeholder="Type your message..." autocomplete="off">
    <button onclick="sendFloatingChat()">Send</button>
  </div>
</div>
</body>
</html>
'''

def get_favicon(soup, url):
    icon = soup.find('link', rel=lambda x: x and 'icon' in x.lower())
    if icon and icon.get('href'):
        href = icon['href']
        if href.startswith('http'):
            return href
        else:
            return urljoin(url, href)
    # fallback: try /favicon.ico
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"

@app.route('/', methods=['GET', 'POST'])
def index():
    title = meta_desc = error = language = None
    links = images = headings = []
    status_code = response_time = word_count = char_count = None
    html_download = False
    url = favicon = None
    not_https = False
    history = session.get('history', [])
    if request.method == 'POST':
        url = request.form.get('url')
        user_agent = request.form.get('user_agent', 'browser')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        } if user_agent == 'browser' else {'User-Agent': 'MyWebBot/1.0'}
        if request.form.get('download') == '1':
            # Download HTML feature
            try:
                resp = requests.get(url, timeout=5, headers=headers)
                return send_file(
                    io.BytesIO(resp.content),
                    mimetype='text/html',
                    as_attachment=True,
                    download_name='page.html'
                )
            except Exception as e:
                error = f"Error downloading HTML: {e}"
        elif request.form.get('export_json') == '1':
            # Export as JSON
            try:
                resp = requests.get(url, timeout=5, headers=headers)
                soup = BeautifulSoup(resp.text, 'html.parser')
                title = soup.title.string.strip() if soup.title and soup.title.string else 'No title found'
                meta = soup.find('meta', attrs={'name': 'description'})
                meta_desc = meta['content'].strip() if meta and meta.get('content') else 'No meta description found'
                links = [a['href'] for a in soup.find_all('a', href=True)]
                images = [urljoin(url, img['src']) for img in soup.find_all('img', src=True)]
                headings = [h.get_text(strip=True) for h in soup.find_all(re.compile('^h[1-6]$'))]
                text = soup.get_text()
                word_count = len(text.split())
                char_count = len(text)
                try:
                    language = detect(text)
                except LangDetectException:
                    language = 'Unknown'
                data = {
                    'title': title,
                    'meta_description': meta_desc,
                    'links': links,
                    'images': images,
                    'headings': headings,
                    'word_count': word_count,
                    'char_count': char_count,
                    'language': language
                }
                return jsonify(data)
            except Exception as e:
                error = f"Error exporting JSON: {e}"
        else:
            try:
                start = time.time()
                resp = requests.get(url, timeout=5, headers=headers)
                response_time = int((time.time() - start) * 1000)
                status_code = resp.status_code
                soup = BeautifulSoup(resp.text, 'html.parser')
                title = soup.title.string.strip() if soup.title and soup.title.string else 'No title found'
                meta = soup.find('meta', attrs={'name': 'description'})
                meta_desc = meta['content'].strip() if meta and meta.get('content') else 'No meta description found'
                links = [a['href'] for a in soup.find_all('a', href=True)]
                images = [urljoin(url, img['src']) for img in soup.find_all('img', src=True)]
                headings = [h.get_text(strip=True) for h in soup.find_all(re.compile('^h[1-6]$'))]
                text = soup.get_text()
                word_count = len(text.split())
                char_count = len(text)
                try:
                    language = detect(text)
                except LangDetectException:
                    language = 'Unknown'
                favicon = get_favicon(soup, url)
                not_https = not url.lower().startswith('https://')
                html_download = True
                # Save to session history
                if url not in history:
                    history.append(url)
                    session['history'] = history
            except Exception as e:
                error = f"Error: {e}"
    return render_template_string(HTML_FORM, title=title, meta_desc=meta_desc, links=links, status_code=status_code, response_time=response_time, html_download=html_download, url=url, error=error, images=images, word_count=word_count, char_count=char_count, headings=headings, language=language, favicon=favicon, not_https=not_https, history=history)

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.get_json()
    url = data.get('url')
    user_agent = data.get('user_agent', 'browser')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    } if user_agent == 'browser' else {'User-Agent': 'MyWebBot/1.0'}
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    try:
        start = time.time()
        resp = requests.get(url, timeout=5, headers=headers)
        response_time = int((time.time() - start) * 1000)
        status_code = resp.status_code
        soup = BeautifulSoup(resp.text, 'html.parser')
        title = soup.title.string.strip() if soup.title and soup.title.string else 'No title found'
        meta = soup.find('meta', attrs={'name': 'description'})
        meta_desc = meta['content'].strip() if meta and meta.get('content') else 'No meta description found'
        links = [a['href'] for a in soup.find_all('a', href=True)]
        images = [urljoin(url, img['src']) for img in soup.find_all('img', src=True)]
        headings = [h.get_text(strip=True) for h in soup.find_all(re.compile('^h[1-6]$'))]
        text = soup.get_text()
        word_count = len(text.split())
        char_count = len(text)
        try:
            language = detect(text)
        except LangDetectException:
            language = 'Unknown'
        favicon = get_favicon(soup, url)
        not_https = not url.lower().startswith('https://')
        return jsonify({
            'title': title,
            'meta_description': meta_desc,
            'status_code': status_code,
            'response_time_ms': response_time,
            'links': links,
            'images': images,
            'headings': headings,
            'word_count': word_count,
            'char_count': char_count,
            'language': language,
            'favicon': favicon,
            'not_https': not_https
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_msg = data.get('message', '').strip().lower()
    # Simple rule-based chatbot logic
    if not user_msg:
        reply = "Please type something!"
    elif 'hello' in user_msg or 'hi' in user_msg:
        reply = "Hello! How can I help you today?"
    elif 'help' in user_msg:
        reply = "You can analyze a web page by entering its URL above, or ask me anything!"
    elif 'thank' in user_msg:
        reply = "You're welcome! 😊"
    elif 'bye' in user_msg:
        reply = "Goodbye! Have a great day!"
    else:
        reply = f"You said: {data.get('message', '')}"
    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(debug=True)
