#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import numpy as np
from pandas import *



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
	return x, y
