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

class ConfigurationManager:
    


if __name__ == "__main__":
