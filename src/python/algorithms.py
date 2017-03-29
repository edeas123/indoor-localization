# -*- coding: utf-8 -*-
"""
Created on Thu Mar 09 14:36:37 2017

@author: oodiete
"""
import numpy as np
import pandas as pd
import intersection as it
import particle_filter as pf
import centerline as ct

class location:
    
    def __init__(self, apdata):
        self.apdata = apdata.set_index(['mac'], False)
    
    def strongest(self, df):
        return df.loc[df['level'].idxmax()]
    
    def loc(self, df):
        rdf = pd.DataFrame()
        for row in df.iterrows():
            f = row[1]
#        for f in df['base_bssid'].values:
            try:
#                print "try", f
                coord = self.apdata.loc[f['base_bssid']]
                coord['level'] = f['level']
                coord['freq'] = f['freq']
#                print coord
                rdf = rdf.append(coord, ignore_index=True)            
            except:
#                print "fail"
                pass
        return rdf
    
    def locate_particles(self, df):
        
        # retreive info of floor and building from ap database
        df_full = self.loc(df)
        
        # retrieve centerline database points for floor and building
        
        if len(df_full) == 0:
            columns = self.apdata.columns.values
            coord = pd.DataFrame(data=[[None] * len(columns)],index=None,columns=columns)
            coord['source'] = "Unknown Router"
            
            return coord
        
        floor_counts = df_full['floor'].value_counts()
        floor = floor_counts.idxmax()

        building_counts = df_full['building'].value_counts()
        building = building_counts.idxmax()
        
        if (building == "MurrayLibrary"):
            building = "Murray"
    
        centerline_x_y = ct.get_points(floor, building)
#        print floor, building, centerline_x_y
#        
        # get the data for the ssid with the strongest signal
#        router_count = len(np.unique(df_full['mac']))        
        observations = pd.groupby(df_full, ['mac']).apply(self.strongest)

        # call particle filtering algorithm
        points = pf.particle_filter(centerline_x_y,  observations)
        print points
        return points

    def locate(self, df):
     
        # the dataframe represent a duty cycle,
        # it would contain multiple ssid from the same router
        # get the details of the router using the router database
        
        # this would give the number of routers seen at each duty cycle by 
        # a participant ... can be used in the distribution plot after little
        # ... modification
        # TODO: confirm column present first
        router_count = len(np.unique(df['base_bssid']))
#        print df
#        print router_count
        
        # if the df represents only one router: macid
        # return the x,y cordinate of that router.
        # if the router is not in the ap database
        # return null        
        if (router_count == 1):
#            print "entered here"
#            print df['base_bssid']
            router_mac = df['base_bssid']#.values[0]
#            print "router_mac", router_mac
            try:
                pt = self.apdata.loc[router_mac].values[0]
                columns = self.apdata.columns.values
#                print columns
#                print pt
                coord = pd.DataFrame(data=[pt], columns=columns)
#                print coord
                coord['source'] = "Router"
                # additional algorithm using markov rule etc
                # to narrow it down based on previous location
                # particle filtering
#                print "coord", coord
                return coord
            except:
                # we don't have the router in our database
#                print "Nonex1", None
                columns = self.apdata.columns.values
                coord = pd.DataFrame(data=[[None] * len(columns)],index=None,columns=columns)
                coord['source'] = "Unknown Router"
                
                return coord
            

        
        # if there are multiple routers
        # filter to the strongest signal strengths (-30, -80)
        # TODO: we need to plot a distribution of the signal levels too
        # ... since we are filtering with it
        
        # get the data for the ssid with the strongest signal
        df_strongest = pd.groupby(df, ['base_bssid']).apply(self.strongest)
        
#        print "df_strongest", df_strongest
        # get router coordinate etc from router database
        df_mac = self.loc(df_strongest)

#        print "df_mac", df_mac
        
        # return null if none of the routers is in the database        
        router_count = len(df_mac)
        if (router_count == 0):
#            print router_count, "None2"
#            return None
            columns = self.apdata.columns.values
            coord = pd.DataFrame(data=[[None] * len(columns)],index=None,columns=columns)
            coord['source'] = "Unknown Router"            
            return coord
        
        
        # perform the circle intersection - using the ssid data for the strongest signal
        points = it.circle_intersection(router_count, df_mac['easting'], df_mac['northing'], 
                               df_mac['freq'], df_mac['level'])
        
        # if you have no intersection,
        # return the original router locationS  
#        print "points", points
        if (len(points) == 0):
            df_mac['source'] = "Zero Intersection"
            return df_mac
        
        coord = pd.DataFrame(columns=['easting', 'northing'])
        for point in points:
            pt = pd.DataFrame(data=[[point[0], point[1]]], columns=['easting', 'northing'])
#            print pt
#            pt['easting'] = [point[0]]
#            pt['northing'] = [point[1]]
            pt['source'] = "Intersection"            
            coord = coord.append(pt)
        
        return coord    