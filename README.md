Extenções nescessarias para rodar os codigos python no vs code
(cole os pip install no terminal)
pip install customtkinter 
pip install mysql-connector-python

Para criar a aplicação foi usado o nuitka
py -m nuitka --onefile --disable-console --enable-plugin=tk-inter --windows-icon-from-ico="testelogo.ico" --include-data-file=testelogo.ico=testelogo.ico -o "Duostudy.exe" app.py
