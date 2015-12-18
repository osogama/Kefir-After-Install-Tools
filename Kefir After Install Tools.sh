#!/bin/bash


#################################################################################
#                                                                               #
#                  Kefir After Install Tools Shell                              #   
#                                                                               # 
#################################################################################
clear
	echo "Olá $USER, este script vai instalar os principais softwares no seu computador 
        (Ubuntu ou Linux Mint) -- Pressione Enter para iniciar --"
	read key
	if [ $key == $key ]
		then
			echo "Vamos prosseguir com a instalação..."	
			sleep 2
			echo "Digite a sua senha de usuário"

            sudo update-alternatives --config x-cursor-theme
            sudo apt-get install htop -y
            sudo apt-get install mplayer -y
            sudo apt-get install fbi -y
            sudo apt-get install links2 -y
            sudo apt-get install gdebi -y
            sudo apt-get install ubuntu-restricted-extras -y
            sudo apt-get install unity-tweak-tool -y
            sudo apt-get install tor-browser -y
            sudo apt-get install skype -y
            sudo apt-get install furiusisomount -y
            sudo apt-get install vlc -y
            sudo apt-get install bleachbit -y
            sudo apt-get install pdfmod -y
            sudo apt-get install geany -y
            sudo apt-get install synaptic -y
            sudo apt-get install git-core -y
            sudo apt-get install unetbootin -y
            sudo apt-get install samba -y
            sudo apt-get install gimp -y
            sudo apt-get install inkscape -y
            sudo apt-get install mypaint -y
            sudo apt-get install teamviewer -y
            sudo apt-get install audacity -y
            sudo apt-get install wifite -y
            sudo apt-get install synapse -y
            sudo apt-get install reaver -y
            sudo apt-get install aircrack-ng -y
            sudo apt-get install sound-juicer -y
            sudo apt-get install steam -y
            sudo apt-get install openshot
            sudo apt-get install xubuntu-icon-theme -y
	    sudo apt-get install synergy -y
            sudo apt-get install tuxguitar-alsa tuxguitar-jsa tuxguitar-oss -y
            sudo add-apt-repository ppa:fossfreedom/indicator-sysmonitor -y
            sudo add-apt-repository ppa:ravefinity-project/ppa -y
            sudo add-apt-repository ppa:atareao/atareao -y
            sudo add-apt-repository ppa:noobslab/themes -y
	        sudo add-apt-repository ppa:webupd8team/java -y && 
            sudo apt-get update &&
            sudo apt-get install flat-plat-gs
            #sudo apt-get install ambiance-flat-colors radiance-flat-colors -y
            sudo apt-get install my-weather-indicator -y
            sudo apt-get install indicator-sysmonitor -y
			sudo apt-get install oracle-java8-installer -y &&
			clear
			echo "A instalação foi concluída!"
            
			sleep 5
	fi
	
