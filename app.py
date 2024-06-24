from flask import Flask, render_template, g, request
from turbo_flask import Turbo
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.utils import secure_filename
import os
import uuid


import svgBlockLib

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'svg', 'xml'}

#https://world.hey.com/georgespencer/using-turbo-flask-to-stream-progress-updates-to-users-without-more-javascript-81479750

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
turbo = Turbo(app)

alertTypes = ['alert-primary', 'alert-success', 'alert-warning', 'alert-danger']

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


@app.route('/')
def index():
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
            
            g.pathCount = blk.pathCount
            g.estimatedWidth = blk.estimatedWidth
            g.estimatedHeight = blk.estimatedHeight

            #Use estimated width and height to set defaults
            set3DDefaults()
            g.scaleBy = blk.scaleBy

            #Update div
            turbo.push(turbo.update(render_template('_svgStats.html'), 'uploadResultsText'))    


        #Must use app_context
        with app.app_context(): 
            g.alertType='success'
            g.alertTitle='Image'
            g.alertText='Image uploaded to server!'
            turbo.push(turbo.update(render_template('_alerts.html'), 'divAlert'))
        
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

