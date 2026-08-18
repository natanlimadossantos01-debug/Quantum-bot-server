# app.py - Servidor do Quantum Bot
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import threading
import time
import random
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'quantum-bot-secret-2024'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-2024'

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
jwt = JWTManager(app)

# Banco de dados (em memória)
usuarios = {}
configs = {}
bots = {}
historico = {}
LICENCA = 'QUANTUM-BOT-2024'

# ============================================
# ROTAS DE AUTENTICAÇÃO
# ============================================

@app.route('/api/auth/register', methods=['POST'])
def registrar():
    dados = request.json
    usuario = dados.get('username')
    senha = dados.get('password')
    licenca = dados.get('license_key')
    
    if licenca != LICENCA:
        return jsonify({'error': 'Licença inválida'}), 401
    
    if usuario in usuarios:
        return jsonify({'error': 'Usuário já existe'}), 400
    
    usuarios[usuario] = {'password': senha}
    token = create_access_token(identity=usuario)
    
    return jsonify({'success': True, 'token': token, 'username': usuario})

@app.route('/api/auth/login', methods=['POST'])
def login():
    dados = request.json
    usuario = dados.get('username')
    senha = dados.get('password')
    
    if usuario not in usuarios or usuarios[usuario]['password'] != senha:
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    token = create_access_token(identity=usuario)
    return jsonify({'success': True, 'token': token, 'username': usuario})

# ============================================
# CONFIGURAÇÕES
# ============================================

@app.route('/api/config', methods=['GET'])
@jwt_required()
def get_config():
    usuario = get_jwt_identity()
    
    if usuario not in configs:
        configs[usuario] = {
            'valor_entrada': 10.0,
            'max_gales': 2,
            'stop_loss': 0,
            'stop_win': 0
        }
    
    return jsonify({'success': True, 'config': configs[usuario]})

@app.route('/api/config', methods=['POST'])
@jwt_required()
def save_config():
    usuario = get_jwt_identity()
    configs[usuario] = request.json
    return jsonify({'success': True, 'message': 'Configuração salva!'})

# ============================================
# CONTROLE DO BOT
# ============================================

@app.route('/api/bot/start', methods=['POST'])
@jwt_required()
def start_bot():
    usuario = get_jwt_identity()
    
    if usuario in bots and bots[usuario].get('running', False):
        return jsonify({'error': 'Bot já está rodando'}), 400
    
    def rodar_bot():
        bots[usuario] = {'running': True, 'lucro': 0, 'operacoes': 0}
        
        while bots[usuario].get('running', False):
            ganhou = random.random() > 0.4
            lucro = random.uniform(0.5, 1.5) if ganhou else random.uniform(-1.5, -0.5)
            
            bots[usuario]['lucro'] += lucro
            bots[usuario]['operacoes'] += 1
            
            if usuario not in historico:
                historico[usuario] = []
            
            historico[usuario].append({
                'horario': datetime.now().strftime('%H:%M:%S'),
                'resultado': 'WIN' if ganhou else 'LOSS',
                'lucro': lucro
            })
            
            if len(historico[usuario]) > 50:
                historico[usuario] = historico[usuario][-50:]
            
            time.sleep(5)
    
    thread = threading.Thread(target=rodar_bot)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Bot iniciado!'})

@app.route('/api/bot/stop', methods=['POST'])
@jwt_required()
def stop_bot():
    usuario = get_jwt_identity()
    
    if usuario in bots:
        bots[usuario]['running'] = False
    
    return jsonify({'success': True, 'message': 'Bot parado!'})

@app.route('/api/bot/status', methods=['GET'])
@jwt_required()
def bot_status():
    usuario = get_jwt_identity()
    
    if usuario in bots:
        bot = bots[usuario]
        wins = sum(1 for h in historico.get(usuario, []) if h['resultado'] == 'WIN')
        losses = sum(1 for h in historico.get(usuario, []) if h['resultado'] == 'LOSS')
        
        return jsonify({
            'success': True,
            'rodando': bot.get('running', False),
            'lucro_dia': bot.get('lucro', 0),
            'operacoes': bot.get('operacoes', 0),
            'wins': wins,
            'losses': losses
        })
    
    return jsonify({
        'success': True,
        'rodando': False,
        'lucro_dia': 0,
        'operacoes': 0,
        'wins': 0,
        'losses': 0
    })

@app.route('/api/bot/history', methods=['GET'])
@jwt_required()
def get_history():
    usuario = get_jwt_identity()
    return jsonify({'success': True, 'history': historico.get(usuario, [])})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'online', 'timestamp': datetime.now().isoformat()})

# ============================================
# INICIALIZAÇÃO
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
