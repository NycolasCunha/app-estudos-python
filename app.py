import chat_media 
from tkinter import filedialog
import subprocess 
import os
import chat_media  
from tkinter import filedialog
import subprocess 
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import mysql.connector
from mysql.connector import errorcode
import sys
import os
import ctypes 
from datetime import datetime
import textwrap
import seguranca


# --- 0. Configurações de Cores e Constantes ---

DB_CONFIG = {
    'host': '',
    'user': 'sistema_de_chat_educacional',
    'password': '',
    'port': 3306,
    'database': 'sistema_de_chat_educacional'
}
DB_NAME = 'sistema_de_chat_educacional' 
SESSION_FILE = 'session_status.txt'

#ico config
def resource_path(relative_path):
    """ Obtém o caminho absoluto para o recurso (Universal: PyInstaller, Nuitka e Dev) """
    try:
        # PyInstaller cria uma pasta temporária e armazena em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Nuitka ou modo desenvolvimento (usa o diretório do arquivo atual)
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, relative_path)

# --- Configuração OBRIGATÓRIA para o ícone aparecer na Barra de Tarefas do Windows ---
myappid = 'sistema.chat.educacional.v1' # Pode ser qualquer nome único
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# --- CORES ATUALIZADAS (COM MODO CLARO/ESCURO) ---
CTK_THEME_COLORS = {
    "primary": "#4f46e5",
    "secondary": "#4f46e5",
    "Terceira":"#000000",
    "danger": "#e11d48", 
    "success": "#16a34a",
    "bg_main": ("#E5E7EB", "#111827"),
    "bg_card": ("white", "#1F2937"),
    "text_dark": ("#1f2937", "#F9FAFB"),
    "text_light": ("#6b7280", "#9CA3AF"),
    "nav_button_default": ("#6B7280", "#4B5563")
}

ctk.set_appearance_mode("light") 
ctk.set_default_color_theme("blue") 

# --- 1. Funções de Acesso ao Banco de Dados (Inalteradas) ---

def get_connection(db_name=None):
    config = DB_CONFIG.copy()
    if db_name:
        config['database'] = db_name
    try:
        cnx = mysql.connector.connect(**config)
        return cnx
    except mysql.connector.Error as err:
        print(f"Erro de conexão com o MySQL: {err}")
        return None

def fetch_user_details(user_id):
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return None
    details = {}
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT idUsuario, nome, email, idade FROM Usuario WHERE idUsuario = %s", (user_id,))
        details = cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Erro ao buscar detalhes do usuário: {err}")
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()
    return details

def validate_login(email, password):
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return None
    user_id = None
    try:
        cursor = cnx.cursor()
        query = "SELECT idUsuario FROM Usuario WHERE email = %s AND senha = %s"
        cursor.execute(query, (email, password))
        result = cursor.fetchone()
        if result:
            user_id = result[0]
    except mysql.connector.Error as err:
        print(f"Erro na validação de login: {err}")
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()
    return user_id

def create_new_account(name, age, email, password):
    cnx = get_connection(db_name=DB_NAME)
    if not cnx:
        return False, "Erro de conexão com o banco de dados."
    try:
        cursor = cnx.cursor()
        query = "INSERT INTO Usuario (nome, idade, email, senha) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (name, age, email, password))
        cnx.commit()
        new_id = cursor.lastrowid
        return True, new_id
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            return False, "Este e-mail já está cadastrado."
        print(f"Erro ao criar conta: {err}")
        return False, f"Erro inesperado: {err}"
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()

def fetch_user_chats(user_id):
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return []
    chat_ids = []
    try:
        cursor = cnx.cursor()
        query = "SELECT idChat FROM Usuario_Chat WHERE idUsuario = %s"
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        chat_ids = [row[0] for row in results]
    except mysql.connector.Error as err:
        print(f"Erro ao buscar chats do usuário: {err}")
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()
    return chat_ids

def get_chat_details(chat_id, current_user_id):
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return None
    details = {}
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT tipo FROM Chat WHERE idChat = %s", (chat_id,))
        chat_info = cursor.fetchone()
        if not chat_info: return None
        chat_type = chat_info['tipo']
        details['type'] = chat_type
        query = "SELECT u.nome FROM Usuario_Chat uc JOIN Usuario u ON uc.idUsuario = u.idUsuario WHERE uc.idChat = %s AND uc.idUsuario != %s"
        cursor.execute(query, (chat_id, current_user_id))
        participants = cursor.fetchall()
        participant_names = [p['nome'] for p in participants]
        if chat_type == 'privado':
            details['name'] = participant_names[0] if participants else "Chat Vazio"
        else:
            cursor.execute("SELECT G.nome FROM Chat C JOIN Grupo G ON C.idGrupo_FK = G.idGrupo WHERE C.idChat = %s", (chat_id,))
            group_name_result = cursor.fetchone()
            if group_name_result:
                details['name'] = group_name_result['nome']
            else:
                details['name'] = f"Grupo: {', '.join(participant_names)}"
                if not participant_names:
                    details['name'] = "Grupo Vazio"
            
    except mysql.connector.Error as err:
        print(f"Erro ao buscar detalhes do chat: {err}")
        return None
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()
    return details

# ======================================================================
# --- FUNÇÃO CORRIGIDA 1 ---
# ======================================================================

def fetch_messages(chat_id, current_user_id):
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return []
    messages = []
    try:
        cursor = cnx.cursor(dictionary=True)
        # ADICIONADO: m.idMensagem, m.tipo, m.caminho_arquivo
        query = """
            SELECT m.idMensagem, m.conteudo, m.dataEnvio, m.tipo, m.caminho_arquivo, 
                   u.nome AS remetente, m.idUsuario 
            FROM Mensagem m 
            JOIN Usuario u ON m.idUsuario = u.idUsuario 
            WHERE m.idChat = %s 
            ORDER BY m.dataEnvio ASC
        """
        cursor.execute(query, (chat_id,))
        messages = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Erro ao buscar mensagens: {err}")
    finally:
        if cnx.is_connected(): cursor.close(); cnx.close()
    return messages

# ======================================================================
# --- FUNÇÃO CORRIGIDA 2 ---
# ======================================================================

def post_new_message(chat_id, user_id, content, msg_type='texto', file_path=None):
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return False, "Erro de conexão."
    try:
        cursor = cnx.cursor(dictionary=True) 
        
        # (Lógica de segurança mantida...)
        permitido, mensagem_status = seguranca.verificar_mensagem(cursor, chat_id, content)
        if not permitido: return False, mensagem_status
            
        query = """
            INSERT INTO Mensagem (conteudo, idUsuario, idChat, tipo, caminho_arquivo) 
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (content, user_id, chat_id, msg_type, file_path)
        cursor.execute(query, params)
        cnx.commit()
        return True, "Mensagem enviada."
    except mysql.connector.Error as err:
        cnx.rollback() 
        return False, f"Erro ao enviar: {err}"
    finally:
        if cnx.is_connected(): cursor.close(); cnx.close()

#Função para deletar as mensagens

def delete_message(message_id):
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return False
    try:
        cursor = cnx.cursor()
        cursor.execute("DELETE FROM Mensagem WHERE idMensagem = %s", (message_id,))
        cnx.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao deletar: {err}")
        return False
    finally:
        if cnx.is_connected(): cursor.close(); cnx.close()

# --- 1.2 NOVAS FUNÇÕES (GRUPOS E MODERAÇÃO) ---
# (Restante do código inalterado)

def check_user_moderator_status(user_id):
    """Verifica se o usuário é um moderador."""
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return False
    is_mod = False
    try:
        cursor = cnx.cursor()
        cursor.execute("SELECT 1 FROM Moderador WHERE idModerador = %s LIMIT 1", (user_id,))
        if cursor.fetchone():
            is_mod = True
    except mysql.connector.Error as err:
        print(f"Erro ao verificar status de moderador: {err}")
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()
    return is_mod

def search_groups(search_term, user_id):
    """Busca grupos públicos e verifica o status do usuário em relação a eles."""
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return []
    groups = []
    try:
        cursor = cnx.cursor(dictionary=True)
        query = """
            SELECT 
                g.idGrupo, g.nome, g.descricao,
                (CASE WHEN ug.idUsuario IS NOT NULL THEN 1 ELSE 0 END) AS is_member,
                (CASE WHEN n.idNotificacao IS NOT NULL THEN 1 ELSE 0 END) AS is_pending
            FROM Grupo g
            LEFT JOIN Usuario_Grupo ug ON g.idGrupo = ug.idGrupo AND ug.idUsuario = %s
            LEFT JOIN Notificacao n ON g.idGrupo = n.origem_id 
                                    AND n.idUsuarioSolicitante = %s 
                                    AND n.tipo = 'solicitacao_grupo' 
                                    AND n.status = 'pendente'
            WHERE g.nome LIKE %s AND g.tipo = 'público'
            GROUP BY g.idGrupo, g.nome, g.descricao, is_member, is_pending
        """
        like_term = f"%{search_term}%"
        cursor.execute(query, (user_id, user_id, like_term))
        groups = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Erro ao buscar grupos: {err}")
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()
    return groups

def request_group_entry(user_id, group_id, user_name, group_name):
    """Cria notificações para todos os moderadores de um grupo."""
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return False, "Erro de conexão."
    
    try:
        cursor = cnx.cursor(dictionary=True)
        
        cursor.execute("SELECT idModerador FROM Grupo_Moderador WHERE idGrupo = %s", (group_id,))
        moderators = cursor.fetchall()
        
        if not moderators:
            return False, "Este grupo não possui moderadores para aprovar a entrada."

        insert_query = """
            INSERT INTO Notificacao 
            (idUsuarioDestinatario, tipo, origem_id, preview, status, idUsuarioSolicitante) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        tipo = 'solicitacao_grupo'
        preview = f"{user_name} quer entrar no grupo {group_name}."
        status = 'pendente'
        
        for mod in moderators:
            mod_id = mod['idModerador']
            params = (mod_id, tipo, group_id, preview, status, user_id)
            cursor.execute(insert_query, params)
            
        cnx.commit()
        return True, "Solicitação enviada com sucesso!"
        
    except mysql.connector.Error as err:
        cnx.rollback()
        if err.errno == errorcode.ER_DUP_ENTRY:
             return False, "Uma solicitação já foi enviada."
        print(f"Erro ao solicitar entrada: {err}")
        return False, f"Erro de BD: {err}"
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()

def fetch_moderator_notifications(moderator_id):
    """Busca solicitações de entrada pendentes para os grupos que o usuário modera."""
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return []
    notifications = []
    try:
        cursor = cnx.cursor(dictionary=True)
        query = """
            SELECT 
                n.idNotificacao, n.idUsuarioSolicitante, n.origem_id,
                u.nome AS solicitante_nome, 
                g.nome AS grupo_nome
            FROM Notificacao n
            JOIN Usuario u ON n.idUsuarioSolicitante = u.idUsuario
            JOIN Grupo g ON n.origem_id = g.idGrupo
            WHERE n.idUsuarioDestinatario = %s 
              AND n.tipo = 'solicitacao_grupo' 
              AND n.status = 'pendente'
        """
        cursor.execute(query, (moderator_id,))
        notifications = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Erro ao buscar notificações: {err}")
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()
    return notifications

def approve_group_request(notification_id, user_id, group_id):
    """
    Aprova a entrada de um usuário no grupo, limpa a notificação,
    CRIA O CHAT (se não existir) E ADICIONA O USUÁRIO AO CHAT.
    """
    cnx = get_connection(db_name=DB_NAME)
    if not cnx:
        return False, "Erro de conexão."
    
    try:
        cursor = cnx.cursor(dictionary=True)
        
        cursor.execute("INSERT IGNORE INTO Usuario_Grupo (idUsuario, idGrupo) VALUES (%s, %s)", (user_id, group_id))

        chat_id = None
        
        cursor.execute("SELECT idChat FROM Chat WHERE idGrupo_FK = %s AND tipo = 'grupo'", (group_id,))
        chat_result = cursor.fetchone()
        
        if chat_result:
            chat_id = chat_result['idChat']
        else:
            print(f"AVISO: O Grupo {group_id} não possuía um Chat. Criando novo chat de grupo...")
            try:
                cursor.execute("INSERT INTO Chat (tipo, idGrupo_FK) VALUES ('grupo', %s)", (group_id,))
                chat_id = cursor.lastrowid
                print(f"Novo Chat (ID: {chat_id}) criado e associado ao Grupo {group_id}.")
            except mysql.connector.Error as err_chat:
                print(f"ERRO CRÍTICO ao tentar criar o Chat para o Grupo {group_id}: {err_chat}")
                cnx.rollback()
                return False, f"Erro ao criar chat: {err_chat}"
        
        if chat_id:
            cursor.execute("INSERT IGNORE INTO Usuario_Chat (idUsuario, idChat) VALUES (%s, %s)", (user_id, chat_id))
        else:
             print(f"ERRO: Não foi possível associar o usuário {user_id} ao chat do grupo {group_id}.")

        cursor.execute("UPDATE Notificacao SET status = 'aprovada' WHERE idNotificacao = %s", (notification_id,))
        
        cursor.execute("""
            UPDATE Notificacao 
            SET status = 'rejeitada' 
            WHERE idUsuarioSolicitante = %s 
              AND origem_id = %s 
              AND tipo = 'solicitacao_grupo' 
              AND status = 'pendente'
        """, (user_id, group_id))
        
        cnx.commit()
        return True, "Usuário aprovado."
        
    except mysql.connector.Error as err:
        cnx.rollback()
        print(f"Erro ao aprovar: {err}")
        return False, str(err)
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()

def reject_group_request(notification_id):
    """Rejeita a entrada de um usuário."""
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return False, "Erro de conexão."
    try:
        cursor = cnx.cursor()
        cursor.execute("UPDATE Notificacao SET status = 'rejeitada' WHERE idNotificacao = %s", (notification_id,))
        cnx.commit()
        return True, "Solicitação rejeitada."
    except mysql.connector.Error as err:
        cnx.rollback()
        print(f"Erro ao rejeitar: {err}")
        return False, str(err)
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()

def search_users_to_invite(search_term, current_user_id):
    """Busca usuários para convidar, excluindo o próprio usuário."""
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return []
    users = []
    try:
        cursor = cnx.cursor(dictionary=True)
        query = "SELECT idUsuario, nome, email FROM Usuario WHERE nome LIKE %s AND idUsuario != %s"
        cursor.execute(query, (f"%{search_term}%", current_user_id))
        users = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Erro ao buscar usuários: {err}")
    finally:
        if cnx.is_connected(): cursor.close(); cnx.close()
    return users

def create_group_with_invites(creator_id, group_name, group_desc, invited_user_ids):
    """
    Cria grupo, define criador como moderador e envia notificações de convite.
    """
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return False, "Erro de conexão."
    
    try:
        cursor = cnx.cursor()
        
        # 1. Criar o Grupo
        cursor.execute("INSERT INTO Grupo (nome, descricao, tipo) VALUES (%s, %s, 'público')", (group_name, group_desc))
        group_id = cursor.lastrowid
        
        # 2. Adicionar criador como Membro e Moderador
        cursor.execute("INSERT INTO Usuario_Grupo (idUsuario, idGrupo) VALUES (%s, %s)", (creator_id, group_id))
        
        # Verifica se o criador já é moderador na tabela 'Moderador', se não, insere
        cursor.execute("INSERT IGNORE INTO Moderador (idModerador) VALUES (%s)", (creator_id,))
        cursor.execute("INSERT INTO Grupo_Moderador (idGrupo, idModerador) VALUES (%s, %s)", (group_id, creator_id))
        
        # 3. Criar o Chat do Grupo
        cursor.execute("INSERT INTO Chat (tipo, idGrupo_FK) VALUES ('grupo', %s)", (group_id,))
        chat_id = cursor.lastrowid
        
        # 4. Adicionar criador ao Chat
        cursor.execute("INSERT INTO Usuario_Chat (idUsuario, idChat) VALUES (%s, %s)", (creator_id, chat_id))
        
        # 5. Criar Notificações para os convidados
        if invited_user_ids:
            notif_query = """
                INSERT INTO Notificacao (idUsuarioDestinatario, idUsuarioSolicitante, tipo, origem_id, preview, status)
                VALUES (%s, %s, 'convite_grupo', %s, %s, 'pendente')
            """
            preview_text = f"Você foi convidado para entrar no grupo '{group_name}'."
            for guest_id in invited_user_ids:
                cursor.execute(notif_query, (guest_id, creator_id, group_id, preview_text))
        
        cnx.commit()
        return True, "Grupo criado e convites enviados!"
        
    except mysql.connector.Error as err:
        cnx.rollback()
        print(f"Erro ao criar grupo: {err}")
        return False, str(err)
    finally:
        if cnx.is_connected(): cursor.close(); cnx.close()

def fetch_all_notifications(user_id):
    """Busca TANTO solicitações de entrada (se for mod) QUANTO convites recebidos."""
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return []
    notifications = []
    try:
        cursor = cnx.cursor(dictionary=True)
        query = """
            SELECT n.*, u.nome as nome_remetente, g.nome as nome_grupo
            FROM Notificacao n
            JOIN Usuario u ON n.idUsuarioSolicitante = u.idUsuario
            JOIN Grupo g ON n.origem_id = g.idGrupo
            WHERE n.idUsuarioDestinatario = %s AND n.status = 'pendente'
            ORDER BY n.dataEnvio DESC
        """
        cursor.execute(query, (user_id,))
        notifications = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Erro ao buscar notificações: {err}")
    finally:
        if cnx.is_connected(): cursor.close(); cnx.close()
    return notifications

def accept_group_invite(notification_id, user_id, group_id):
    """Usuário aceita um convite para entrar no grupo."""
    cnx = get_connection(db_name=DB_NAME)
    if not cnx: return False, "Conexão falhou."
    try:
        cursor = cnx.cursor(dictionary=True)
        
        # Adiciona ao grupo
        cursor.execute("INSERT IGNORE INTO Usuario_Grupo (idUsuario, idGrupo) VALUES (%s, %s)", (user_id, group_id))
        
        # Busca o chat e adiciona
        cursor.execute("SELECT idChat FROM Chat WHERE idGrupo_FK = %s", (group_id,))
        chat = cursor.fetchone()
        if chat:
            cursor.execute("INSERT IGNORE INTO Usuario_Chat (idUsuario, idChat) VALUES (%s, %s)", (user_id, chat['idChat']))
        
        # Atualiza notificação
        cursor.execute("UPDATE Notificacao SET status = 'aprovada' WHERE idNotificacao = %s", (notification_id,))
        cnx.commit()
        return True, "Convite aceito!"
    except mysql.connector.Error as err:
        cnx.rollback()
        return False, str(err)
    finally:
        if cnx.is_connected(): cursor.close(); cnx.close()

# --- 2. Gerenciamento de Sessão (Inalterado) ---

def set_login_status(logged_in_id=None):
    try:
        with open(SESSION_FILE, 'w') as f:
            if logged_in_id:
                f.write(f"LOGGED_IN_ID={logged_in_id}")
            else:
                f.write("LOGGED_IN_ID=")
        return True
    except IOError as e:
        print(f"Erro ao escrever no arquivo de sessão: {e}")
        return False

def check_login_status():
    if not os.path.exists(SESSION_FILE): return None
    try:
        with open(SESSION_FILE, 'r') as f:
            line = f.readline().strip()
            if line.startswith("LOGGED_IN_ID=") and len(line) > 13:
                return int(line.split('=')[1])
    except (IOError, ValueError, IndexError) as e:
        print(f"Erro ao ler arquivo de sessão: {e}")
    return None

# --- 3. Classes da Interface Gráfica (GUI) ---

# --- PÁGINA 1: FRAME DE CHAT ---
class ChatFrame(ctk.CTkFrame):
    """Este Frame contém a interface de chat (sidebar e área de mensagens)."""
    
    def __init__(self, master, user_id, user_details):
        super().__init__(master, fg_color="transparent")
        
        self.user_id = user_id
        self.user_name = user_details.get('nome', 'Usuário')
        self.current_chat_id = None
        self.chats_info = {} 
        
        # --- NOVO: Controlador de Áudio ---
        self.recorder = chat_media.AudioRecorder()
        self.is_recording = False
        # ----------------------------------

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=200) 
        self.grid_columnconfigure(1, weight=4) 

        self.create_sidebar()
        self.create_chat_area()
        self.load_user_chats()

    def send_file_handler(self):
        if self.current_chat_id is None: return
        file_path = filedialog.askopenfilename()
        if file_path:
            saved_path = chat_media.save_attachment(file_path)
            # Envia como tipo 'arquivo'
            post_new_message(self.current_chat_id, self.user_id, "Enviou um arquivo", "arquivo", saved_path)
            self.load_messages()

    def toggle_recording(self):
        if self.current_chat_id is None: return
        
        if not self.is_recording:
            # Começar a gravar
            self.is_recording = True
            self.recorder.start_recording()
            self.record_btn.configure(fg_color="red", text="⏹") # Vira botão de parar
        else:
            # Parar e Enviar
            self.is_recording = False
            self.record_btn.configure(fg_color=CTK_THEME_COLORS["secondary"], text="🎤")
            audio_path = self.recorder.stop_recording()
            if audio_path:
                post_new_message(self.current_chat_id, self.user_id, "Mensagem de Voz", "audio", audio_path)
                self.load_messages()

    def send_message_handler(self, event=None):
        """Envia uma mensagem de texto simples"""
        if self.current_chat_id is None:
            return

        text = self.message_entry.get().strip()
        if not text:
            return

        # Chama a função do banco de dados para salvar (tipo 'texto')
        success, msg_status = post_new_message(self.current_chat_id, self.user_id, text, 'texto')
        
        if success:
            self.message_entry.delete(0, "end") # Limpa o campo de texto
            self.load_messages() # Recarrega o chat
        else:
            messagebox.showerror("Erro", f"Não foi possível enviar: {msg_status}")

    def create_sidebar(self):
        sidebar_frame = ctk.CTkFrame(self, fg_color=CTK_THEME_COLORS["bg_card"], corner_radius=10)
        sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=0)
        
        sidebar_frame.grid_rowconfigure(1, weight=1)
        sidebar_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(sidebar_frame, text="Meus Chats", font=ctk.CTkFont(size=18, weight="bold"), text_color=CTK_THEME_COLORS["primary"])
        title_label.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self.chat_list_frame = ctk.CTkScrollableFrame(sidebar_frame, fg_color="transparent")
        self.chat_list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    def create_chat_area(self):
        # ... (código anterior igual até chegar no input_frame) ...
        chat_area_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        chat_area_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=0)
        chat_area_frame.grid_rowconfigure(1, weight=1) # area mensagens
        
        self.chat_title_label = ctk.CTkLabel(chat_area_frame, text="Selecione um chat...", font=ctk.CTkFont(size=16, weight="bold"), text_color=CTK_THEME_COLORS["text_dark"])
        self.chat_title_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(0, 10))

        self.messages_frame = ctk.CTkScrollableFrame(chat_area_frame, fg_color=CTK_THEME_COLORS["bg_card"], corner_radius=10)
        self.messages_frame.grid(row=1, column=0, sticky="nsew")
        self.messages_frame.grid_columnconfigure(0, weight=1)

        # --- ÁREA DE INPUT MODIFICADA ---
        input_frame = ctk.CTkFrame(chat_area_frame, fg_color="transparent")
        input_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.message_entry = ctk.CTkEntry(input_frame, placeholder_text="Digite...", height=40)
        self.message_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.message_entry.bind("<Return>", self.send_message_handler)

        # Botão Anexar Arquivo (📎)
        self.attach_btn = ctk.CTkButton(input_frame, text="📎", width=40, height=40, 
                                        fg_color=CTK_THEME_COLORS["secondary"], command=self.send_file_handler)
        self.attach_btn.grid(row=0, column=1, padx=2)

        # Botão Gravar Áudio (🎤)
        self.record_btn = ctk.CTkButton(input_frame, text="🎤", width=40, height=40, 
                                        fg_color=CTK_THEME_COLORS["secondary"], command=self.toggle_recording)
        self.record_btn.grid(row=0, column=2, padx=2)

        # Botão Enviar
        self.send_button = ctk.CTkButton(input_frame, text="Enviar", width=60, height=40, command=self.send_message_handler)
        self.send_button.grid(row=0, column=3, padx=(5,0))

    def load_user_chats(self):
        chat_ids = fetch_user_chats(self.user_id)
        if not chat_ids:
            ctk.CTkLabel(self.chat_list_frame, text="Nenhum chat encontrado.").pack(pady=10)
            return
        for chat_id in chat_ids:
            details = get_chat_details(chat_id, self.user_id)
            if details:
                self.chats_info[chat_id] = details
                chat_name = details['name']
                if len(chat_name) > 25: chat_name = chat_name[:22] + "..."
                chat_button = ctk.CTkButton(
                    self.chat_list_frame, text=chat_name, 
                    fg_color=CTK_THEME_COLORS["bg_main"],
                    text_color=CTK_THEME_COLORS["text_dark"],
                    hover_color=CTK_THEME_COLORS["secondary"],
                    anchor="w",
                    command=lambda c_id=chat_id: self.select_chat(c_id)
                )
                chat_button.pack(fill="x", pady=4, padx=5)

    def select_chat(self, chat_id):
        self.current_chat_id = chat_id
        chat_details = self.chats_info[chat_id]
        self.chat_title_label.configure(text=chat_details['name'])
        self.send_button.configure(state="normal")
        self.message_entry.delete(0, "end")
        self.load_messages()

    def load_messages(self):
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        if self.current_chat_id is None: return 
        
        messages = fetch_messages(self.current_chat_id, self.user_id)
        
        if not messages:
            ctk.CTkLabel(self.messages_frame, text="Sem mensagens.").pack(pady=10)
            return

        for msg in messages:
            is_own = (str(msg['idUsuario']) == str(self.user_id))
            
            # Configuração Visual (Direita/Esquerda)
            if is_own:
                anchor = "e"; justify = "right"
                bg_color = CTK_THEME_COLORS["primary"]
                text_color = "white"
            else:
                anchor = "w"; justify = "left"
                bg_color = CTK_THEME_COLORS["bg_main"]
                text_color = CTK_THEME_COLORS["text_dark"]

            # Container da Linha (para agrupar msg + lixeira)
            row_frame = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2, padx=10, anchor=anchor)

            # --- Botão de Lixeira (Só aparece se for mensagem própria) ---
            if is_own:
                trash_btn = ctk.CTkButton(row_frame, text="🗑️", width=25, height=25, 
                                          fg_color="transparent", text_color="red", hover_color="#fee2e2",
                                          font=ctk.CTkFont(size=14),
                                          command=lambda mid=msg['idMensagem']: self.delete_msg_handler(mid))
                # Empacota ANTES do balão se estiver à direita
                trash_btn.pack(side="left", padx=(0, 5))

            # --- Balão da Mensagem ---
            bubble = ctk.CTkFrame(row_frame, fg_color=bg_color, corner_radius=10)
            bubble.pack(side="left" if not is_own else "right") # Se não é meu, fica na esquerda

            # Cabeçalho (Nome e Hora)
            try: time_str = msg['dataEnvio'].strftime("%H:%M")
            except: time_str = ""
            header_txt = f"Você ({time_str})" if is_own else f"{msg['remetente']} ({time_str})"
            
            ctk.CTkLabel(bubble, text=header_txt, font=ctk.CTkFont(size=10, slant="italic"), 
                         text_color="white" if is_own else "gray").pack(padx=8, pady=(4,0), anchor="w")

            # --- Conteúdo da Mensagem (Texto, Arquivo ou Áudio) ---
            msg_type = msg.get('tipo', 'texto')
            file_path = msg.get('caminho_arquivo')

            if msg_type == 'texto':
                wrapped = textwrap.fill(msg['conteudo'], width=50)
                ctk.CTkLabel(bubble, text=wrapped, text_color=text_color, justify=justify).pack(padx=10, pady=5)
            
            elif msg_type == 'arquivo':
                btn_text = f"📄 Arquivo: {msg['conteudo']}"
                ctk.CTkButton(bubble, text=btn_text, fg_color="white", text_color="black", hover_color="#d1d5db",
                              command=lambda p=file_path: self.open_file(p)).pack(padx=10, pady=5)
            
            elif msg_type == 'audio':
                ctk.CTkButton(bubble, text="▶ Reproduzir Áudio", fg_color="#10b981", hover_color="#059669",
                              command=lambda p=file_path: self.open_file(p)).pack(padx=10, pady=5)

    def open_file(self, path):
        """Abre o arquivo usando o sistema operacional"""
        if path and os.path.exists(path):
            try:
                if os.name == 'nt': # Windows
                    os.startfile(path)
                else: # Linux/Mac
                    subprocess.call(('xdg-open', path))
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível abrir o arquivo: {e}")
        else:
            messagebox.showwarning("Erro", "Arquivo não encontrado (pode ter sido movido).")

    def delete_msg_handler(self, msg_id):
        if messagebox.askyesno("Confirmar", "Deseja apagar esta mensagem?"):
            if delete_message(msg_id):
                self.load_messages()
            else:
                messagebox.showerror("Erro", "Falha ao apagar.")

# --- PÁGINA 2: FRAME DE GRUPOS (Inalterado) ---
class GrupoFrame(ctk.CTkFrame):
    """Este Frame contém a busca de grupos e os resultados."""
    
    def __init__(self, master, user_id, user_name):
        super().__init__(master, fg_color="transparent")
        
        self.user_id = user_id
        self.user_name = user_name

        self.grid_rowconfigure(2, weight=1) # Linha para os resultados
        self.grid_columnconfigure(0, weight=1)

        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=0, column=0, padx=50, pady=30, sticky="ew")
        content_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(content_frame, text="Procurar Grupos", font=ctk.CTkFont(size=24, weight="bold"), text_color=CTK_THEME_COLORS["text_dark"])
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        self.search_entry = ctk.CTkEntry(content_frame, placeholder_text="Digite o nome do grupo...", height=40, border_width=0, fg_color=CTK_THEME_COLORS["bg_card"])
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        
        self.search_button = ctk.CTkButton(content_frame, text="Procurar", height=40, command=self.perform_search)
        self.search_button.grid(row=1, column=1, sticky="e")
        
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
        
        self.results_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.results_frame.grid(row=2, column=0, padx=50, pady=(0, 20), sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1) 
        
        self.info_label = ctk.CTkLabel(self.results_frame, text="Digite um termo de busca para encontrar grupos.", text_color=CTK_THEME_COLORS["text_light"], font=ctk.CTkFont(size=14))
        self.info_label.pack(pady=20)

    def perform_search(self, event=None):
        search_term = self.search_entry.get().strip()
        
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        if not search_term:
            self.info_label = ctk.CTkLabel(self.results_frame, text="Digite um termo de busca para encontrar grupos.", text_color=CTK_THEME_COLORS["text_light"], font=ctk.CTkFont(size=14))
            self.info_label.pack(pady=20)
            return

        results = search_groups(search_term, self.user_id)
        
        if not results:
            self.info_label = ctk.CTkLabel(self.results_frame, text="Nenhum grupo encontrado.", text_color=CTK_THEME_COLORS["text_light"], font=ctk.CTkFont(size=14))
            self.info_label.pack(pady=20)
            return

        results = search_groups(search_term, self.user_id)
        
        if not results:
            self.info_label = ctk.CTkLabel(self.results_frame, text="Nenhum grupo encontrado.", text_color=CTK_THEME_COLORS["text_light"], font=ctk.CTkFont(size=14))
            self.info_label.pack(pady=20)
            return
            
        for group in results:
            self.create_group_card(group)

    def create_group_card(self, group):
        card = ctk.CTkFrame(self.results_frame, fg_color=CTK_THEME_COLORS["bg_card"], corner_radius=8)
        card.pack(fill="x", pady=5, padx=0) # padx=0 para usar o espaço todo
        
        card.grid_columnconfigure(0, weight=1) # Coluna do texto
        card.grid_columnconfigure(1, weight=0) # Coluna do botão
        
        # Frame para os textos (nome e descrição)
        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.grid(row=0, column=0, padx=15, pady=(10, 10), sticky="w")

        nome = ctk.CTkLabel(text_frame, text=group['nome'], font=ctk.CTkFont(size=16, weight="bold"), text_color=CTK_THEME_COLORS["text_dark"])
        nome.pack(anchor="w")
        
        desc = ctk.CTkLabel(text_frame, text=group['descricao'], font=ctk.CTkFont(size=12), text_color=CTK_THEME_COLORS["text_light"], justify="left")
        desc.pack(anchor="w", pady=(2, 0))

        # Lógica dos botões (Membro, Pendente, Solicitar)
        if group['is_member'] == 1:
            status_button = ctk.CTkButton(card, text="Membro", state="disabled", fg_color=CTK_THEME_COLORS["nav_button_default"], height=30, width=110)
        elif group['is_pending'] == 1:
            status_button = ctk.CTkButton(card, text="Pendente", state="disabled", fg_color=CTK_THEME_COLORS["secondary"], height=30, width=110)
        else:
            status_button = ctk.CTkButton(
                card, 
                text="Solicitar Entrada", 
                fg_color=CTK_THEME_COLORS["primary"], 
                height=30,
                width=110,
                command=lambda g_id=group['idGrupo'], g_name=group['nome']: self.handle_request_entry(g_id, g_name)
            )
        
        status_button.grid(row=0, column=1, padx=15, sticky="e")

    def handle_request_entry(self, group_id, group_name):
        success, message = request_group_entry(self.user_id, group_id, self.user_name, group_name)
        
        if success:
            messagebox.showinfo("Sucesso", message)
            # Atualiza a busca para mostrar o botão como "Pendente"
            self.perform_search()
        else:
            messagebox.showwarning("Erro", message)

# --- PÁGINA 4: FRAME DE MODERAÇÃO (NOVO) ---
class CriarGrupoFrame(ctk.CTkFrame):
    def __init__(self, master, user_id):
        super().__init__(master, fg_color="transparent")
        self.user_id = user_id
        self.invited_users = [] # Lista de IDs selecionados (tuple: id, nome)

        self.grid_columnconfigure(0, weight=1) # Formuário
        self.grid_columnconfigure(1, weight=1) # Busca de Pessoas
        self.grid_rowconfigure(0, weight=1)

        # --- LADO ESQUERDO: Dados do Grupo ---
        left_frame = ctk.CTkFrame(self, fg_color=CTK_THEME_COLORS["bg_card"])
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(left_frame, text="Criar Novo Grupo", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        self.name_entry = ctk.CTkEntry(left_frame, placeholder_text="Nome do Grupo")
        self.name_entry.pack(fill="x", padx=20, pady=10)
        
        self.desc_entry = ctk.CTkEntry(left_frame, placeholder_text="Descrição do Grupo")
        self.desc_entry.pack(fill="x", padx=20, pady=10)

        # Lista visual de convidados selecionados
        ctk.CTkLabel(left_frame, text="Participantes Selecionados:", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        self.selected_list_box = ctk.CTkTextbox(left_frame, height=150)
        self.selected_list_box.pack(fill="x", padx=20, pady=5)
        self.selected_list_box.configure(state="disabled")

        self.create_btn = ctk.CTkButton(left_frame, text="Criar Grupo", fg_color=CTK_THEME_COLORS["success"], command=self.submit_group)
        self.create_btn.pack(pady=20)

        # --- LADO DIREITO: Buscar Pessoas ---
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(right_frame, text="Convidar Participantes", font=ctk.CTkFont(size=16)).pack(pady=10)
        
        search_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        search_frame.pack(fill="x")
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Buscar usuário...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(search_frame, text="Buscar", width=60, command=self.perform_user_search).pack(side="right")

        self.results_scroll = ctk.CTkScrollableFrame(right_frame, fg_color=CTK_THEME_COLORS["bg_card"])
        self.results_scroll.pack(fill="both", expand=True, pady=10)

    def perform_user_search(self):
        term = self.search_entry.get()
        for widget in self.results_scroll.winfo_children(): widget.destroy()
        
        users = search_users_to_invite(term, self.user_id)
        if not users:
            ctk.CTkLabel(self.results_scroll, text="Ninguém encontrado.").pack(pady=10)
            return

        for u in users:
            # Verifica se já está na lista de convidados
            if any(invited[0] == u['idUsuario'] for invited in self.invited_users):
                continue

            row = ctk.CTkFrame(self.results_scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=u['nome']).pack(side="left", padx=5)
            ctk.CTkButton(row, text="+", width=30, command=lambda usr=u: self.add_user(usr)).pack(side="right", padx=5)

    def add_user(self, user):
        self.invited_users.append((user['idUsuario'], user['nome']))
        self.update_selected_display()
        self.perform_user_search() # Atualiza para remover o botão "+"

    def update_selected_display(self):
        self.selected_list_box.configure(state="normal")
        self.selected_list_box.delete("0.0", "end")
        text = "\n".join([f"- {u[1]}" for u in self.invited_users])
        self.selected_list_box.insert("0.0", text)
        self.selected_list_box.configure(state="disabled")

    def submit_group(self):
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()
        
        if not name:
            messagebox.showwarning("Aviso", "O grupo precisa de um nome.")
            return

        invited_ids = [u[0] for u in self.invited_users]
        success, msg = create_group_with_invites(self.user_id, name, desc, invited_ids)
        
        if success:
            messagebox.showinfo("Sucesso", msg)
            self.name_entry.delete(0, "end")
            self.desc_entry.delete(0, "end")
            self.invited_users = []
            self.update_selected_display()
        else:
            messagebox.showerror("Erro", msg)


class NotificacoesFrame(ctk.CTkFrame):
    """Mostra convites e solicitações de moderação."""
    def __init__(self, master, user_id):
        super().__init__(master, fg_color="transparent")
        self.user_id = user_id
        
        ctk.CTkLabel(self, text="Notificações e Solicitações", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20, padx=20, anchor="w")
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.refresh_btn = ctk.CTkButton(self, text="Atualizar Lista", command=self.load_notifs)
        self.refresh_btn.pack(pady=10)
        
        self.load_notifs()

    def load_notifs(self):
        for w in self.scroll.winfo_children(): w.destroy()
        
        notifs = fetch_all_notifications(self.user_id)
        if not notifs:
            ctk.CTkLabel(self.scroll, text="Nenhuma notificação pendente.").pack(pady=20)
            return

        for n in notifs:
            card = ctk.CTkFrame(self.scroll, fg_color=CTK_THEME_COLORS["bg_card"])
            card.pack(fill="x", pady=5)
            
            # Texto descritivo
            msg = n['preview']
            if n['tipo'] == 'solicitacao_grupo':
                title = "Solicitação de Entrada"
                color = CTK_THEME_COLORS["text_dark"][0] # Ajuste simples de cor
            else:
                title = "Convite de Grupo"
                color = CTK_THEME_COLORS["primary"]
                
            ctk.CTkLabel(card, text=title, text_color=color, font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
            ctk.CTkLabel(card, text=msg, wraplength=400).pack(anchor="w", padx=10, pady=(0,5))
            
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=5)
            
            # Ações diferem por tipo
            if n['tipo'] == 'solicitacao_grupo':
                # Eu sou moderador, aprovo ou rejeito a entrada dele
                ctk.CTkButton(btn_frame, text="Aprovar", width=80, fg_color="green", 
                              command=lambda nid=n['idNotificacao'], uid=n['idUsuarioSolicitante'], gid=n['origem_id']: self.mod_action(nid, uid, gid, True)).pack(side="right", padx=5)
                ctk.CTkButton(btn_frame, text="Rejeitar", width=80, fg_color="red", 
                              command=lambda nid=n['idNotificacao']: self.mod_action(nid, None, None, False)).pack(side="right", padx=5)
            
            elif n['tipo'] == 'convite_grupo':
                # Eu fui convidado, aceito ou recuso entrar
                ctk.CTkButton(btn_frame, text="Aceitar", width=80, fg_color="green",
                              command=lambda nid=n['idNotificacao'], gid=n['origem_id']: self.invite_action(nid, gid, True)).pack(side="right", padx=5)
                ctk.CTkButton(btn_frame, text="Recusar", width=80, fg_color="red",
                              command=lambda nid=n['idNotificacao']: self.invite_action(nid, None, False)).pack(side="right", padx=5)

    def mod_action(self, nid, uid, gid, approved):
        if approved:
            approve_group_request(nid, uid, gid)
            messagebox.showinfo("Feito", "Usuário aprovado.")
        else:
            reject_group_request(nid)
            messagebox.showinfo("Feito", "Solicitação rejeitada.")
        self.load_notifs()

    def invite_action(self, nid, gid, accepted):
        if accepted:
            accept_group_invite(nid, self.user_id, gid)
            messagebox.showinfo("Bem-vindo", "Você entrou no grupo!")
        else:
            reject_group_request(nid) 
            messagebox.showinfo("Recusado", "Convite removido.")
        self.load_notifs()

# --- PÁGINA 3: FRAME DE PERFIL ---
class PerfilFrame(ctk.CTkFrame):
    """Este Frame contém as informações de perfil e o botão de logout."""
    
    def __init__(self, master, app, user_details):
        super().__init__(master, fg_color="transparent")
        
        self.app = app # Referência ao HubApp para chamar on_closing
        self.user_details = user_details
        self.user_name = user_details.get('nome', 'N/A')

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Linha do meio (espaçador)
        self.grid_rowconfigure(2, weight=0) # Logout

        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=0, column=0, padx=50, pady=30, sticky="new")
        content_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(content_frame, text="Meu Perfil", font=ctk.CTkFont(size=24, weight="bold"), text_color=CTK_THEME_COLORS["text_dark"])
        title.pack(anchor="w", pady=(0, 20))

        name_label = ctk.CTkLabel(content_frame, text=f"Nome: {self.user_name}", font=ctk.CTkFont(size=16), text_color=CTK_THEME_COLORS["text_dark"])
        name_label.pack(anchor="w", pady=5)

        email_label = ctk.CTkLabel(content_frame, text=f"Email: {self.user_details.get('email', 'N/A')}", font=ctk.CTkFont(size=16), text_color=CTK_THEME_COLORS["text_dark"])
        email_label.pack(anchor="w", pady=5)
        
        age_label = ctk.CTkLabel(content_frame, text=f"Idade: {self.user_details.get('idade', 'N/A')}", font=ctk.CTkFont(size=16), text_color=CTK_THEME_COLORS["text_dark"])
        age_label.pack(anchor="w", pady=5)

        edit_button = ctk.CTkButton(content_frame, text="Editar Informações (Em Breve)", state="disabled", fg_color=CTK_THEME_COLORS["Terceira"], height=40)
        edit_button.pack(anchor="w", pady=20)

        # --- NOVO: Switch de Modo Escuro ---
        self.dark_mode_switch = ctk.CTkSwitch(
            content_frame, 
            text="Modo Escuro", 
            command=self.toggle_dark_mode,
            text_color=CTK_THEME_COLORS["text_dark"] # Texto do switch também muda de cor
        )
        self.dark_mode_switch.pack(anchor="w", pady=20)

        # Define o estado inicial do switch
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            self.dark_mode_switch.select()
        else:
            self.dark_mode_switch.deselect()

        # Botão de Logout
        logout_button = ctk.CTkButton(
            self, 
            text="Logout (Sair)", 
            command=self.app.on_closing, 
            fg_color=CTK_THEME_COLORS["danger"], 
            hover_color="#be123c", 
            height=40,
            width=200
        )
        logout_button.grid(row=2, column=0, padx=50, pady=30, sticky="s")

    def toggle_dark_mode(self):
        """Muda o tema do app entre claro e escuro."""
        current_mode = self.dark_mode_switch.get() # 1 = on (dark), 0 = off (light)
        
        if current_mode == 1:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")



# --- CLASSE PRINCIPAL: HubApp (MODIFICADA para Moderação) ---
class HubApp(ctk.CTk):
    def __init__(self, user_id, user_details):
        super().__init__()
        
        self.iconbitmap(resource_path("testelogo.ico"))

        self.user_id = user_id
        self.user_details = user_details 
        self.user_name = user_details.get('nome', 'Usuário')

        self.title(f"Sistema Educacional - Bem-vindo(a), {self.user_name}")
        self.geometry("900x600")
        self.configure(fg_color=CTK_THEME_COLORS["bg_main"])
        
        self.grid_rowconfigure(0, weight=1) 
        self.grid_rowconfigure(1, weight=0) 
        self.grid_columnconfigure(0, weight=1)

        self.main_content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

        self.nav_frame = ctk.CTkFrame(self, fg_color=CTK_THEME_COLORS["bg_card"], height=60, corner_radius=10)
        self.nav_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.nav_frame.grid_rowconfigure(0, weight=1)
        
        self.frames = {}
        
        # --- LÓGICA DE MODERAÇÃO ---
        self.is_moderator = check_user_moderator_status(self.user_id)
        
        # Define as páginas
        # --- ATUALIZAÇÃO DA LISTA DE PÁGINAS ---
        # Agora todos têm acesso a notificações e a criar grupos
        pages = [
            (ChatFrame, "chat"),
            (GrupoFrame, "grupos"),
            (CriarGrupoFrame, "criar"),        # NOVA ABA
            (NotificacoesFrame, "notificações"), # SUBSTITUI MODERAÇÃO ANTIGA
            (PerfilFrame, "perfil")
        ]
        
        # Configura as colunas da barra de navegação
        for i in range(len(pages)):
            self.nav_frame.grid_columnconfigure(i, weight=1)
            
        # Cria os frames
        for (F, name) in pages:
            if name == "chat":
                 frame = F(self.main_content_frame, user_id=self.user_id, user_details=self.user_details)
            elif name == "grupos":
                 frame = F(self.main_content_frame, user_id=self.user_id, user_name=self.user_name)
            elif name == "perfil":
                 frame = F(self.main_content_frame, app=self, user_details=self.user_details)
            elif name == "criar":  # Instanciando a nova classe
                 frame = F(self.main_content_frame, user_id=self.user_id)
            elif name == "notificações": # Instanciando a nova classe unificada
                 frame = F(self.main_content_frame, user_id=self.user_id)
            else:
                 frame = F(self.main_content_frame)
                 
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Cria os botões de navegação
        self.nav_buttons = {}
        
        col_index = 0
        for name in self.frames.keys():
            text = name.capitalize()
            button = ctk.CTkButton(
                self.nav_frame, text=text, height=40,
                fg_color=CTK_THEME_COLORS["nav_button_default"],
                command=lambda n=name: self.show_frame(n)
            )
            button.grid(row=0, column=col_index, padx=10, pady=10, sticky="ew")
            self.nav_buttons[name] = button
            col_index += 1

        self.show_frame("chat")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def show_frame(self, frame_name):
        default_color = CTK_THEME_COLORS["nav_button_default"]
        
        # Reseta todos os botões
        for button in self.nav_buttons.values():
            button.configure(fg_color=default_color)
        
        # Mostra o frame
        frame = self.frames[frame_name]
        frame.tkraise()
        
        # Destaca o botão ativo
        active_color = CTK_THEME_COLORS["primary"]
        self.nav_buttons[frame_name].configure(fg_color=active_color)

    def on_closing(self):
        if messagebox.askokcancel("Sair", "Deseja realmente sair e fazer logout?"):
            set_login_status(logged_in_id=None)
            self.destroy()
            login_app = LoginApp()
            login_app.mainloop()

# --- CLASSE LoginApp (Inalterada) ---
class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.iconbitmap(resource_path("testelogo.ico"))

        self.title("Login - Sistema de Chat")
        self.geometry("400x450")
        self.configure(fg_color=CTK_THEME_COLORS["bg_main"]) 
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self, fg_color=CTK_THEME_COLORS["bg_card"], corner_radius=15)
        main_frame.grid(row=0, column=0, padx=30, pady=30, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(main_frame, text="Bem-vindo!", font=ctk.CTkFont(size=24, weight="bold"), text_color=CTK_THEME_COLORS["primary"])
        title_label.grid(row=0, column=0, padx=30, pady=(30, 10))

        subtitle_label = ctk.CTkLabel(main_frame, text="Faça login ou crie sua conta.", font=ctk.CTkFont(size=14), text_color=CTK_THEME_COLORS["text_light"])
        subtitle_label.grid(row=1, column=0, padx=30, pady=(0, 20))

        self.tab_view = ctk.CTkTabview(main_frame, fg_color="transparent", 
                                       segmented_button_fg_color=CTK_THEME_COLORS["bg_main"], 
                                       segmented_button_selected_color=CTK_THEME_COLORS["primary"], 
                                       segmented_button_selected_hover_color="#3730a3")
        self.tab_view.grid(row=2, column=0, sticky="ew", padx=30, pady=10)
        self.tab_view.add("Login")
        self.tab_view.add("Criar Conta")
        
        self.create_login_tab(self.tab_view.tab("Login"))
        self.create_account_tab(self.tab_view.tab("Criar Conta"))

    def create_login_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        self.login_email_entry = ctk.CTkEntry(tab, placeholder_text="E-mail", height=40, border_width=0)
        self.login_email_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.login_pass_entry = ctk.CTkEntry(tab, placeholder_text="Senha", show="*", height=40, border_width=0)
        self.login_pass_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        login_button = ctk.CTkButton(tab, text="Entrar", height=40, command=self.handle_login, fg_color=CTK_THEME_COLORS["primary"])
        login_button.grid(row=2, column=0, sticky="ew", padx=10, pady=(10, 20))

    def create_account_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        self.create_name_entry = ctk.CTkEntry(tab, placeholder_text="Nome Completo", height=40, border_width=0)
        self.create_name_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.create_age_entry = ctk.CTkEntry(tab, placeholder_text="Idade", height=40, border_width=0)
        self.create_age_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.create_email_entry = ctk.CTkEntry(tab, placeholder_text="E-mail", height=40, border_width=0)
        self.create_email_entry.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.create_pass_entry = ctk.CTkEntry(tab, placeholder_text="Senha", show="*", height=40, border_width=0)
        self.create_pass_entry.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        create_button = ctk.CTkButton(tab, text="Criar Conta e Entrar", height=40, command=self.handle_create_account, fg_color=CTK_THEME_COLORS["secondary"])
        create_button.grid(row=4, column=0, sticky="ew", padx=10, pady=(10, 20))

    def get_credentials(self, is_creating=False):
        if is_creating:
            name = self.create_name_entry.get().strip()
            age_str = self.create_age_entry.get().strip()
            email = self.create_email_entry.get().strip()
            password = self.create_pass_entry.get().strip()
            if not (name and age_str and email and password):
                messagebox.showwarning("Campos Vazios", "Por favor, preencha todos os campos.")
                return None, None, None, None
            try:
                age = int(age_str)
                return name, age, email, password
            except ValueError:
                messagebox.showwarning("Idade Inválida", "Por favor, insira um número válido para a idade.")
                return None, None, None, None
        else:
            email = self.login_email_entry.get().strip()
            password = self.login_pass_entry.get().strip()
            if not (email and password):
                messagebox.showwarning("Campos Vazios", "Por favor, preencha e-mail e senha.")
                return None, None
            return email, password

    def handle_login(self):
        email, password = self.get_credentials()
        if not email: return
        
        user_id = validate_login(email, password)
        if user_id:
            if set_login_status(logged_in_id=user_id):
                user_details = fetch_user_details(user_id)
                self.destroy()
                hub_app = HubApp(user_id, user_details)
                hub_app.mainloop()
        else:
            messagebox.showerror("Falha no Login", "E-mail ou senha incorretos.")

    def handle_create_account(self):
        name, age, email, password = self.get_credentials(is_creating=True)
        if not name: return
        
        success, result = create_new_account(name, age, email, password)
        if success:
            new_id = result
            if set_login_status(logged_in_id=new_id):
                user_details = fetch_user_details(new_id)
                self.destroy()
                hub_app = HubApp(new_id, user_details)
                hub_app.mainloop()
        else:
            messagebox.showerror("Erro ao Criar Conta", result)


# --- 4. Execução Principal (Inalterada) ---
if __name__ == "__main__":
    if not get_connection(db_name=DB_NAME):
        root_temp = tk.Tk()
        root_temp.withdraw() 
        messagebox.showerror("ERRO FATAL", "Não foi possível conectar ao MySQL. Verifique se o servidor está rodando e se as credenciais em DB_CONFIG estão corretas.")
    else:
        logged_in_id = check_login_status()
        if logged_in_id:
            user_details = fetch_user_details(logged_in_id)
            if user_details:
                print(f"Sessão ativa encontrada para o usuário {logged_in_id}. Iniciando HubApp.")
                hub_app = HubApp(logged_in_id, user_details)
                hub_app.mainloop()
            else:
                print("ID da sessão inválido. Iniciando LoginApp.")
                set_login_status(logged_in_id=None)
                login_app = LoginApp()
                login_app.mainloop()
        else:
            print("Nenhuma sessão ativa. Iniciando LoginApp.")
            login_app = LoginApp()
            login_app.mainloop()
