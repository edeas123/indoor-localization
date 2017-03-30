# -*- coding: utf-8 -*-
"""
Created on Tue Mar 28 12:42:27 2017

@author: oodiete
"""

import arcpy
import pandas as pd
import os

"""
   retrieve the centerline points corresponding to give floor and building
"""
def get_points(floor, building):

    # set paths
    base_path = os.path.dirname(os.path.dirname(os.getcwd())) # get root directory
    data_path = base_path + os.sep + "data" # set data directory
    arc_path = data_path + os.sep + "arcgis" + os.sep + "campus.gdb" # set arc files directory

    arcpy.env.workspace = arc_path
    feature_class = arc_path + os.sep + "CenterLine2_1mPoints"
    
    rows = arcpy.SearchCursor(feature_class)
    row = rows.next()
    
    fname_map = {"ground floor": 0, "1st floor": 1,  "2nd floor":2, "3rd floor": 3, "basement floor": -1,
                 "4th floor": 4, "5th floor": 5, "6th floor": 6, "7th floor": 7,
                 "8th floor": 8, "9th floor": 9, "10th floor": 10, "11th floor": 11,
                 "12th floor": 12, "13th floor": 13, "14th floor": 14, "15th floor": 15,
                 "lower floor": -1, "main floor": 1}
    
    centerline_x_y = pd.DataFrame()
    while row:
        if (floor == fname_map[row.fname] and building==row.bname):
            centerline_x_y = centerline_x_y.append(pd.DataFrame(data=[[row.X, row.Y]]), ignore_index=True)
        row = rows.next()

    return centerline_x_y.values
