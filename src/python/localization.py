# -*- coding: utf-8 -*-
"""
Created on Thu Mar 09 07:34:23 2017

@author: oodiete
"""

# import required packages
import pandas as pd
import utils
import os

from algorithms import location

# TODO: Update the campus wifi table in sql

# set paths
base_path = os.path.dirname(os.path.dirname(os.getcwd())) # get root directory
data_path = base_path + os.sep + "data" # set data directory
src_path = base_path + os.sep + "src"  # set src directory
sql_path = src_path + os.sep + "sql" + os.sep + "crepe" # set sql files directory
config_path = src_path + os.sep + "config" # set config files directory

# database configuration file
cfg_file = file(config_path + os.sep + 'config.txt')

# query to retrieve study wifi data
data_query = open(sql_path + os.sep + 'data_query.sql', 'r')
study = utils.run_sql(data_query, cfg_file)

data = pd.DataFrame(study, columns=['user_id', 'record_time', 'ssid', 'bssid', 
                                     'base_bssid', 'level', 'freq'])

# query to retrieve study access points database
cfg_file = file(config_path + os.sep + 'config.txt')

router_query = open(sql_path + os.sep + 'router_query.sql', 'r')
routers = utils.run_sql(router_query, cfg_file)

apdata = pd.DataFrame(routers, columns=['mac', 'location', 'building', 
                                     'Isinroom', 'floor', 'easting', 'northing'])

# initiate algorithm class with wifi router database
algo = location(apdata)

# determine localization information for each duty cycle
duty_cycles = pd.groupby(data, ['user_id', 'record_time'])

# using the strongest signal strength at that duty cycle
# using trilateration algorithm at that duty cycle
result = duty_cycles.apply(algo.locate)

result = result.reset_index(['mac'], drop=True)


