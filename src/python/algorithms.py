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
import initialize as init
import scipy.spatial

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
        
        #change to particle filter call
        #limit to initial observation
        obs = observations.loc[observations['record_time'] == observations.record_time.unique()[0]]
        points_list = pf.particle_filter(observations, init.initialize(obs))

        # reformat to single dataframe
        points = pd.concat(points_list, ignore_index=True)
        
        #save the list of data frames to a csv file 
        points.to_csv('particle.csv', sep='\t')
        
        return points


    def locate_points(self, observations):
        """ 
        use trilateration to locate point. The dataframe represent a duty cycle,
        it would contain multiple ssid from the same router
        get the details of the router using the router database
        """
       #get the floor and building 
        se = pd.Series(1/abs(observations.level))
        #add this as a column to df
        observations.is_copy = False
        observations['weight'] = se.values
        observations['count'] = 1
        mul = observations.groupby(['floor','building']).sum()
        mul = mul['weight']/mul['count']
        #get the index of the maximum probability
        floor, building = mul.idxmax()
        #check that the building is spelled correctly
        place = {"MurrayLibrary": "Murray", "MarquisHall": "Marquis Hall", "KirkHall": "Kirk Hall", "PlaceRiel": "Place Riel", "MUB": "Memorial", "Spinks": "Thorvaldson", "Thorvaldson": "Thorvaldson", "QuAppelleHallAddition": "Quappelle Hall", "SaskatchewanHall": "Saskatchewan Hall", "Administration": "Administration", "Agriculture": "Argiculture", "Archaeology": "Archaeology", "Arts": "Arts", "Athabasca": "Athabasca Hall", "Biology": "Biology", "College": "College", "Commerce": "Commerce", "Engineering": "Engineering", "Geology": "Geology", "Law": "Law", "Physics": "Physics"}
        
        # perform the circle intersection
        router_count = len(observations)
        points = it.circle_intersection(router_count, observations['easting'].values, observations['northing'].values, 
                               observations['freq'].values, observations['level'].values)

        coord = pd.DataFrame(columns=['easting', 'northing'])
        for point in points:
            pt = pd.DataFrame(data=[[point[0], point[1]]], columns=['easting', 'northing'])
            coord = coord.append(pt)

        #build tree if the building has centerline points
        if building in place:
            tr = ct.get_points(floor,place[building])
            nodes = [tuple(i[0][2:4]) for i in tr]
            tr = scipy.spatial.cKDTree(nodes)
            cent_x = []
            cent_y = []
            
            #for each intersection point
            coord = coord.reset_index()
            for c in range(coord.shape[0]):
                #get nearest point in centerline
                dist, index = pf.search_kdtree(tr, (coord.loc[c]['easting'], coord.loc[c]['northing']))
                #Store as cent_x and cent_y in the coord dataframe
                cent_x.append(tr.data[index, 0])
                cent_y.append(tr.data[index, 1])
        else: #the building isn't in the centerline database, so the intersection points are the best we can do, no snapping is done
            cent_x = ["NA"] * coord.shape[0]
            cent_y = ["NA"] * coord.shape[0]
        coord['floor'] = floor
        coord['building'] = building
        se = pd.Series(cent_x)
        coord['cent_x'] = se.values
        se = pd.Series(cent_y)
        coord['cent_y'] = se.values
        return coord
    
