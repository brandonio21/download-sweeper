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
        try:
            with open(self.config_file_path, 'r') as openConfigFile:
                self.config_file_dict = yaml.load(openConfigFile.read())
        except Exception as e:
            raise ConfigurationManager.ConfigurationException(
                    ("Error when loading configuration file found at path {}."
                    "System returned err: {}").format( self.config_file_path, 
                        str(e))) from None

#if __name__ == "__main__":
