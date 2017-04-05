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
    
    def filter_location(self, df):

        """ 
        use router database and signal level to filter records
        """        
        # retreive info of floor and building from ap database
        df_full = self.loc(df)
        
        # router not in the database
        if len(df_full) == 0:
            columns = self.apdata.columns.values
            coord = pd.DataFrame(data=[[None] * len(columns)],index=None,columns=columns)
            return coord
        
        # get the data for the ssid with the strongest signal
        coord = pd.groupby(df_full, ['mac']).apply(self.strongest)
        return coord
        
    def locate_particles(self, observations):
        """ 
        use particle filtering to locate point. The dataframe represent all the
        duty cycle for a participants. Each duty cycle has the strongest signals
        from the routers seen
        """        
        # call particle filtering algorithm
        # returns a list of xytuples
        #points_list = pf.particle_filter(None, observations)
        
        #change to particle filter call
        points = pf.particle_filter(observations, init.initialize(observations))

        # reformat to pandas series
        #points = pd.DataFrame(points_list, columns = ["easting","northing"])

        #save the list of data frames to a csv file 
        pd.concat(points).to_csv('particle.csv', sep='\t')
        
        return points


    def locate_points(self, observations):
        """ 
        use trilateration to locate point. The dataframe represent a duty cycle,
        it would contain multiple ssid from the same router
        get the details of the router using the router database
        """
        # perform the circle intersection
        router_count = len(observations)
        points = it.circle_intersection(router_count, observations['easting'].values, observations['northing'].values, 
                               observations['freq'].values, observations['level'].values)

        coord = pd.DataFrame(columns=['easting', 'northing'])
        for point in points:
            pt = pd.DataFrame(data=[[point[0], point[1]]], columns=['easting', 'northing'])
            coord = coord.append(pt)
        
        return coord
