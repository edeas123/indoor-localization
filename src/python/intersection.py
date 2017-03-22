#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import numpy as np
import math

#class Geometry from https://gist.github.com/xaedes/974535e71009fa8f090e and 
#http://stackoverflow.com/questions/3349125/circle-circle-intersection-points
class Geometry(object):
    def circle_intersection(self, circle1, circle2):
        '''
        @summary: calculates intersection points of two circles
        @param circle1: tuple(x,y,radius)
        @param circle2: tuple(x,y,radius)
        @result: tuple of intersection points (which are (x,y) tuple)
        '''
        # return self.circle_intersection_sympy(circle1,circle2)
        x1,y1,r1 = circle1
        x2,y2,r2 = circle2
        # http://stackoverflow.com/a/3349134/798588
        dx,dy = x2-x1,y2-y1
        d = math.sqrt(dx*dx+dy*dy)
        if d > r1+r2:
            return ()  # no solutions, the circles are separate
        if d < abs(r1-r2):
            return ()# no solutions because one circle is contained within the other
        if d == 0 and r1 == r2:
            return ()  # circles are coincident and there are an infinite number of solutions

        #Considering the two triangles P0P2P3 and P1P2P3 we can write
        #a2 + h2 = r02 and b2 + h2 = r12
        #Using d = a + b we can solve for a,
        #P2 = P0 + a ( P1 - P0 ) / d
        #And finally, P3 = (x3,y3) in terms of P0 = (x0,y0), P1 = (x1,y1) and P2 = (x2,y2), is
        #x3 = x2 +- h ( y1 - y0 ) / d
        #y3 = y2 -+ h ( x1 - x0 ) / d

        a = (r1*r1-r2*r2+d*d)/(2*d)
        h = math.sqrt(r1*r1-a*a)
        xm = x1 + a*dx/d
        ym = y1 + a*dy/d
        xs1 = xm + h*dy/d
        xs2 = xm - h*dy/d
        ys1 = ym - h*dx/d
        ys2 = ym + h*dx/d

        return (xs1,ys1),(xs2,ys2)

    def circle_intersection_sympy(self, circle1, circle2):
        from sympy.geometry import Circle, Point
        x1,y1,r1 = circle1
        x2,y2,r2 = circle2
        c1=Circle(Point(x1,y1),r1)
        c2=Circle(Point(x2,y2),r2)
        intersection = c1.intersection(c2)
        if len(intersection) == 1:
            intersection.append(intersection[0])
        p1 = intersection[0]
        p2 = intersection[1]
        xs1,ys1 = p1.x,p1.y
        xs2,ys2 = p2.x,p2.y
        return (xs1,ys1),(xs2,ys2)


#calculation of distance from a router in meters
# d = 10 ^ ((27.55 - (20 * log10(frequency)) + signalLevel)/20)


def calculateDistance(freqInMHz, level):
    """
    This function returns the distance in meters from a reference point
    level: the level in dbm
    freqInMHz: the frequency of the router signal in MHz
    """
    exp = (27.55 - (20 * math.log10(freqInMHz)) + abs(level)) / 20.0 
    return math.pow(10.0, exp)

#I added num_routers as a parameter, just in case you would like to test this on more than three routers
#note this is only for one duty cycle
def circle_intersection(num_routers, x, y, freq, strength):
    """
    num_routers: number of routers to find intersection points for
    x: list of x coordintes for routers
    y: list of y coordinates
    freq: list of frequencies
    strength: list of signal strengths 

    returns a list of tuples (x,y) indicating all the points of intersection
    """
    geom = Geometry()
    result=[]
    for i in range(0, num_routers-1):
        for j in range(i+1,num_routers):
            result.extend(geom.circle_intersection((x[i],y[i],calculateDistance(freq[i],strength[i])), (x[j],y[j],calculateDistance(freq[j],strength[j]))))
    return result
   