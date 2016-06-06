downloadsweepervenv: downloadsweepervenv/bin/activate

downloadsweepervenv/bin/activate: requirements.txt
	test -d downloadsweepervenv || virtualenv -p /usr/bin/python3 downloadsweepervenv 
	downloadsweepervenv/bin/pip install -r requirements.txt
	touch downloadsweepervenv/bin/activate

install: download-sweeper.service.template download-sweeper.timer downloadsweepervenv
	cat download-sweeper.service.template | sed "s@DOWNLOADSWEEPERPATH@${DESTDIR}@g" > download-sweeper.service 
	mkdir -p ${DESTDIR}/usr/lib/systemd/system/
	install -Dm644 download-sweeper.service ${DESTDIR}/usr/lib/systemd/system/
	install -Dm644 download-sweeper.timer ${DESTDIR}/usr/lib/systemd/system/


