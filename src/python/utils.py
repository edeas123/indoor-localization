# -*- coding: utf-8 -*-
"""
Created on Thu Mar 09 11:23:36 2017

@author: oodiete
"""

import mysql.connector
from config import Config

""" run msql query in file"""
def run_sql(sql_file, cfg_file):
    
    cfg = Config(cfg_file)
    
    # connect to database
    try:
        cnx = mysql.connector.connect(**cfg)
    except mysql.connector.Error as err:
        print(err)
    
    # get cursor for executing query
    cursor = cnx.cursor()

    # read sql statement from file
    query = sql_file.read()
    sql_file.close()

    queries = query.strip(";").split(";")
    if len(queries) > 1:
        results = []
        
        for result in cursor.execute(query, True):
            results.append(result.fetchall())
    
        return results
    
    cursor.execute(query)
    return cursor.fetchall()