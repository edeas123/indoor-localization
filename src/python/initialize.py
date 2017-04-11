#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import numpy as np
from pandas import *
from intersection import *



def initialize(obs, N=500, r=3):
	"""
	Based on the observations of the first duty cycle (dataframe of mac id, x/y coordinates, frequency, level whatever else you need)
	Get the x/y location of the strongest signal
	Calculate the distance from this x/y coordinate and multiply by some integer r
	Generate a particle within the radius as initial hypotheses
	"""
	#get the maximum level x/y coordinate in the observation data frame
	l = obs.loc[obs['level'].idxmax()].level
	f = obs.loc[obs['level'].idxmax()].freq
	#calculate distance away from the router and multiply by r
	dist = calculateDistance(f,l) * r 
	#generate a random particle uniformly distributed between x-dist, x+dist, same for y
	xmin, xmax = obs.loc[obs['level'].idxmax()].easting - dist, obs.loc[obs['level'].idxmax()].easting + dist
	ymin, ymax = obs.loc[obs['level'].idxmax()].northing - dist, obs.loc[obs['level'].idxmax()].northing + dist
	x = np.random.uniform(xmin, xmax, N)
	y = np.random.uniform(ymin, ymax, N)
	return zip(x, y)


def initialize_dist(obs, N=500, r=3):
    """
    initialize points for the particle filter uniformly using the distance obtained
    from the signal level as the probability of a particle being in that range.
    The function considers all the routers seen in that duty cycle, not just the
    router with the strongest signal
    """
    # if the number of routers in the duty cycle is 1
    # return the results from initialize function above
    router_count = len(np.unique(obs['mac']))
    
    if router_count == 1:
        return initialize(obs, N, r)
    
    # if the number of routers is greater than 1
    # get the levels of the different routers, multiply
    inv_dists = []
    porp = []
    for row in obs.iterrows():
        df = row[1]
        dist = calculateDistance(df['freq'], df['level'])
        inv_dists.append(1/float(dist))   
    
    inv_dists_sum = sum(inv_dists)
    for i in inv_dists:
        porp.append(round((i / inv_dists_sum) * N))
    
    j = 0
    points = []
    for row in obs.iterrows():
        df = row[1]
        points.extend(initialize(DataFrame([df.tolist()], columns=obs.columns), porp[j]))
        j = j + 1

    return points[0:N]


def initialize_intersect(obs, N=500, r=3, step_size=1):
    
    # if the number of routers in the duty cycle is 1
    # return the results from initialize function above
    router_count = len(np.unique(obs['mac']))
    
    if router_count == 1:
        return initialize(obs, N, r)
    
    # if the number of routers is greater than 1
    d = []; x = []; y = []
    step = step_size
    geom = Geometry()
    
    for row in obs.iterrows():
        df = row[1]
        d.append(calculateDistance(df['freq'], df['level']))
        x.append(df['easting'])
        y.append(df['northing'])
    
    # save the original d, x and y
    origx = x; origy = y; origd = d
    
    result = []
    while len(result) < N:
        num_routers = len(d)
        
        # compute the circle intersections
        for i in range(0, num_routers-1):
            for j in range(i+1,num_routers):
                points = geom.circle_intersection((x[i],y[i], d[i]), (x[j],y[j], d[j]))
                if len(points) == 0: #if no intersections are found
                    result.extend(line_intersect(x[i],y[i],d[i], x[j],y[j],d[j]))
                else:
                    result.extend(points)
    
        # increase and reduce the circle radius by the step size
        dp = np.array(origd) + step
        dm = np.array(origd)- step
        d = dp.tolist() + dm.tolist()
        
        # increase the number of center points
        x = origx * 2
        y = origy * 2        
        
        # increase the step size
        step = step + step_size
    
    return result[0:N]

