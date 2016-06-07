downloadsweepervenv: ${DESTDIR}/etc/download-sweeper/venv/bin/activate

${DESTDIR}/etc/download-sweeper/venv/bin/activate: requirements.txt
	test -d ${DESTDIR}/etc/download-sweeper || mkdir -p ${DESTDIR}/etc/download-sweeper
	test -d ${DESTDIR}/etc/download-sweeper/venv || virtualenv -p /usr/bin/python3 ${DESTDIR}/etc/download-sweeper/venv
	${DESTDIR}/etc/download-sweeper/venv/bin/pip install -r requirements.txt
	touch ${DESTDIR}/etc/download-sweeper/venv/bin/activate

install: download-sweeper.service download-sweeper.timer config.yaml download_sweeper.py downloadsweepervenv
	mkdir -p ${DESTDIR}/etc/download-sweeper/
	mkdir -p ${DESTDIR}/usr/lib/systemd/system/
	install config.yaml ${DESTDIR}/etc/download-sweeper/
	install -Dm755 download_sweeper.py ${DESTDIR}/usr/bin/
	install -Dm644 download-sweeper.service ${DESTDIR}/usr/lib/systemd/system/
	install -Dm644 download-sweeper.timer ${DESTDIR}/usr/lib/systemd/system/
