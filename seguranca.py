'''DB_CONFIG = {
    'host': 'hopper.proxy.rlwy.net',
    'user': 'root',
    'password': 'AsSPWHPnoPqfscSNBCVlIJZMAGcRWNDS',
    'port': 33343,
    'database': 'railway'
}
DB_NAME = 'SistemaDeChatEducacional' 
SESSION_FILE = 'session_status.txt'''




import mysql.connector
from mysql.connector import errorcode

# --- Lista de Palavras Proibidas ---
# Usar um 'set' (conjunto) é mais rápido para buscas
PALAVRAS_PROIBIDAS = {
    "Cearense",
    "vasco",
    "bobo"
    # Adicione aqui todas as palavras que deseja bloquear
}

def _conteudo_e_inapropriado(conteudo):
    """
    Função interna (privada) que verifica se a string contém palavras proibidas.
    """
    if not conteudo:
        return False
    
    # Normaliza o conteúdo para minúsculas para verificação
    conteudo_lower = conteudo.lower()
    
    # Verifica se alguma palavra proibida está contida na mensagem
    for palavra in PALAVRAS_PROIBIDAS:
        if palavra in conteudo_lower:
            return True
            
    return False

def verificar_mensagem(cursor, chat_id, content):
    """
    Função principal de verificação.
    Verifica se o chat é um grupo público e, em caso afirmativo,
    aplica o filtro de conteúdo.

    Recebe o cursor do banco de dados (de app.py) para reutilizar a conexão.
    
    Retorna:
        (True, "Permitido") se a mensagem for aprovada.
        (False, "Mensagem de erro") se a mensagem for bloqueada.
    """
    
    try:
        # 1. Descobrir o tipo de chat E o tipo do grupo (público ou privado)
        #    Usamos LEFT JOIN para garantir que chats privados (sem idGrupo_FK)
        #    não causem erro.
        query_chat_info = """
            SELECT 
                G.tipo AS grupo_tipo 
            FROM Chat C
            LEFT JOIN Grupo G ON C.idGrupo_FK = G.idGrupo
            WHERE C.idChat = %s
        """
        cursor.execute(query_chat_info, (chat_id,))
        chat_info = cursor.fetchone()
        
        if not chat_info:
            # Isso não deve acontecer se o chat_id for válido
            return False, "Chat não encontrado."
        
        if chat_info.get('grupo_tipo') == 'público':
            # Se o grupo for público, rodamos o filtro
            if _conteudo_e_inapropriado(content):
                # Se encontrar palavra imprópria, bloqueia a mensagem
                return False, "Sua mensagem contém conteúdo impróprio e foi bloqueada."
        
        # 3. Se não for um grupo público, ou se for público e a mensagem for limpa:
        return True, "Permitido"

    except mysql.connector.Error as err:
        print(f"Erro no módulo de segurança ao verificar chat_id {chat_id}: {err}")
        return False, "Erro interno ao verificar a mensagem."