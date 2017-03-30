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
    feature_class = arc_path + os.sep + "CenterLine2_1mPoints_b"
    
    clause = '"bname"' +  " = '" + str(building) + "' and " + '"fnum"' +  " = " + str(floor)
    
    centerline_x_y = pd.DataFrame()
    with arcpy.da.SearchCursor(feature_class, ("fname", "bname", "x", "y",), clause) as cursor:
        for row in cursor:
            centerline_x_y = centerline_x_y.append(pd.DataFrame(data=[[row]]), ignore_index=True)
            
    return centerline_x_y.values
