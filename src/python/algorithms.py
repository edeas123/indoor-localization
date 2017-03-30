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
        # initialize access point database
        self.apdata = apdata.set_index(['mac'], drop=False)
    
    def strongest(self, df):
        # return the records with the strongest signal strength for each router
        return df.loc[df['level'].idxmax()]
    
    def loc(self, df):
        # return the details of the routers from the ap database
        rdf = pd.DataFrame()
        for row in df.iterrows():
            f = row[1]
            try:
                coord = self.apdata.loc[f['base_bssid']]
                coord['level'] = f['level']
                coord['freq'] = f['freq']
                rdf = rdf.append(coord, ignore_index=True)            
            except:
                pass
        return rdf
    
    def locate_particles(self, df):
        """ 
        use particle filtering to locate point. The dataframe represent a duty cycle,
        it would contain multiple ssid from the same router
        get the details of the router using the router database
        """        
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
        
        # fix name difference across databases
        if (building == "MurrayLibrary"):
            building = "Murray"
    
        centerline_x_y = ct.get_points(floor, building)
#        print floor, building, centerline_x_y
        
        # get the data for the ssid with the strongest signal
        observations = pd.groupby(df_full, ['mac']).apply(self.strongest)
        observations = observations[['freq','level','easting','northing']].reset_index(drop=True)
        
        # call particle filtering algorithm
        print "observations"
        print observations
        
        print "centerline_x_y"
        print centerline_x_y
        
        points = pf.particle_filter(centerline_x_y,  observations)
        return points

    def locate(self, df):
        """ 
        use trilateration to locate point. The dataframe represent a duty cycle,
        it would contain multiple ssid from the same router
        get the details of the router using the router database
        """
        # this would give the number of routers seen at each duty cycle by 
        # a participant ... can be used in the distribution plot after little
        # ... modification
        # TODO: confirm column present first
        router_count = len(np.unique(df['base_bssid']))
        
        # if the df represents only one router: macid
        # return the x,y cordinate of that router.
        # if the router is not in the ap database
        # return null        
        if (router_count == 1):
            router_mac = df['base_bssid']
            try:
                pt = self.apdata.loc[router_mac].values[0]
                columns = self.apdata.columns.values
                coord = pd.DataFrame(data=[pt], columns=columns)
                coord['source'] = "Router"
                return coord
            except:
                # we don't have the router in our database
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
        
        # get router coordinate etc from router database
        df_mac = self.loc(df_strongest)

        # return null if none of the routers is in the database        
        router_count = len(df_mac)
        if (router_count == 0):
            columns = self.apdata.columns.values
            coord = pd.DataFrame(data=[[None] * len(columns)],index=None,columns=columns)
            coord['source'] = "Unknown Router"            
            return coord
        
        # perform the circle intersection - using the ssid data for the strongest signal
        points = it.circle_intersection(router_count, df_mac['easting'], df_mac['northing'], 
                               df_mac['freq'], df_mac['level'])
        
        # if you have no intersection, return the original router location
        if (len(points) == 0):
            df_mac['source'] = "Zero Intersection"
            return df_mac
        
        coord = pd.DataFrame(columns=['easting', 'northing'])
        for point in points:
            pt = pd.DataFrame(data=[[point[0], point[1]]], columns=['easting', 'northing'])
            pt['source'] = "Intersection"            
            coord = coord.append(pt)
        
        return coord    