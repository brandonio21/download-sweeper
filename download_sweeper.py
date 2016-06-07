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
import shutil
from datetime import datetime, timedelta
from zipfile import ZipFile

# Setup the commandline arguments
argParser = argparse.ArgumentParser(description="Manage old downloaded files")
argParser.add_argument('--config', default='/etc/download-sweeper',
                       help='The location of the configuration directory')

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

deleteFromPurgeGrp = argParser.add_mutually_exclusive_group()
deleteFromPurgeGrp.add_argument('--delete-from-purge', default=argparse.SUPPRESS,
                      help='''Files in the purge directory should be deleted''',
                      action='store_true', dest='delete_from_purge')
deleteFromPurgeGrp.add_argument('--no-delete-from-purge', 
                      default=argparse.SUPPRESS, help='''Files in the purge 
                      directory should not be deleted''', action='store_false',
                      dest='delete_from_purge')

class ConfigKeyTranslator(object):
    DOWNLOADS = "downloads"
    ARCHIVES = "archive"
    PURGES = "purge"
    _translation_list = {
            DOWNLOADS: ('download_stale_after', 'download_directories'),
            ARCHIVES: ('archive_stale_after','archive_directores'     ),
            PURGES: ('purge_stale_after', 'purge_directores'        ) }

    def __init__(self, configType):
        self.configType = configType
        self.stale_limit_key, self.path_key = self._translation_list[configType]
        

class File(object):

    def __init__(self, path, filename):
        self.path = path
        self.filename = filename

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


    def get_stale_file_paths(self, configTranslator, recordKeeper):
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
                for file in (files+dirs):
                    fullFilePath       = os.path.join(root, file)

                    # Skip directories that are not empty
                    if os.path.isdir(fullFilePath) and not len(os.listdir(fullFilePath)) == 0:
                        continue

                    if configTranslator.configType == ConfigKeyTranslator.DOWNLOADS:
                        lastAccessCDate    = os.lstat(fullFilePath).st_atime
                        lastAccessDatetime = datetime.strptime(
                                time.ctime(lastAccessCDate), "%a %b %d %H:%M:%S %Y")
                    else:
                        lastAccessDatetime = datetime.strptime(
                                recordKeeper.get_record(configTranslator.configType,
                                    fullFilePath), "%a %b %d %H:%M:%S %Y")

                    adjLastAccessTime = (lastAccessDatetime +
                            ConfigFileTimeDeltaParser.get_timedelta_from_config_str(
                                self.configManager.get_option_value(
                                    configTranslator.stale_limit_key)))

                    if adjLastAccessTime < datetime.today():
                        stalePaths.append(File(fullFilePath, file))


        return stalePaths

    def get_all_file_paths(self, configTranslator):
        """
        Gets the paths of all files in the certain type of directory.

        """
        filePaths = []
        for directoryPath in self.configManager.get_option_value(
                configTranslator.path_key):
            for root, dirs, files in os.walk(directoryPath):
                for file in files:
                    filePaths.append(os.path.join(root, file))

        return filePaths

class ConfigurationManager(object):
    class ConfigurationException(Exception): pass
    CONFIG_FILE_NAME = "config.yaml"

    """ An object used to manage the download-sweeper configuration file
    and retrieve specific settings"""
    def __init__(self, configPath, argNamespace, loadFile=True):
        """ Create the configuration manager and load the specified data from
        the file if loadFile is true """
        self.config_file_path = os.path.join(configPath, self.CONFIG_FILE_NAME)
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

class FileRecordKeeper(object):
    """ Keeps track of while files have been moved, where they have been moved
    to, and on what date/time they have been moved """
    DEFAULT_RECORD_FILE = 'records.yaml'
    def __init__(self, configPath, recordFile=DEFAULT_RECORD_FILE):
        self.recordFileLocation = os.path.join(configPath, recordFile)
        self.records = {}    #movLoc: {Filepath: movDate}

    def load_existing_records(self):
        """ Loads the existing records from the record file """
        if not os.path.isfile(self.recordFileLocation): return
        with open(self.recordFileLocation, 'r') as openRecordFile:
            retrievedFileContents = yaml.load(openRecordFile.read())
            if not retrievedFileContents is None:
                self.records = retrievedFileContents

    def add_record(self, filePath, moveLocation, moveDate: str):
        if not str(moveLocation) in self.records:
            self.records[str(moveLocation)] = {}
        self.records[str(moveLocation)][filePath] = moveDate

    def get_filepaths_in_type(self, movLocationType):
        if str(movLocationType) in self.records:
            return list(self.records[str(movLocationType)].keys())
        else: return []

    def record_exists(self, movLocation, filePath):
        return str(movLocation) in self.records and filePath in self.records[str(movLocation)]

    def get_record(self, movLocation, filePath):
        return self.records[str(movLocation)][filePath]

    def delete_record(self, filePath, moveLoc):
        del self.records[str(moveLoc)][filePath]

    def clean_records(self):
        badRecords = []
        for movLocation in self.records:
            for filePath in self.records[movLocation]:
                if not os.path.isfile(filePath):
                    badRecords.append((filePath, movLocation))

        for badRecord in badRecords:
            self.delete_record(badRecord[0], badRecord[1])

    def write_records(self):
        with open(self.recordFileLocation, 'w+') as openRecordFile:
            openRecordFile.write(yaml.dump(self.records))

def move_file_to_path(path, file):
    if not os.path.isdir(path): os.mkdir(path)
    newFilePath = os.path.join(path, file.filename)

    oldFileDetails = os.stat(file.path)
    oldUid = oldFileDetails.st_uid
    oldGid = oldFileDetails.st_gid
    shutil.move(file.path, newFilePath)
    os.chown(newFilePath, oldUid, oldGid)
    return newFilePath

def move_downloads_to_archive(sweeper, configurationManager, recordKeeper):
    if not configurationManager.get_option_value('archive_downloads'): return
    downloadConfigTranslator = ConfigKeyTranslator(ConfigKeyTranslator.DOWNLOADS)
    archiveConfigTranslator  = ConfigKeyTranslator(ConfigKeyTranslator.ARCHIVES)
    staleFiles = sweeper.get_stale_file_paths(downloadConfigTranslator, recordKeeper)
    
    for file in staleFiles:
        if os.path.isfile(file.path):
            for archivePath in configurationManager.get_option_value(archiveConfigTranslator.path_key):
                archivedFilePath = move_file_to_path(archivePath, file)
                recordKeeper.add_record(archivedFilePath, ConfigKeyTranslator.ARCHIVES,
                        time.ctime())
                if not configurationManager.get_option_value('move_to_all_archive_dirs'):
                    break
        else:
            os.rmdir(file.path)

def move_archives_to_purge(sweeper, configurationManager, recordKeeper):
    if not configurationManager.get_option_value('purge_archives'): return
    archiveConfigTranslator = ConfigKeyTranslator(ConfigKeyTranslator.ARCHIVES)
    purgeConfigTranslator   = ConfigKeyTranslator(ConfigKeyTranslator.PURGES)
    staleFiles = sweeper.get_stale_file_paths(archiveConfigTranslator, recordKeeper)

    for file in staleFiles:
        if os.path.isfile(file.path):
            for purgePath in configurationManager.get_option_value(purgeConfigTranslator.path_key):
                recordKeeper.delete_record(file.path, ConfigKeyTranslator.ARCHIVES)
                purgedFilePath = move_file_to_path(purgePath, file)
                recordKeeper.add_record(purgedFilePath, ConfigKeyTranslator.PURGES,
                        time.ctime())
                if not configurationManager.get_option_value('move_to_all_purge_dirs'):
                    break
        else:
            os.rmdir(file.path)

def delete_from_purge(sweeper, configurationMangager, recordKeeper):
    purgeConfigTranslator = ConfigKeyTranslator(ConfigKeyTranslator.PURGES)
    staleFiles = sweeper.get_stale_file_paths(purgeConfigTranslator, recordKeeper)

    # Delete all stale purge files
    for file in staleFiles:
        if os.path.isdir(file.path): shutil.rmtree(file.path)
        else: os.remove(file.path)

def is_zip_extension(extension):
    return extension in ['.zip']

def zip_path(filePath):
    
    zipPath = '{}.zip'.format(filePath)
    with ZipFile(zipPath, 'w') as zipFile:
        zipFile.write(filePath)
    return zipPath


def compress_archive_files(configurationManager, recordKeeper):
    # For now there will be no compression method available except for ZIP
    for filePath in recordKeeper.get_filepaths_in_type(ConfigKeyTranslator.ARCHIVES)[:]:
        fileExtension = os.path.splitext(filePath)[1]
        if not is_zip_extension(fileExtension):
            try:
                zipPath = zip_path(filePath)
                os.remove(filePath)
                recordedDatetime = recordKeeper.get_record(ConfigKeyTranslator.ARCHIVES,
                        filePath)
                recordKeeper.delete_record(filePath, ConfigKeyTranslator.ARCHIVES)
                recordKeeper.add_record(zipPath, ConfigKeyTranslator.ARCHIVES, recordedDatetime)
            except Exception:
                continue

def load_untracked_archives_into_record(sweeper, records):
    archiveConfigTranslator = ConfigKeyTranslator(ConfigKeyTranslator.ARCHIVES)
    archivedFiles = sweeper.get_all_file_paths(archiveConfigTranslator)
    add_unknown_files_to_record(ConfigKeyTranslator.ARCHIVES, records, archivedFiles)

def load_untracked_purges_into_record(sweeper, records):
    purgeConfigTranslator = ConfigKeyTranslator(ConfigKeyTranslator.PURGES)
    purgedFiles = sweeper.get_all_file_paths(purgeConfigTranslator)
    add_unknown_files_to_record(ConfigKeyTranslator.PURGES, records, purgedFiles)

def add_unknown_files_to_record(locationType, records, paths):
    for path in paths:
        if not records.record_exists(locationType, path):
            records.add_record(path, locationType, time.ctime())

if __name__ == "__main__":
    # Parse the arguments
    parsed_args = argParser.parse_args()
    configMgr = ConfigurationManager(parsed_args.config, parsed_args)
    sweeperObj = Sweeper(configMgr)
    records = FileRecordKeeper(parsed_args.config)
    records.load_existing_records()
    records.clean_records()
    load_untracked_archives_into_record(sweeperObj, records)
    load_untracked_purges_into_record(sweeperObj, records)

    if configMgr.get_option_value('archive_downloads'):
        move_downloads_to_archive(sweeperObj, configMgr, records)

    if configMgr.get_option_value('compress_archives'):
        compress_archive_files(configMgr, records)

    if configMgr.get_option_value('purge_archives'):
        move_archives_to_purge(sweeperObj, configMgr, records)

    if configMgr.get_option_value('delete_from_purge'):
        delete_from_purge(sweeperObj, configMgr, records)


    records.write_records()
