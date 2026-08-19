# app.py - Servidor do Quantum Bot (VERSÃO CORRIGIDA E COMPLETA)
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import threading
import time
import random
from datetime import datetime
import os
import sys

app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'quantum-bot-secret-2024')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'jwt-secret-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # Tokens não expiram

# CORS - Permitir todas as origens
CORS(app, resources={r"/*": {"origins": "*"}})

# Inicializa JWT
jwt = JWTManager(app)

# Banco de dados em memória
usuarios = {}
configs = {}
bots = {}
historico = {}

# Chave de licença
LICENCA = 'QUANTUM-BOT-2024'

# ============================================
# ROTA PRINCIPAL (RAIZ)
# ============================================

@app.route('/', methods=['GET'])
def home():
    """Rota principal - mostra informações do servidor"""
    return jsonify({
        'status': 'online',
        'message': '⚛️ Quantum Bot Server',
        'version': '1.0.0',
        'servidor': 'online',
        'timestamp': datetime.now().isoformat(),
        'endpoints': [
            {'rota': '/api/health', 'metodo': 'GET', 'descricao': 'Verifica saúde do servidor'},
            {'rota': '/api/auth/register', 'metodo': 'POST', 'descricao': 'Registrar novo usuário'},
            {'rota': '/api/auth/login', 'metodo': 'POST', 'descricao': 'Login do usuário'},
            {'rota': '/api/auth/validate', 'metodo': 'POST', 'descricao': 'Validar licença'},
            {'rota': '/api/config', 'metodo': 'GET/POST', 'descricao': 'Configurações do bot'},
            {'rota': '/api/bot/start', 'metodo': 'POST', 'descricao': 'Iniciar o bot'},
            {'rota': '/api/bot/stop', 'metodo': 'POST', 'descricao': 'Parar o bot'},
            {'rota': '/api/bot/status', 'metodo': 'GET', 'descricao': 'Status do bot'},
            {'rota': '/api/bot/history', 'metodo': 'GET', 'descricao': 'Histórico de operações'}
        ]
    })

# ============================================
# ROTA DE SAÚDE
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica saúde do servidor"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'bots_ativos': len([b for b in bots.values() if b.get('running', False)]),
        'total_usuarios': len(usuarios),
        'version': '1.0.0'
    }), 200

# ============================================
# ROTAS DE AUTENTICAÇÃO
# ============================================

@app.route('/api/auth/register', methods=['POST'])
def registrar():
    try:
        dados = request.json
        usuario = dados.get('username')
        senha = dados.get('password')
        licenca = dados.get('license_key')
        
        if not usuario or not senha:
            return jsonify({'error': 'Usuário e senha são obrigatórios'}), 400
            
        if licenca != LICENCA:
            return jsonify({'error': 'Licença inválida'}), 401
        
        if usuario in usuarios:
            return jsonify({'error': 'Usuário já existe'}), 400
        
        usuarios[usuario] = {
            'password': senha,
            'created_at': datetime.now().isoformat()
        }
        
        token = create_access_token(identity=usuario)
        
        return jsonify({
            'success': True,
            'token': token,
            'username': usuario,
            'message': 'Usuário registrado com sucesso!'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        dados = request.json
        usuario = dados.get('username')
        senha = dados.get('password')
        
        if not usuario or not senha:
            return jsonify({'error': 'Usuário e senha são obrigatórios'}), 400
        
        if usuario not in usuarios or usuarios[usuario]['password'] != senha:
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        token = create_access_token(identity=usuario)
        
        return jsonify({
            'success': True,
            'token': token,
            'username': usuario,
            'message': 'Login realizado com sucesso!'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/validate', methods=['POST'])
def validate_license():
    """Valida licença"""
    try:
        dados = request.json
        licenca = dados.get('license_key')
        
        if licenca == LICENCA:
            return jsonify({'valid': True, 'message': 'Licença válida'}), 200
        else:
            return jsonify({'valid': False, 'message': 'Licença inválida'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# CONFIGURAÇÕES
# ============================================

@app.route('/api/config', methods=['GET'])
@jwt_required()
def get_config():
    try:
        usuario = get_jwt_identity()
        
        if usuario not in configs:
            configs[usuario] = {
                'valor_entrada': 10.0,
                'multiplicador_gale': 2.0,
                'max_gales': 2,
                'stop_loss': 0.0,
                'stop_win': 0.0,
                'operacoes_por_ciclo': 2,
                'account_type': 'PRACTICE'
            }
        
        return jsonify({
            'success': True,
            'config': configs[usuario]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['POST'])
@jwt_required()
def save_config():
    try:
        usuario = get_jwt_identity()
        dados = request.json
        
        configs[usuario] = {
            'valor_entrada': float(dados.get('valor_entrada', 10)),
            'multiplicador_gale': float(dados.get('multiplicador_gale', 2)),
            'max_gales': int(dados.get('max_gales', 2)),
            'stop_loss': float(dados.get('stop_loss', 0)),
            'stop_win': float(dados.get('stop_win', 0)),
            'operacoes_por_ciclo': int(dados.get('operacoes_por_ciclo', 2)),
            'account_type': dados.get('account_type', 'PRACTICE')
        }
        
        return jsonify({
            'success': True,
            'message': 'Configuração salva com sucesso!'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# CONTROLE DO BOT
# ============================================

@app.route('/api/bot/start', methods=['POST'])
@jwt_required()
def start_bot():
    try:
        usuario = get_jwt_identity()
        
        # Verifica se já está rodando
        if usuario in bots and bots[usuario].get('running', False):
            return jsonify({'error': 'Bot já está rodando'}), 400
        
        # Inicia o bot em uma thread
        def rodar_bot():
            try:
                # Inicializa dados do bot
                bots[usuario] = {
                    'running': True,
                    'lucro': 0.0,
                    'operacoes': 0,
                    'status': 'running',
                    'started_at': datetime.now().isoformat()
                }
                
                # Loop principal
                while bots[usuario].get('running', False):
                    # Simula operação (40% de chance de perder)
                    ganhou = random.random() > 0.4
                    
                    # Gera lucro/perda
                    if ganhou:
                        lucro = round(random.uniform(0.5, 1.5), 2)
                    else:
                        lucro = round(random.uniform(-1.5, -0.5), 2)
                    
                    # Atualiza dados
                    bots[usuario]['lucro'] += lucro
                    bots[usuario]['operacoes'] += 1
                    
                    # Salva no histórico
                    if usuario not in historico:
                        historico[usuario] = []
                    
                    historico[usuario].append({
                        'horario': datetime.now().strftime('%H:%M:%S'),
                        'resultado': 'WIN' if ganhou else 'LOSS',
                        'lucro': lucro,
                        'operacao': bots[usuario]['operacoes']
                    })
                    
                    # Mantém apenas últimas 100 operações
                    if len(historico[usuario]) > 100:
                        historico[usuario] = historico[usuario][-100:]
                    
                    # Aguarda 5 segundos
                    time.sleep(5)
                    
            except Exception as e:
                print(f'Erro no bot: {e}')
                bots[usuario]['running'] = False
                bots[usuario]['status'] = 'error'
        
        # Inicia thread
        thread = threading.Thread(target=rodar_bot)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Bot iniciado com sucesso!'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/stop', methods=['POST'])
@jwt_required()
def stop_bot():
    try:
        usuario = get_jwt_identity()
        
        if usuario in bots:
            bots[usuario]['running'] = False
            bots[usuario]['status'] = 'stopped'
            return jsonify({
                'success': True,
                'message': 'Bot parado com sucesso!'
            }), 200
        
        return jsonify({'error': 'Bot não está rodando'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/status', methods=['GET'])
@jwt_required()
def bot_status():
    try:
        usuario = get_jwt_identity()
        
        if usuario in bots:
            bot = bots[usuario]
            wins = sum(1 for h in historico.get(usuario, []) if h['resultado'] == 'WIN')
            losses = sum(1 for h in historico.get(usuario, []) if h['resultado'] == 'LOSS')
            
            return jsonify({
                'success': True,
                'status': bot.get('status', 'stopped'),
                'rodando': bot.get('running', False),
                'lucro_dia': round(bot.get('lucro', 0), 2),
                'operacoes': bot.get('operacoes', 0),
                'wins': wins,
                'losses': losses,
                'started_at': bot.get('started_at')
            }), 200
        
        return jsonify({
            'success': True,
            'status': 'stopped',
            'rodando': False,
            'lucro_dia': 0,
            'operacoes': 0,
            'wins': 0,
            'losses': 0
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/history', methods=['GET'])
@jwt_required()
def get_history():
    try:
        usuario = get_jwt_identity()
        limit = request.args.get('limit', 20, type=int)
        
        hist = historico.get(usuario, [])
        
        return jsonify({
            'success': True,
            'history': hist[-limit:],
            'total': len(hist)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# TRATAMENTO DE ERROS GLOBAIS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Rota não encontrada',
        'message': 'Verifique a URL ou consulte a documentação'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Erro interno do servidor',
        'message': 'Tente novamente mais tarde'
    }), 500

# ============================================
# INICIALIZAÇÃO
# ============================================

if __name__ == '__main__':
    # Usar a porta dinâmica do Railway
    port = int(os.environ.get('PORT', 5000))
    print(f'🚀 Servidor Quantum Bot rodando na porta {port}')
    print(f'📊 Health Check: http://localhost:{port}/api/health')
    print(f'🌐 Rota raiz: http://localhost:{port}/')
    
    # Inicia com o servidor embutido do Flask
    app.run(host='0.0.0.0', port=port, debug=False)
