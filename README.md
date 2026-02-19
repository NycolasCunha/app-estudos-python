
 ​# Aplicativo de Estudos (Core Logic)

​Projeto desenvolvido originalmente durante o curso técnico no SENAI Joinville. Esta versão foca na lógica principal e funcionalidades de back-end que desenvolvi individualmente.

​## 🚀 Tecnologias e Conceitos Aplicados

* **Linguagem:** Python

* **Banco de Dados:** Integração com SQL (Operações CRUD)

* **Interface:** Lógica de navegação e organização de estudos

* **Ferramentas:** Visual Studio e Git para controle de versão


Extenções nescessarias para rodar os codigos python no vs code
(cole os pip install no terminal)
pip install customtkinter 
pip install mysql-connector-python

Para criar a aplicação foi usado o nuitka
py -m nuitka --onefile --disable-console --enable-plugin=tk-inter --windows-icon-from-ico="testelogo.ico" --include-data-file=testelogo.ico=testelogo.ico -o "Duostudy.exe" app.py
