'''
Library for creating printing press blocks from SVGs.

Currently only supports Paths.

Uses code developed by Dov Grobgeld<dov.grobgeld@gmail.com>

'''

import svgpathtools
from svgpathtools import svg2paths
import cadquery as cq
from cadquery import exporters
import numpy as np
from math import sin, cos, sqrt, pi, acos, fmod, degrees
from stl import mesh
import uuid

class blkLibrary:

    def __init__(self, createBlock=False):
        
        #Add Function to CQ 
        cq.Workplane.addSvgPath = addSvgPath
        
        #SVG data
        self.width = None
        self.height = None
        
        self.svgPath = None
        self.paths = None
        self.attributes = None
        self.pathCount = None
        
        #List of path number to skip while parsing
        self.skipPathNumber = []
        
        #Need to rename this to self.blk in the future
        self.base = cq.Workplane('XY').tag('workFace')
        
        # https://www.pinterest.com/pin/63754150967869908/
        self.neckHeight = 2 #This is the SVG 3D height
        self.neckBuffer = 2 #This is a solid buffer between the neck and hollow cutout
        self.bodyHeight = 0 # Calculated later on
        self.constantTypeHeight = 23.31 #This shall never change
        self.overallTypeHeight = 23.31  #This can change if scaleBy changes
        
        self.scaleBy = 1
        
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
        
        #Actual depth is calculated
        self.hollowDepth = None
        
        #Percentage of the height of the block to be cut out for the feet
        self.feetCutOutPercentage = 0.04
        
        #Fillet Amount
        self.filletAmount = 1.2
        
        
    def readSVGFromFile(self, fileName):
        '''
        Sets svgPath to the fileName. When calling parseSVG, svg2Paths can read in a file from disk
        '''
        self.svgPath = fileName
        
        
    def setScale(self, scale):
        '''
        #https://stackoverflow.com/questions/43199869/rotate-and-scale-a-complete-svg-document-using-python
        #https://cairosvg.org/documentation/
        
        #Look at this gist!
        https://gist.github.com/dduan/251cb9816787f3e4125f5cb197d2144e
        
        Or maybe use svgelements
        https://pypi.org/project/svgelements/
        
        Scaling is hard. Scaling is important because SVGs are allowed to have any
        width/height they choose. Most are not in double digits, but rather 100's
        if not 1000's of unitless measurements. Ultimately, the height must be ~23mm
        to meet the 'standard' size. To overcome this, a scale will be set and the 
        code will reflect the scaling. The STL will be scaled at the end to meet 
        the standard type size.
        
        Expected to be 1, 10, 100, 1000, but really can be anything.
        '''
        self.scaleBy = scale
    
    
    def doMath(self):
        '''
        The idea is to read the SVG and add some default values to be used later on. Going to finish the code as-is and then come back to fill in the values here.
        '''
        self.overallTypeHeight = self.overallTypeHeight * self.scaleBy
        #Neck Height must be set before converting SVG to 3D
        #self.neckHeight = self.neckHeight * self.scaleBy
        self.neckBuffer = self.neckBuffer * self.scaleBy
        self.filletAmount = self.filletAmount * self.scaleBy
        
        self.bodyHeight = self.overallTypeHeight - self.neckHeight
        
        
    def estimateSVGSize(self):
        '''
        Sets the estimatedWidth and estimatedHeight for a SVG. 
        
        It's not reliable to get the svgAttributes as this isn't required by the SVG standard.
        
        https://stackoverflow.com/questions/47682830/get-bounding-box-of-svg-drawing
        
        Need to check to make sure self.paths exists
        '''
        
        #Loop though paths derived from parseSVG Fn
        for i, path in enumerate(self.paths):
            if i == 0:
                # Initialise the overall min-max with the first path
                xmin, xmax, ymin, ymax = path.bbox()
            else:
                # Expand bounds to match path bounds if needed
                p_xmin, p_xmax, p_ymin, p_ymax = path.bbox()
                xmin = p_xmin if p_xmin < xmin else xmin
                xmax = p_xmax if p_xmax > xmax else xmax
                ymin = p_ymin if p_ymin < ymin else ymin
                ymax = p_ymax if p_ymax > ymax else ymax

        #print(xmax-xmin, ymax-ymin)
        self.estimatedWidth = xmax - xmin
        self.estimatedHeight = ymax - ymin
        
        
    def parseSVG(self):
        '''
        Given a valid svgPath, svg2paths will return the paths and attributes.
        
        In the future, I hope this could include an HTML link.

        Sets estimated length and width and number of paths
        Need to find a way to get other non-path elements
        - text, shapes, transforms, etc.
        See: https://pypi.org/project/svgelements/

        Should return a warning if non-paths are found. Not
        an error.
        '''
        paths, attributes = svg2paths(self.svgPath)
        self.paths = paths
        self.attributes = attributes
        self.pathCount = len(paths)
        
        svgAttributes = svg2paths(self.svgPath, return_svg_attributes = True)

        

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
            

            
    def buildBoundingBox(self):
        '''
        This function builds a 'box' around the SVG and returns the height and width. Hopefully this will be more useful in the future when the UI can display the w/h and prompt them to scale accordingly.
        '''
        
        bboxTemp = self.base.val().BoundingBox()
        
        #Update the height and width (looking from above)
        self.width = bboxTemp.xlen * self.xLenAdj
        self.height = bboxTemp.ylen * self.yLenAdj
        
        self.centerX = bboxTemp.center.x
        self.centerY = bboxTemp.center.y
        
            
    def buildBody(self):
        '''
        Builds body of the type. Builds a box around the 3D SVG.
        
        Then calculates the body height by subtracting the neck height
        from the overall type height.
        
        Then extrude. Feet will be cut out from the total body.
        
        The offset is required or else an error will occur.
        https://stackoverflow.com/questions/77845206/cadquery-unexpected-valueerror-null-topods-shape-object-during-cut-operation
        '''
        
        self.base = (
                self.base.workplaneFromTagged('workFace')
                .workplane(offset = 0.0001)
                .center(self.centerX, self.centerY)
                .rect(self.width, self.height)
                .extrude(-1*self.bodyHeight)
        )
        
        
    def hollowBody(self):
        '''
        Hollowing could be done in percentage or manual width
        
        Currently percentage only. Hollow Depth is divided by 2 for the pyramid cutout
        in the next step.

        '''
        
        bboxTemp = self.base.faces('<Z').val().BoundingBox()
        
        self.hollowDepth = self.overallTypeHeight - self.neckHeight - self.neckBuffer
        
        #Calculate the x/y wall thickness
        self.xWallThickness = (self.width - (bboxTemp.xlen * self.xhollowPercentage))/2
        self.yWallThickness = (self.height - (bboxTemp.ylen * self.yhollowPercentage))/2
        
        self.base = (
            self.base.faces('<Z')
            .workplane()
            .rect(bboxTemp.xlen * self.xhollowPercentage,
                  bboxTemp.ylen * self.yhollowPercentage)
            .extrude(-1*self.hollowDepth/2, combine='cut')
        )
        
        
    def createAndCutPyramid(self):
        '''
        Creates a new pyramid body. Then removes it from the base body.
        
        It top of the pyramid is set to 1/100 of the hollowed out areas.
        '''
        bboxTemp = self.base.faces('>>Z[2]').val().BoundingBox()
        
        origin = (bboxTemp.center.x,
                  bboxTemp.center.y, 
                  bboxTemp.center.z
                 )
        
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
            .move(bboxTemp.ylen*0.18, 0)                                        #_
            .line(bboxTemp.ylen*0.02, self.height*self.feetCutOutPercentage)    #_/
            .line(bboxTemp.ylen*0.6, 0)                                         #_/----
            .line(bboxTemp.ylen*0.02, -1*self.height*self.feetCutOutPercentage) #_/----\
            .close()
            .extrude(-1*self.width, combine='cut')
        )
           
    def smoothOuterEdges(self):
        self.base = (
            self.base.faces('<Y or >Y or >X or <Z')
            .edges()
            .fillet(self.filletAmount)
        )
        
    def exportSVG(self, folder=None, svgName=None, **kwargs):
        '''
        Look at exporting TJS. Made for ThreeJS
        Doc: https://cadquery.readthedocs.io/en/latest/importexport.html?highlight=Export%20SVG
        '''
        
        if svgName == None:
            svgName = 'svgs/' + str(uuid.uuid4()) + '.svg'

        if folder != None:
            svgName = folder + svgName
        
        #Default options
        opts = {
                "width": 600,
                "height": 400,
                "marginLeft": 60,
                "marginTop": 60,
                "showAxes": False,
                "projectionDir": (0.5, 0.5, 0.5),
                "strokeWidth": 1.6,
                "strokeColor": (0, 0, 0),
                "hiddenColor": (140, 140, 140),
                "showHidden": True,
            }
        
        for key, value in kwargs.items():
            if key == 'projectionDir':
                #print(value)
                opts[key] = value
                
            opts[key] = value
            
        #print(opts)
        
        exporters.export(
            self.base,
            svgName,
            opt=opts,
        )
        
        return svgName
        
    def exportSTL(self, stlName=None, axis='XYZ'):
        '''
        Scales the STL if self.scaleBy is other than 1.
        
        If scaling, axis to scale can be selected.
        
        If no name is given, one will be generated.
        '''
        if stlName == None:
            stlName = str(uuid.uuid4()) + '.stl'
        
        #Verify it ends with stl or add it.
        if stlName[-4:] != '.stl':
            stlName = stlName + '.stl'
            
        #Need to remove in the future. Push to stl folder
        stlName = 'stls/' + stlName
        
        
        if self.scaleBy != 1.0:
            
            tempUUID = str(uuid.uuid4()) + '.stl'
            exporters.export(self.base, tempUUID)
            
            #Load STL
            tempMesh = mesh.Mesh.from_file(tempUUID)

            #Scale
            tempMesh.vectors = tempMesh.vectors/self.scaleBy

            # Export the scaled STL file to 'output.stl'
            tempMesh.save(stlName)
            
            #Delete tempUUID
            
        else:
            exporters.export(self.base, stlName)

            
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
    #print('Fn: Arc_endpoint_to_center')
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
