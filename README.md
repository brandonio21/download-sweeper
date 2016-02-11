download-sweeper
================
A tool written in Python meant to help get rid of old downloads without running
the risk of losing data that you need. download-sweeper's primary goal is to
save the user precious disk space.


The Three-Tier Model
--------------------
download-sweeper considers downloads to be organized in three tiers:

 	1. The Download Tier: Files that are freshly downloaded or accessed
	                      repeatedly from their downloaded location.

	2. The Archive Tier : Files that were downloaded long ago and not 
	                      recently accessed but still may be accessed in the
			      future. By default, these files are compressed.

	3. The Purge Tier   : These files are ready to be deleted and are 
	 		      are considered to be never used. 



Flexibility
----------
download-sweeper is meant to be extremely flexible and allow the user to deal
with any sort of data-redundance that they want to take place. Thus, the user
can easily edit the YAML configuration file (even while download-sweeper is 
running) to add download, archive, or purge directories. The user may also edit
the time limits that differentiate between tiers and disable certain tier 
operations. 

For instance, a user could choose to move all downloads into the compressed
archive tier without deleting the files.

A user could also declare multiple directories as archive directories, meaning
that download-sweeper will automatically compress any uncompressed files and
remove them when they become stale.

A user could also declare several directories as download directories 
(Downloads, "My Received Files", etc.) that will operate the same way within
the download-sweeper pipeline.


Isolation
---------
As a development philosophy, download-sweeper will be able to read all settings
found within the configuraiton file as commandline arguments, meaning that it
can be run without access to a configuration file.


Systemd Integration
-------------------
download-sweeper is primarily meant to be run on system startup; however, 
service files will be instantiated when the user initiates "make" that will
allow the user to customize the intervals at which download-sweeper runs.