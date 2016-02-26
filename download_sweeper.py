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

                       

class ConfigurationManager(object):
    class ConfigurationException(Exception): pass

    """ An object used to manage the download-sweeper configuration file
    and retrieve specific settings"""
    def __init__(self, configPath, loadFile=True):
        """ Create the configuration manager and load the specified data from
        the file if loadFile is true """
        self.config_file_path = configPath
        self.config_file_dict = {}

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

    def get_option_value(self, argNamespace, key):
        """ Returns the value of the provided option key. The values stored in
        commandline args take precedence over config file """
        argDictionary = vars(argNamespace)
        return (argDictionary[key] if key in argDictionary else 
                self.config_file_dict[key])

#if __name__ == "__main__":
