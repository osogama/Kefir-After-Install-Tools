#!/bin/bash

#Kefir After Install on OS                                
                                                                              
#update
sudo apt-get update

#Instalar dependencias

sudo apt-get install python-software-properties -y
sudo apt-get install python-webkit -y

#criar pastas e icons

sudo mkdir /opt/kefir-after-install/
sudo cp -R * /opt/kefir-after-install/
sudo cp kefir-after-install.desktop /usr/share/applications/
sudo chmod +x /usr/share/applications/kefir-after-install.desktop
sudo chmod +x /opt/kefir-after-install/*.*
cd /opt/kefir-after-install/
sudo python -m py_compile kefir-after-install.py

clear
echo "A instalação foi concluída!"
echo "Esse diretório pode pode ser deletado"
echo "Acesse em: Aplicativos > Ferramentas de Sistema > Kefir After Install"
sleep 1

#TELA DE OPÇÔES PARA USUARIO {{{
echo
echo "__________________________________________________"
echo "EXECUTAR O PROGRAMA AGORA? / RUN PROGRAM NOW?[Y/N]"
read -p "ENTER: " esc
    case $esc in
    Y|y|s|S) #ESCOLHA
        cd  /opt/kefir-after-install/
        gksudo python kefir-after-install.py
        exit
    
    N|n
        exit    
    ;;
esac



