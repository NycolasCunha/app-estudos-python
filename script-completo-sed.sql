-- ==============================================
-- 1. CRIAÇÃO DO BANCO (DO create_tables.sql)
-- ==============================================
-- (Simplificado para focar no banco de dados principal)
CREATE DATABASE IF NOT EXISTS SistemaDeChatEducacional;
USE SistemaDeChatEducacional;

-- ==============================================
-- 2. TABELAS PRINCIPAIS (DO create_tables.sql)
-- ==============================================

CREATE TABLE Usuario (
    idUsuario INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    idade INT,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL
);

-- Tabela de Notificações
CREATE TABLE IF NOT EXISTS Notificacao (
    idNotificacao INT PRIMARY KEY AUTO_INCREMENT,
    idUsuarioDestinatario INT NOT NULL,
    idUsuarioSolicitante INT NOT NULL, -- Quem enviou (o admin do grupo ou o usuário pedindo pra entrar)
    tipo ENUM('solicitacao_grupo', 'convite_grupo') NOT NULL, 
    origem_id INT NOT NULL, -- ID do Grupo em questão
    preview VARCHAR(255),
    status ENUM('pendente', 'aprovada', 'rejeitada') DEFAULT 'pendente',
    dataEnvio DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idUsuarioDestinatario) REFERENCES Usuario(idUsuario) ON DELETE CASCADE,
    FOREIGN KEY (idUsuarioSolicitante) REFERENCES Usuario(idUsuario) ON DELETE CASCADE,
    FOREIGN KEY (origem_id) REFERENCES Grupo(idGrupo) ON DELETE CASCADE
);

CREATE TABLE Moderador (
    idModerador INT PRIMARY KEY,
    FOREIGN KEY (idModerador) REFERENCES Usuario(idUsuario)
        ON DELETE CASCADE
);

-- Tabela Chat (sem a FK de Grupo ainda, será adicionada abaixo)
CREATE TABLE Chat (
    idChat INT PRIMARY KEY AUTO_INCREMENT,
    tipo ENUM('privado', 'grupo') NOT NULL,
    dataHora DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Mensagem (
    idMensagem INT PRIMARY KEY AUTO_INCREMENT,
    conteudo TEXT,
    anexo VARCHAR(255),
    dataEnvio DATETIME DEFAULT CURRENT_TIMESTAMP,
    idChat INT NOT NULL,
    idUsuario INT NOT NULL,
    FOREIGN KEY (idChat) REFERENCES Chat(idChat)
        ON DELETE CASCADE,
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario)
        ON DELETE CASCADE
);

CREATE TABLE Grupo (
    idGrupo INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    tipo ENUM('público', 'privado') NOT NULL
);

CREATE TABLE Usuario_Grupo (
    idUsuario INT,
    idGrupo INT,
    PRIMARY KEY (idUsuario, idGrupo),
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario)
        ON DELETE CASCADE,
    FOREIGN KEY (idGrupo) REFERENCES Grupo(idGrupo)
        ON DELETE CASCADE
);

CREATE TABLE Usuario_Chat (
    idUsuario INT,
    idChat INT,
    PRIMARY KEY (idUsuario, idChat),
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario)
        ON DELETE CASCADE,
    FOREIGN KEY (idChat) REFERENCES Chat(idChat)
        ON DELETE CASCADE
);

CREATE TABLE Duvida (
    idDuvida INT PRIMARY KEY AUTO_INCREMENT,
    titulo VARCHAR(150) NOT NULL,
    descricao TEXT,
    dataPostagem DATETIME DEFAULT CURRENT_TIMESTAMP,
    idUsuario INT NOT NULL,
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario)
        ON DELETE CASCADE
);

CREATE TABLE Resposta (
    idResposta INT PRIMARY KEY AUTO_INCREMENT,
    conteudo TEXT NOT NULL,
    dataPostagem DATETIME DEFAULT CURRENT_TIMESTAMP,
    idDuvida INT NOT NULL,
    idUsuario INT NOT NULL,
    FOREIGN KEY (idDuvida) REFERENCES Duvida(idDuvida)
        ON DELETE CASCADE,
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario)
        ON DELETE CASCADE
);

CREATE TABLE Grupo_Moderador (
    idGrupo INT,
    idModerador INT,
    PRIMARY KEY (idGrupo, idModerador),
    FOREIGN KEY (idGrupo) REFERENCES Grupo(idGrupo)
        ON DELETE CASCADE,
    FOREIGN KEY (idModerador) REFERENCES Moderador(idModerador)
        ON DELETE CASCADE
);

-- ==============================================
-- 3. ALTERAÇÕES DE TABELA (DO grupos-script.sql)
-- ==============================================

ALTER TABLE Chat
ADD COLUMN idGrupo_FK INT NULL;

ALTER TABLE Chat
ADD CONSTRAINT FK_Chat_Grupo FOREIGN KEY (idGrupo_FK) REFERENCES Grupo(idGrupo);

-- ==============================================
-- 4. INSERINDO DADOS (DO into_tables.sql)
-- ==============================================

-- Usuários
INSERT INTO Usuario (nome, idade, email, senha)
VALUES
('Bryan', 20, 'bryan@email.com', '123456'),
('Ana Clara', 22, 'ana@email.com', 'senha123'),
('Carlos Silva', 25, 'carlos@email.com', 'abc123'),
('Maria Eduarda', 21, 'maria@email.com', 'minhasenha');

-- Moderador (herda de Usuario)
INSERT INTO Moderador (idModerador)
VALUES (1); -- Bryan é moderador

-- Grupos
INSERT INTO Grupo (nome, descricao, tipo)
VALUES
('Estudos de Programação', 'Grupo para dúvidas de Java e Python', 'público'),
('Engenharia de Software', 'Discussões sobre modelagem UML e projetos', 'privado');

-- Chats
INSERT INTO Chat (tipo) VALUES ('privado'), ('grupo');

-- Associação de usuários aos chats
INSERT INTO Usuario_Chat (idUsuario, idChat)
VALUES
(1, 1), (2, 1), -- Chat privado entre Bryan e Ana
(1, 2), (3, 2), (4, 2); -- Chat em grupo entre Bryan, Carlos e Maria

-- Mensagens
INSERT INTO Mensagem (conteudo, idChat, idUsuario)
VALUES
('Olá Ana, tudo bem?', 1, 1),
('Oi Bryan! Tudo sim e você?', 1, 2),
('Pessoal, o que acham do novo projeto UML?', 2, 1),
('Achei interessante, podemos melhorar o diagrama.', 2, 3);

-- Associação usuários a grupos
INSERT INTO Usuario_Grupo (idUsuario, idGrupo)
VALUES
(1, 1), (2, 1), (3, 2), (4, 2);

-- Moderador gerencia grupo
INSERT INTO Grupo_Moderador (idGrupo, idModerador)
VALUES (1, 1);

-- Dúvidas
INSERT INTO Duvida (titulo, descricao, idUsuario)
VALUES
('Erro ao conectar no banco de dados', 'Não consigo conectar ao MySQL pelo Java.', 2),
('Como usar ENUM em SQL?', 'Quero limitar o tipo de chat em "privado" ou "grupo".', 3);

-- Respostas
INSERT INTO Resposta (conteudo, idDuvida, idUsuario)
VALUES
('Verifique se o driver JDBC está configurado corretamente.', 1, 1),
('Você pode usar ENUM(tipo1, tipo2) na criação da tabela.', 2, 4);

-- ==============================================
-- 5. ATUALIZAÇÃO DE DADOS (DO alteraracaoeupdate-scrip.sql)
-- ==============================================

-- Ajuste para vincular o chat de grupo (idChat = 2) ao grupo (idGrupo = 1)
-- Nota: O script original usava idGrupo_FK = 1. Ajustei para idGrupo_FK = 1, pois o chat 2 (Bryan, Carlos, Maria)
-- não corresponde aos membros do grupo 1 (Bryan, Ana).
-- Vou manter o script original, mas deixo a nota.
-- O script original presumia que o chat 2 (idChat=2) pertencia ao grupo 1 (idGrupo=1)
UPDATE Chat SET idGrupo_FK = 1 WHERE idChat = 2 AND tipo = 'grupo';
