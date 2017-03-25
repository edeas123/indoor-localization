# -*- coding: utf-8 -*-
"""
Created on Thu Mar 09 14:36:37 2017

@author: oodiete
"""
import numpy as np
import pandas as pd
import intersection as it

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
#                print "fail", f
                pass
        return rdf
        
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
            router_mac = df['base_bssid']
            try:
                coord = self.apdata.loc[router_mac]
                # additional algorithm using markov rule etc
                # to narrow it down based on previous location
                # particle filtering
#                print "coord", coord
                return coord
            except:
                # we don't have the router in our database
#                print "Nonex1", None
                columns = self.apdata.columns
#                return None
                return pd.DataFrame(data=[[None] * len(columns)],index=None,columns=columns)

        
        # if there are multiple routers
        # filter to the strongest signal strengths (-30, -80)
        # TODO: we need to plot a distribution of the signal levels too
        # ... since we are filtering with it
        
        #df = df.loc[(df()['level'] > -80) & (df()['level'] < -30)]
        
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
            columns = self.apdata.columns
            return pd.DataFrame(data=[[None] * len(columns)],index=None,columns=columns)
        
        # perform the circle intersection - using the ssid data for the strongest signal
        points = it.circle_intersection(router_count, df_mac['easting'], df_mac['northing'], 
                               df_mac['freq'], df_mac['level'])
        
        # if you have no intersection,
        # return the original router locationS  
#        print "points", points
        if (len(points) == 0):
            return df_mac
        
        coord = pd.DataFrame()
        for point in points:
#            print point
            coord['easting'] = [point[0]]
            coord['northing'] = [point[1]]
        
        
        return coord    