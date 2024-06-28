from flask import Flask, render_template, g, request
from turbo_flask import Turbo
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.utils import secure_filename
import os
import uuid
import xml.dom.minidom as dom

import svgBlockLib

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'svg', 'xml'}

#https://world.hey.com/georgespencer/using-turbo-flask-to-stream-progress-updates-to-users-without-more-javascript-81479750

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
turbo = Turbo(app)

app.secret_key = 'BAD_SECRET_KEY'

alertTypes = ['alert-primary', 'alert-success', 'alert-warning', 'alert-danger']

class userClass:
    def __init__(self):
        self.id = None

    def createUUID(self):
        id = uuid.uuid4()
        self.id = id
        return id
        

user = userClass()

#Initalize Lib  
blk = svgBlockLib.blkLibrary()

@app.route('/testAlert')
def testAlert():
    print('Fn: testAlert')

    #Must use app_context
    with app.app_context(): 
        g.alertType='success'
        g.alertTitle='Alerts'
        g.alertText='Alerts are working!'
        turbo.push(turbo.update(render_template('_alerts.html'), 'divAlert'))
    
    return {'return':'None'}

@turbo.user_id
def get_user_id():
    return user.id

@app.route('/')
def index():
    #Create a new ID when the page is loaded. 
    #Each time the page is refreshed, a new ID/User is created
    user.createUUID()
    get_user_id()
    return render_template('index.html')


@app.route('/processUpload', methods=['POST'])
def processUpload():
    print('Fn: processUpload')

    if request.method == 'POST':
        
        file = request.files['image_background']
        
        ## Need check to make sure file is an SVG

        #Save file using unique name
        if file:
            filename = str(uuid.uuid4()) + '.svg'
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            #Read SVG and do inital parsing
            blk.readSVGFromFile(app.config['UPLOAD_FOLDER'] + "/" + filename)
            blk.parseSVG()
            blk.estimateSVGSize()

            #Check for elements that are not paths
            nonSVGPathCounts = checkSVGForNonPaths(app.config['UPLOAD_FOLDER'] + "/" + filename)

            g.pathCount = blk.pathCount
            g.estimatedWidth = blk.estimatedWidth
            g.estimatedHeight = blk.estimatedHeight

            #Use estimated width and height to set defaults
            set3DDefaults()
            g.scaleBy = blk.scaleBy

            #Update div
            #with app.app_context(): 
            turbo.push(turbo.update(render_template('_svgStats.html'), 'uploadResultsText'), to=user.id)    


        #Must use app_context
        with app.app_context(): 
            g.alertType='success'
            g.alertTitle='Image'
            g.alertText='Image uploaded to server!'
            turbo.push(turbo.append(render_template('_alerts.html'), 'divAlert'), to=user.id)
        
        if nonSVGPathCounts > 0:
            with app.app_context(): 
                g.alertType='warning'
                g.alertTitle='Caution'
                g.alertText='SVG Contains Non-Path elements. These elements will not be processed and may change the overall look of the SVG.'
                turbo.push(turbo.append(render_template('_alerts.html'), 'divAlert'), to=user.id)


        #Update website values
        scaleName = 'webScale_' + str((int(blk.scaleBy)))
        returnDict = {'status':'success',
                      'setScale': scaleName,
                      }

        return returnDict


def set3DDefaults():
    '''
    After SVG has been parsed, the known height/width can be used to make some
    guesses on the rest of the values. This will hopefully get better over time.
    
    Should defulat values be pushed as g values as well?
    '''

    if max(blk.estimatedHeight, blk.estimatedWidth) < 100:
        blk.neckHeight = 2
        blk.setScale(1)
        blk.feetCutOutPercentage = 0.08
        blk.filletAmount = 0.02
    elif max(blk.estimatedHeight, blk.estimatedWidth) < 1000:
        blk.neckHeight = 20
        blk.setScale(10)
        blk.feetCutOutPercentage = 0.10
        blk.filletAmount = 0.2
    elif max(blk.estimatedHeight, blk.estimatedWidth) < 10000:
        blk.neckHeight = 200
        blk.setScale(100)
        blk.feetCutOutPercentage = 0.12
        blk.filletAmount = 2
    else:
        blk.neckHeight = 2000
        blk.setScale(1000)
        blk.feetCutOutPercentage = 0.14
        blk.filletAmount = 20


@app.route('/processBlockCreation', methods=['POST'])
def processBlockCreation():
    print('Fn: processBlockCreation')

    if request.method == 'POST':

        #Update user
        with app.app_context(): 
            g.alertType='warning'
            g.alertTitle='Processing'
            g.alertText='Crunching numbers... Drawing Lines...'
            turbo.push(turbo.append(render_template('_alerts.html'), 'divAlert'), to=user.id)
        
        
        print(request.json['webNeckHeight'])
        print(request.json['xLenAdj'])
        print(request.json['yLenAdj'])

        #Add some buffer space around the 2D SVG
        blk.neckHeight = float(request.json['webNeckHeight'])
        blk.xLenAdj = float(request.json['xLenAdj'])
        blk.yLenAdj = float(request.json['yLenAdj'])
        blk.xhollowPercentage = float(request.json['xhollowPercentage'])
        blk.yhollowPercentage = float(request.json['yhollowPercentage'])
        blk.feetCutOutPercentage = float(request.json['feetCutOutPercentage'])

        try:
            #Do the actual translation from 2D to 3D
            blk.translate2Dto3D()
            blk.buildBoundingBox()

            #Calculate heights and Width and extrude
            blk.doMath()
            blk.buildBody()

            #Set hollow amount and hollow body
            #blk.xhollowPercentage = 0.8
            #blk.yhollowPercentage = 0.8
            blk.hollowBody()
            blk.createAndCutPyramid()

            #Cut Feet and Fillet
            blk.cutFeet()
            #blk.smoothOuterEdges()

            #Create SVG
            svgResultFilename = blk.exportSVG(folder='static/',
                        projectionDir=(0.5, 0.5, 0.5),
                        strokeColor=(0,0,0),
                        strokeWidth=2.2,
                        hiddenColor=(94,94,94)
                        )
        
            #Update user
            with app.app_context(): 
                g.alertType='success'
                g.alertTitle='Success!'
                g.alertText='SVG Block has been created!'
                turbo.push(turbo.append(render_template('_alerts.html'), 'divAlert'), to=user.id)
            

            #Set name and push update
            g.svgResultFilename = svgResultFilename
            turbo.push(turbo.update(render_template('_svgResult2D.html'), 'result2D'), to=user.id)

            returnDict = {'status':'success'}
            return returnDict

        except:
            #Update user
            with app.app_context(): 
                g.alertType='danger'
                g.alertTitle='Error!'
                g.alertText='SVG Block could not be created!'
                turbo.push(turbo.append(render_template('_alerts.html'), 'divAlert'), to=user.id)

            returnDict = {'status':'error'}
            return returnDict
                

def checkSVGForNonPaths(svgfile):
    '''
    Generated using Ollama & Codellama model. Not very well though
    '''

    # Load an SVG file
    svg = dom.parse(svgfile)

    # Get all elements in the SVG document that are not paths
    elements = svg.getElementsByTagName('*')
    count = 0
    for element in elements:
        if element.tagName != 'path':
            count = count + 1

    return count

