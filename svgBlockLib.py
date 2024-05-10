'''
Library for creating printing press blocks from SVGs.

Currently only supports Paths.

Uses code developed by Dov Grobgeld<dov.grobgeld@gmail.com>

'''

import svgpathtools
from svgpathtools import svg2paths
import cadquery as cq
import numpy as np
from math import sin, cos, sqrt, pi, acos, fmod, degrees

class blkLibrary:

    def __init__(self, createBlock=False):
        
        cq.Workplane.addSvgPath = self.addSvgPath
        
        self.svgPath = None
        self.paths = None
        self.attributes = None
        self.pathCount = None
        
        #List of path number to skip while parsing
        self.skipPathNumber = []
        
        #Need to rename this to self.blk in the future
        self.base = cq.Workplane('XY').tag('workFace')
    
    
    def readSVGFromFile(self, fileName):
        '''
        Sets svgPath to the fileName. When calling parseSVG, svg2Paths can read in a file from disk
        '''
        self.svgPath = fileName
        
        
    def parseSVG(self):
        '''
        Given a valid svgPath, svg2paths will return the paths and attributes.
        
        In the future, I hope this could include an HTML link.
        '''
        paths, attributes = svg2paths(self.svgPath)
        self.paths = paths
        self.attributes = attributes
        self.pathCount = len(paths)
        

    def translate2Dto3D(self):
        '''
        Loop through the paths and convert to 3D objects
        '''
        
        for idx, path in enumerate(self.paths):
            #print(idx)

            if idx not in self.skipPathNumber:
                svgPath = (
                    self.base
                    .workplaneFromTagged('workFace')
                    .addSvgPath(path)
                    .extrude(10, clean=True)
                )
            self.base = self.base.union(svgPath, glue = True)
            #show_object(guten)

        
        
    def tpl(self, cplx):
        '''Convert a complex number to a tuple'''
        return (cplx.real,cplx.imag)

    
    def angle_between(self, u, v):
        '''Find the angle between the vectors u an v'''
        ux,uy = u
        vx,vy = v
        sign = 1 if ux*vy-uy*vx > 0 else -1
        arg = (ux*vx+uy*vy)/(sqrt(ux*ux+uy*uy)*sqrt(vx*vx+vy*vy))
        return sign*acos(arg)

    
    # Implementation of https://www.w3.org/TR/SVG/implnote.html#ArcConversionCenterToEndpoint
    def arc_endpoint_to_center(self, start, end, flag_a, flag_s, radius, phi):
        '''Convert a endpoint elliptical arc description to a center description'''
        rx,ry = radius.real,radius.imag
        x1,y1 = start.real,start.imag
        x2,y2 = end.real,end.imag

        cosphi = cos(phi)
        sinphi = sin(phi)
        rx2 = rx*rx
        ry2 = ry*ry

        # Step 1. Compute x1p,y1p
        x1p,y1p = (np.array([[cosphi,sinphi], [-sinphi,cosphi]])
             @ np.array([x1-x2, y1-y2])*0.5).flatten()
        x1p2 = x1p*x1p
        y1p2 = y1p*y1p

        # Step 2: Compute (cx', cy')
        cxyp = sqrt((rx2*ry2 - rx2*y1p2 - ry2*x1p2)
              / (rx2*y1p2 + ry2*x1p2)) * np.array([rx*y1p/ry,-ry*x1p/rx])

        if flag_a == flag_s:
            cxyp = -cxyp

        cxp,cyp = cxyp.flatten()

        # Step 3: compute (cx,cy) from (cx',cy')
        cx,cy = (cosphi*cxp - sinphi * cyp + 0.5*(x1+x2),
            sinphi*cxp + cosphi * cyp + 0.5*(y1+y2))

        # Step 4: compute theta1 and deltatheta
        theta1 = angle_between((1,0), ((x1p-cxp)/rx, (y1p-cyp)/ry))
        delta_theta = fmod(angle_between(((x1p-cxp)/rx,(y1p-cyp)/ry),
                        ((-x1p-cxp)/rx, (-y1p-cyp)/ry)),2*pi)

        # Choose the right edge according to the flags
        if not flag_s and delta_theta > 0:
            delta_theta -= 2*pi
        elif flag_s and delta_theta < 0:
            delta_theta += 2*pi
    
        return (cx,cy), theta1, delta_theta


    def compare_complex(self, num1, num2, tolerance):
        """
        Compares two complex numbers using a given tolerance for both the real and imaginary parts.

        :param num1: The first complex number to be compared.
        :param num2: The second complex number to be compared.
        :param tolerance: The tolerance to use when comparing the real and imaginary parts of the numbers.

        :return: True if the real and imaginary parts of the two complex numbers are within the given tolerance, False otherwise.
        """
        # Check that the input is valid
        if not (isinstance(num1, complex) and isinstance(num2, complex)):
            raise ValueError("Both inputs must be complex numbers")

        # Check that the tolerance is valid
        if not (isinstance(tolerance, float) or isinstance(tolerance, int)):
            raise ValueError("Tolerance must be a number")

        # Check that the real and imaginary parts of the two complex numbers are within the given tolerance
        if abs(num1.real - num2.real) < tolerance and abs(num1.imag - num2.imag) < tolerance:
            return True

        return False

    def addSvgPath(self, path):
        '''
        Add the svg path object to the current workspace
        The p in path below is each movement in the path, where the movement
        can be a line, cubic/quad curve, or arc.

        The first p must be either a point or a move to that point.

        All p's are translated using bezier, ellipseArc commands and added
        to res (I assume res = result).
        '''
        
        print('Start Path')
        
        res = self
        path_start = None
        arc_id = 0
        for p in path:
            #print('path element to add: ',p)
            if path_start is None:
                path_start = p.start
            res = res.moveTo(*tpl(p.start))
            
            
            # Support the four svgpathtools different objects
            if isinstance(p, svgpathtools.CubicBezier):
                coords = (tpl(p.start), tpl(p.control1), tpl(p.control2), tpl(p.end))
                res = res.bezier(coords)
            elif isinstance(p, svgpathtools.QuadraticBezier):
                coords = (tpl(p.start), tpl(p.control), tpl(p.end))
                res = res.bezier(coords)
                pass
            
            elif isinstance(p, svgpathtools.Arc):
                arc_id += 1
                center, theta1, delta_theta = arc_endpoint_to_center(
                    p.start,
                    p.end,
                    p.large_arc,
                    p.sweep,
                    p.radius,
                    p.rotation)

                res = res.ellipseArc(
                    x_radius = p.radius.real, \
                    y_radius = p.radius.imag, \
                    rotation_angle=degrees(p.rotation), \
                    angle1= degrees(theta1), \
                    angle2=degrees(theta1+delta_theta))
            
            elif isinstance(p, svgpathtools.Line):   
                #Check to see if start and end points are the same - 0.001
                samePoint = compare_complex(p.start, p.end, 0.001)
                if samePoint:
                    #res = res.lineTo(p.end.real, p.end.imag)
                    pass
                    #print('Start and End are the same - skipping')
                else:
                    #print('Adding line')
                    res = res.lineTo(p.end.real, p.end.imag)
                
            else:
                print('Some other path type')
            
            if path_start == p.end:
                path_start = None
            res = res.close()

        return res
    