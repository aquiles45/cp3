# setup_mongo.py
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid, OperationFailure

# --- Configurações (iguais ao seu url2.py) ---
MONGO_URL = 'mongodb://localhost:27017/'
DB_NAME = 'encurtador_db'
LINKS_COLLECTION = 'links'
LOGS_COLLECTION = 'logs_acesso'
# ----------------------------------------------

def inicializar_banco():
    """
    Conecta ao MongoDB, cria as coleções (se não existirem)
    e aplica os índices necessários para otimização.
    """
    cliente = None
    try:
        # 1. Conectar ao MongoDB
        cliente = MongoClient(MONGO_URL)
        db = cliente[DB_NAME]
        
        print(f"Conectado ao MongoDB: {MONGO_URL}")
        print(f"Selecionado o banco de dados: {DB_NAME}")

        # 2. Criar a coleção 'links' e seu índice
        try:
            db.create_collection(LINKS_COLLECTION)
            print(f"Coleção '{LINKS_COLLECTION}' criada.")
        except CollectionInvalid:
            print(f"Coleção '{LINKS_COLLECTION}' já existe.")
        
        # Criar índice único para 'codigo_curto'
        # Isso garante buscas rápidas e que não haja códigos duplicados
        try:
            db[LINKS_COLLECTION].create_index('codigo_curto', unique=True)
            print(f"Índice único criado para 'codigo_curto' em '{LINKS_COLLECTION}'.")
        except OperationFailure as e:
            if "IndexOptionsConflict" in str(e):
                 print(f"Índice 'codigo_curto' já existe com opções diferentes.")
            elif "IndexKeySpecsConflict" in str(e):
                print(f"Índice 'codigo_curto' já existe.")
            else:
                raise e

        # 3. Criar a coleção 'logs_acesso' e seu índice
        try:
            db.create_collection(LOGS_COLLECTION)
            print(f"Coleção '{LOGS_COLLECTION}' criada.")
        except CollectionInvalid:
            print(f"Coleção '{LOGS_COLLECTION}' já existe.")
        
        # Criar índice para 'link_id'
        # Isso acelera a busca de estatísticas (rota /api/links/<id>/stats)
        try:
            db[LOGS_COLLECTION].create_index('link_id')
            print(f"Índice criado para 'link_id' em '{LOGS_COLLECTION}'.")
        except OperationFailure as e:
            if "IndexKeySpecsConflict" in str(e):
                 print(f"Índice 'link_id' já existe.")
            else:
                raise e

        print("\n[Sucesso] O banco de dados está pronto para uso!")

    except Exception as e:
        print(f"\n[Erro] Ocorreu um erro ao inicializar o MongoDB: {e}")
    
    finally:
        if cliente:
            cliente.close()
            print("Conexão com o MongoDB fechada.")

if __name__ == "__main__":
    inicializar_banco()