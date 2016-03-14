#!/usr/bin/env python3
################################################################################
# Filename: download-sweeper.py
# Author:   Brandon Milton
#           http://brandonio21.com
# Date:     20 February 2016
# 
# This file processes files in the downloads folders specified in the 
# configuration and moves them or removes them according to the user's spec.
################################################################################
import argparse
import yaml
import os
import re
import time
from datetime import datetime, timedelta

# Setup the commandline arguments
argParser = argparse.ArgumentParser(description="Manage old downloaded files")
argParser.add_argument('--config', default='config.yaml', 
                       help='The location of the configuration file to load')

# Functionality enable settings
archiveDownloadsGrp = argParser.add_mutually_exclusive_group()
archiveDownloadsGrp.add_argument('--archive-downloads',default=argparse.SUPPRESS,
                       action='store_true', help='''Downloads should be archived
                       once they become stale''', dest='archive_downloads')
archiveDownloadsGrp.add_argument('--no-archive-downloads',
                       default=argparse.SUPPRESS,action='store_false',
                       help='''Downloads should not be moved once they become
                       stale''', dest='archive_downloads')

purgeArchivesGrp = argParser.add_mutually_exclusive_group()
purgeArchivesGrp.add_argument('--purge-archives',default=argparse.SUPPRESS,
                      action='store_true', help='''Archives should be moved
                      purged when they become stale''', 
                      dest='purge_archives')
purgeArchivesGrp.add_argument('--no-purge-archives',default=argparse.SUPPRESS,
                      help='''Archives should not be moved once they become 
                      stale''', action='store_false',dest='purge_archives')

compressArchivesGrp = argParser.add_mutually_exclusive_group()
compressArchivesGrp.add_argument('--compress-archives',default=argparse.SUPPRESS,
                      help='''Archived files should be compressed''',
                      action='store_true',dest='compress_archives')
compressArchivesGrp.add_argument('--no-compress-archives',
                      default=argparse.SUPPRESS,help='''Archived files should 
                      remain uncompressed''',action='store_false',
                      dest='compress_archives')

shredWhenPurgingGrp = argParser.add_mutually_exclusive_group()
shredWhenPurgingGrp.add_argument('--shred',default=argparse.SUPPRESS,
                      help='Shred files when deleting them',action='store_true',
                      dest='shred_when_purging')
shredWhenPurgingGrp.add_argument('--no-shred',default=argparse.SUPPRESS,
                      help='Do not shred files when deleting them',
                      action='store_false',dest='shred_when_purging')

class ConfigKeyTranslator(object):
    DOWNLOADS = 0
    ARCHIVES = 1
    PURGES = 2
    _translation_list = [
         ('download_stale_after', 'download_directories'),
         ('archive_stale_after','archive_directores'     ),
         ('purge_stale_after', 'purge_directores'        ) ]

    def __init__(self, configType):
        self.stale_limit_key, self.path_key = self._translation_list[configType]
        

"""
class TrackedFileType(object):
    ARCHIVED = 0
    PURGE = 1

class TrackedFileFactory(object):

    def __init__(self, trackedFileType):
        self.trackedFileType = trackedFileType

    def create_new_tracked_file(self):

class ArchivedTrackFile(TrackedFile):

class PurgeTrackFile(TrackedFile):

class TrackedFile(object):
    A class that keeps track of the files that are scanned and then moved to
    the archive or purge directories
    def __init__(self):
    """

class ConfigFileTimeDeltaParser(object):
    DAYS_KEY = "d"
    WEEKS_KEY = "w"
    re_pattern = re.compile('^(\d+)([a-z])$')

    class InvalidConfigTimeStrException(Exception): pass
    class InvalidConfigTimeKeyException(Exception): pass

    @classmethod
    def _translate_key_to_deltakey_dict(cls, key, value):
        translation_dict = {'d' : 'days', 'w': 'weeks'}
        if not key in translation_dict:
            raise InvalidConfigTimeKeyException(
                    '{} is an invalid key'.format(key))
        return {translation_dict[key] : int(value)}

    @classmethod
    def get_timedelta_from_config_str(cls,configStr):
        matchedPattern = cls.re_pattern.match(configStr)
        if matchedPattern is None or not len(matchedPattern.groups()) == 2:
            raise cls.InvalidConfigTimeStrException(
                    '{} is an invalid time str'.format(configStr))

        return timedelta(
                **cls._translate_key_to_deltakey_dict(
                    matchedPattern.group(2), matchedPattern.group(1)))

class Sweeper(object):
    """ An object used to sweep certain directories and move their stale 
    contents to the next directory """

    def __init__(self, configManager):
        """ Inititalizes the Sweeper with a certain set of configurations """
        self.configManager = configManager


    def get_stale_file_paths(self, configTranslator):
        """ 
        Gets the paths of all stale files in the certain type of directory.

        Arguments:
        pathType: str - A member of ConfigKeyTranslator that determines which
                        directory we will be searching
        """
        stalePaths = []
        for directoryPath in self.configManager.get_option_value(
                configTranslator.path_key):
            for root, dirs, files in os.walk(directoryPath):
                for file in files:
                    fullFilePath       = os.path.join(root, file)
                    lastAccessCDate    = os.lstat(fullFilePath).st_atime
                    lastAccessDatetime = datetime.strptime(
                            time.ctime(lastAccessCDate), "%a %b %d %H:%M:%S %Y")
                    adjLastAccessTime = (lastAccessDatetime +
                            ConfigFileTimeDeltaParser.get_timedelta_from_config_str(
                                self.configManager.get_option_value(
                                    configTranslator.stale_limit_key)))

                    if adjLastAccessTime < datetime.today():
                        stalePaths.append(fullFilePath)

        return stalePaths

class ConfigurationManager(object):
    class ConfigurationException(Exception): pass

    """ An object used to manage the download-sweeper configuration file
    and retrieve specific settings"""
    def __init__(self, configPath, argNamespace, loadFile=True):
        """ Create the configuration manager and load the specified data from
        the file if loadFile is true """
        self.config_file_path = configPath
        self.config_file_dict = {}
        self.argNamespace = argNamespace

        if loadFile:
            self.load_config_file()

    def __str__(self):
        """ Return a human-readable representation of this configuration
        manager with all the details provied """
        return "ConfigurationManager with config path {} loaded as dict {}".format(
                self.config_file_path, self.config_file_dict)

    def __repr__(self):
        """ Return a human-readable representation by delegating to __str__ """
        return self.__str__()

    def load_config_file(self):
        """ Attempt to load the provided configuration file. If an error occurs
        while reading it, return a custom ConfigurationManager err """
        with open(self.config_file_path, 'r') as openConfigFile:
            self.config_file_dict = yaml.load(openConfigFile.read())

    def get_option_value(self, key):
        """ Returns the value of the provided option key. The values stored in
        commandline args take precedence over config file """
        argDictionary = vars(self.argNamespace)
        return (argDictionary[key] if key in argDictionary else 
                self.config_file_dict[key])

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    b = a.parse_args([])
    c = ConfigurationManager('config.yaml',b)
    cf = ConfigKeyTranslator(ConfigKeyTranslator.DOWNLOADS)
    s = Sweeper(c)
    print(s.get_stale_file_paths(cf))
