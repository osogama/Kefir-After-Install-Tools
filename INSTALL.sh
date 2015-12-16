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

clear
echo "A instalação foi concluída!"
echo "Esse diretório pode pode ser deletado"
echo "Aplicativos > Ferramentas de Sistema > Kefir After Install"
sleep 5

