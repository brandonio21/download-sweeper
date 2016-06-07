downloadsweepervenv: ${HOME}/.virtualenvs/download-sweeper/bin/activate

${HOME}/.virtualenvs/download-sweeper/bin/activate: requirements.txt download-sweeper.service
	sed "s@\$${HOME}@${HOME}@g" -i download-sweeper.service
	test -d ${HOME}/.virtualenvs/download-sweeper || virtualenv -p /usr/bin/python3 ${HOME}/.virtualenvs/download-sweeper
	${HOME}/.virtualenvs/download-sweeper/bin/pip install -r requirements.txt
	touch ${HOME}/.virtualenvs/download-sweeper/bin/activate

install: download-sweeper.service download-sweeper.timer config.yaml download_sweeper.py
	mkdir -p ${DESTDIR}/etc/download-sweeper/
	mkdir -p ${DESTDIR}/usr/lib/systemd/system/
	mkdir -p ${DESTDIR}/usr/bin/
	install config.yaml ${DESTDIR}/etc/download-sweeper/
	install -Dm755 download_sweeper.py ${DESTDIR}/usr/bin/
	install -Dm644 download-sweeper.service ${DESTDIR}/usr/lib/systemd/system/
	install -Dm644 download-sweeper.timer ${DESTDIR}/usr/lib/systemd/system/
