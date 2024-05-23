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
        
        #Add Function to CQ 
        cq.Workplane.addSvgPath = addSvgPath
        
        self.svgPath = None
        self.paths = None
        self.attributes = None
        self.pathCount = None
        
        #List of path number to skip while parsing
        self.skipPathNumber = []
        
        #Need to rename this to self.blk in the future
        self.base = cq.Workplane('XY').tag('workFace')
        
        # https://www.pinterest.com/pin/63754150967869908/
        self.neckHeight = 2
        self.bodyHeight = 0
        self.overallTypeHeight = 23.31
        
        #Percentage to increase the spacing between the SVG
        # and edge of type. Shall be greater than 1.
        self.xLenAdj = 1
        self.yLenAdj = 1
        
        #x/y wall width is defined later on
        self.xWallWidth = None
        self.yWallWidth = None
        
        #Hollow x/y amount can be defined as a percentage
        self.xhollowPercentage = 0.8
        self.yhollowPercentage = 0.8
        
        
    
    
    def readSVGFromFile(self, fileName):
        '''
        Sets svgPath to the fileName. When calling parseSVG, svg2Paths can read in a file from disk
        '''
        self.svgPath = fileName
        
        
    def scaleSVG(self):
        #https://stackoverflow.com/questions/43199869/rotate-and-scale-a-complete-svg-document-using-python
        pass
    
    
    def doMath(self):
        '''
        The idea is to read the SVG and add some default values to be used later on. Going to finish the code as-is and then come back to fill in the values here.
        '''
        pass
        
        
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
            if idx not in self.skipPathNumber:
                #print(idx)
                svgPath = (
                    self.base
                    .workplaneFromTagged('workFace')
                    .addSvgPath(path)
                    .extrude(self.neckHeight, clean=True)
                )
            #show_object(svgPath)
            self.base = self.base.union(svgPath, glue = True)
            
            
    def buildBody(self):
        '''
        Builds body of the type. Builds a box around the 3D SVG.
        
        Then calculates the body height by subtracting the neck height
        from the overall type height.
        
        Then extrude. Feet will be cut out from the total body.
        
        The offset is required or else an error will occur.
        https://stackoverflow.com/questions/77845206/cadquery-unexpected-valueerror-null-topods-shape-object-during-cut-operation
        '''
        
        self.bodyHeight = self.overallTypeHeight - self.neckHeight
        
        self.bbox = self.base.val().BoundingBox()
        
        self.base = (
                self.base.workplaneFromTagged('workFace')
                .workplane(offset = 0.0001)
                .center(self.bbox.center.x, self.bbox.center.y)
                .rect(self.bbox.xlen*self.xLenAdj, self.bbox.ylen*self.yLenAdj)
                .extrude(-1*self.bodyHeight)
        )
        
        self.bbox = self.base.faces('<Z').val().BoundingBox()
        
        
    def hollowBody(self):
        '''
        Hollowing could be done in percentage or manual width
        
        Setting a constant buffer of 2 here
        '''
        
        bboxTemp = self.base.faces('<Z').val().BoundingBox()
        
        self.hollowDepth = self.overallTypeHeight - self.neckHeight - 2
        
        print('HollowDepth: ', self.hollowDepth)
        
        self.base = (
            self.base.faces('<Z')
            .workplane()
            .rect(bboxTemp.xlen*self.xhollowPercentage, bboxTemp.ylen*self.yhollowPercentage)
            .extrude(-1*self.hollowDepth/2, combine='cut')
        )
        
    def createAndCutPyramid(self):
        bboxTemp = self.base.faces('>>Z[2]').val().BoundingBox()
        
        print(bboxTemp.xlen)
        print(bboxTemp.ylen)
        
        origin = (bboxTemp.center.x,
                  bboxTemp.center.y, 
                  bboxTemp.center.z
                 )
        
        print(origin)
        
        pyramid = (
                    cq.Workplane('XY', origin=(origin))
                    .rect(bboxTemp.xlen, bboxTemp.ylen)
                    .workplane(offset=self.hollowDepth/2)
                    .rect(bboxTemp.xlen/100, bboxTemp.ylen/100)
                    .loft()
                  )
        self.base = self.base.cut(pyramid, clean=True)
                
    def cutFeet(self):
        bboxTemp = self.base.faces('>X').val().BoundingBox()
        
        self.base = (
            self.base.faces('>X')
            .workplane()
            #Move to lower-left corner
            .center(-1*bboxTemp.ylen/2,0)
            .move(bboxTemp.ylen*0.18, 0)   #_
            .line(bboxTemp.ylen*0.02, 20)  #_/
            .line(bboxTemp.ylen*0.6, 0)    #_/----
            .line(bboxTemp.ylen*0.02, -20) #_/----\
            .close()
            .extrude(-1*self.bbox.xlen, combine='cut')
        )
           
        

######################################################################
#  A proof of concept adding a svg path into a cadQuery Workspace
#  object.
#
#  This file is in the public domain.
#
#  Dov Grobgeld <dov.grobgeld@gmail.com>
#  2024-03-10 Sun
######################################################################


def tpl(cplx):
    '''Convert a complex number to a tuple'''
    return (cplx.real,cplx.imag)

def angle_between(u,v):
    '''Find the angle between the vectors u an v'''
    ux,uy = u
    vx,vy = v
    sign = 1 if ux*vy-uy*vx > 0 else -1
    arg = (ux*vx+uy*vy)/(sqrt(ux*ux+uy*uy)*sqrt(vx*vx+vy*vy))
    return sign*acos(arg)

# Implementation of https://www.w3.org/TR/SVG/implnote.html#ArcConversionCenterToEndpoint
def arc_endpoint_to_center(
    start,
    end,
    flag_a,
    flag_s,
    radius,
    phi):
    print('Fn: Arc_endpoint_to_center')
    '''Convert a endpoint elliptical arc description to a center description'''
    rx,ry = radius.real,radius.imag
    x1,y1 = start.real,start.imag
    x2,y2 = end.real,end.imag

    cosphi = cos(phi)
    sinphi = sin(phi)
    rx2 = rx*rx
    ry2 = ry*ry

    # Step 1. Compute x1p,y1p
    x1p,y1p = (np.array([[cosphi,sinphi],
                   [-sinphi,cosphi]])
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

def compare_complex(num1, num2, tolerance):
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

    #print('Start Path')

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
            center,theta1,delta_theta = arc_endpoint_to_center(
                p.start,
                p.end,
                p.large_arc,
                p.sweep,
                p.radius,
                p.rotation)

            res = res.ellipseArc(
                x_radius = p.radius.real,
                y_radius = p.radius.imag,
                rotation_angle=degrees(p.rotation),
                angle1= degrees(theta1),
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
