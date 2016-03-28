
configure: download_sweeper.py download-sweeper.service download-sweeper.timer
	sed "s@DOWNLOADSWEEPERPATH@${PWD}@g" -i download-sweeper.service 

install: download-sweeper.service download-sweeper.timer
	sudo cp download-sweeper.service /usr/lib/systemd/system/
	sudo chmod 664 /usr/lib/systemd/system/download-sweeper.service
	sudo cp download-sweeper.timer /usr/lib/systemd/system/
	sudo chmod 664 /usr/lib/systemd/system/download-sweeper.timer

