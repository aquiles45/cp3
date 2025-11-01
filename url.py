from flask import Flask, redirect, render_template, request, jsonify, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
import re
import secrets
import string

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['encurtador_db']
links_collection = db['links']
logs_collection = db['logs_acesso']

def is_redirect_url(url):
    try:
        import requests
        response = requests.head(url, allow_redirects=False, timeout=5)
        return response.status_code in [301, 302, 303, 307, 308]
    except:
        return False

def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    links = list(links_collection.find())
    return render_template('admin.html', links=links)

@app.route('/api/links', methods=['GET'])
def list_links():
    links = list(links_collection.find())
    for link in links:
        link['_id'] = str(link['_id'])
    return jsonify(links)

@app.route('/api/links', methods=['POST'])
def create_link():
    data = request.json
    url_destino = data.get('url_destino')
    codigo_curto = data.get('codigo_curto')
    
    if not url_destino or not re.match(r'https?://', url_destino):
        return jsonify({'error': 'URL inválida. Use o formato http:// ou https://'}), 400
    
    if is_redirect_url(url_destino):
        return jsonify({'error': 'A URL informada é um redirecionamento. Por razões de segurança, não permitimos encurtar redirecionamentos.'}), 400
    
    if not codigo_curto:
        codigo_curto = generate_short_code()
    
    if links_collection.find_one({'codigo_curto': codigo_curto}):
        return jsonify({'error': 'Este código curto já está em uso. Escolha outro.'}), 400
    
    novo_link = {
        'codigo_curto': codigo_curto,
        'url_destino': url_destino,
        'data_criacao': datetime.datetime.now(datetime.UTC),
        'cliques': 0
    }
    
    result = links_collection.insert_one(novo_link)
    novo_link['_id'] = str(result.inserted_id)
    
    return jsonify(novo_link), 201

@app.route('/api/links/<id>', methods=['DELETE'])
def delete_link(id):
    try:
        result = links_collection.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            return jsonify({'message': 'Link removido com sucesso'}), 200
        else:
            return jsonify({'error': 'Link não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/links/<id>/stats', methods=['GET'])
def get_link_stats(id):
    try:
        link = links_collection.find_one({'_id': ObjectId(id)})
        if not link:
            return jsonify({'erro': 'Link não encontrado'}), 404
            
        cliques = link.get('cliques', 0)
        
        logs = list(logs_collection.find({'link_id': ObjectId(id)}))
        for log in logs:
            log['_id'] = str(log['_id'])
            log['link_id'] = str(log['link_id'])
            log['data_hora'] = log['data_hora'].isoformat()
            
        return jsonify({
            'cliques': cliques,
            'historico': logs
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/<string:codigo>')
def redirect_short_url(codigo):
    try:
        link = links_collection.find_one({'codigo_curto': codigo})

        if link:
            link_id = link['_id']
            url_destino = link['url_destino']

            log_data = {
                'link_id': link_id,
                'data_hora': datetime.datetime.now(datetime.UTC),
                'ip_cliente': request.remote_addr
            }
            logs_collection.insert_one(log_data)

            links_collection.update_one(
                {'_id': link_id},
                {'$inc': {'cliques': 1}}
            )

            return redirect(url_destino)
        else:
            return render_template('erro.html', 
                                  message='Esta URL encurtada não existe ou foi removida.'), 404

    except Exception as e:
        print(f"Erro: {e}")
        return render_template('erro.html', 
                              message='Ocorreu um erro no servidor.'), 500

if __name__ == '__main__':
    app.run(debug=True)