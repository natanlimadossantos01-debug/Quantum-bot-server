# web_app.py - Versão Web do Quantum Bot Pro
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'quantum-web-secret')
CORS(app)

# URL da API do seu bot
API_URL = 'https://quantum-bot-server-production.up.railway.app'

# ============================================
# ROTAS DA APLICAÇÃO WEB
# ============================================

@app.route('/')
def index():
    """Página principal do app web"""
    return render_template('index.html')

@app.route('/api/web/login', methods=['POST'])
def web_login():
    """Proxy para login via web"""
    try:
        data = request.json
        response = requests.post(
            f'{API_URL}/api/auth/login',
            json={'username': data.get('username'), 'password': data.get('password')},
            timeout=10
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/web/register', methods=['POST'])
def web_register():
    """Proxy para registro via web"""
    try:
        data = request.json
        response = requests.post(
            f'{API_URL}/api/auth/register',
            json={
                'username': data.get('username'),
                'password': data.get('password'),
                'license_key': data.get('license_key')
            },
            timeout=10
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/web/bot/start', methods=['POST'])
def web_start_bot():
    """Proxy para iniciar bot via web"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        response = requests.post(
            f'{API_URL}/api/bot/start',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/web/bot/stop', methods=['POST'])
def web_stop_bot():
    """Proxy para parar bot via web"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        response = requests.post(
            f'{API_URL}/api/bot/stop',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/web/bot/status', methods=['GET'])
def web_bot_status():
    """Proxy para status do bot via web"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        response = requests.get(
            f'{API_URL}/api/bot/status',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
