# -*- coding: utf-8 -*-
"""
Created on Thu Mar 09 07:34:23 2017

@author: oodiete
"""

# import required packages
import pandas as pd
import os
import mysql.connector
from config import Config

from algorithms import location

# set paths
base_path = os.path.dirname(os.path.dirname(os.getcwd())) # get root directory
data_path = base_path + os.sep + "data" # set data directory
src_path = base_path + os.sep + "src"  # set src directory
sql_path = src_path + os.sep + "sql" + os.sep + "crepe" # set sql files directory
config_path = src_path + os.sep + "config" # set config files directory
result_path = data_path + os.sep + "result"

# database configuration file
cfg_file = file(config_path + os.sep + 'config.txt')
cfg = Config(cfg_file)

# connect to database
try:
    cnx = mysql.connector.connect(**cfg)
except mysql.connector.Error as err:
    print(err)

# query to retrieve study access points database
router_query = """select mac_address as mac, location_description as location, building, 
is_in_room as Isinroom, floor, easting, northing
from SHED10.router;"""

apdata = pd.read_sql(router_query, con=cnx, columns=['mac', 'location', 'building', 
                                     'Isinroom', 'floor', 'easting', 'northing'])

# initiate algorithm class with wifi router database
algo = location(apdata)

# query to retrieve users
users_query = """select distinct(user_id)
from SHED10.campus"""

users = pd.read_sql(users_query, con=cnx, columns=['user_id']).values

# loop through the users
for user in users:
    user_id = user[0]
    print user_id
    
    # query to retrieve study wifi data
    data_query = """select *
    from SHED10.campus as t1
    where t1.user_id=""" + str(user_id) + ";"
    
    data = pd.read_sql(data_query, con=cnx, columns=['user_id', 'record_time', 'ssid', 'bssid',
                                         'base_bssid', 'level', 'freq'])
    
    # filter study wifi data by signal strength
    # NOTE: we lose about 51% of records
    data = data.loc[(data['level'] > -85) & (data['level'] < -30)]
    
    # filter study wifi data by accelerometer variance over three duty cycle
    
    # determine localization information for each duty cycle
    duty_cycles = pd.groupby(data, ['user_id', 'record_time'])
    
    # filter duty cycle observations
    duty_locations = duty_cycles.apply(algo.filter_location)
    current_data = duty_locations[['floor', 'building','easting','northing', 'freq', 'level']].dropna().reset_index()
    
    # using trilateration algorithm at each duty cycle
    participants_duty_cycles = pd.groupby(current_data, ['user_id', 'record_time'])
    result_points = participants_duty_cycles.apply(algo.locate_points)
    
    #addition of snapped points to data frame
    result_points = result_points[['easting', 'northing','floor','building','cent_x', 'cent_y']].reset_index().dropna()
    
    # write trilateration location to file
    points_file = "points_" + str(user_id) + ".csv"
    result_points.to_csv(result_path + os.sep + points_file, index=False)
    print user_id, len(result_points)

    #TODO: make 2d plot of locations coloured by the duty cycle
    #TODO: project location on the centerline
    # 2d plot of the location for a sample individual
    
    # using particle filtering algorithm
    participants = pd.groupby(current_data, ['user_id'])
    
    result_particles = participants.apply(algo.locate_particles)
    
    # write particles locations to file
    initial = 1
    
    particles_file = "particles_" + str(user_id) + "_" + str(initial) + "_True" + ".csv"
    result_particles.to_csv(result_path + os.sep + particles_file, index=False)
    print user_id, len(result_particles)









