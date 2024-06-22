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
            g.svgPathCount = blk.pathCount
            g.svgWidth = blk.estimatedWidth
            g.svgHeight = blk.estimatedHeight
            g.setScale = 1
            turbo.push(turbo.update(render_template('_svgStats.html'), 'uploadResultsText'))    


        #Must use app_context
        with app.app_context(): 
            g.alertType='success'
            g.alertTitle='Image'
            g.alertText='Image uploaded to server!'
            turbo.push(turbo.update(render_template('_alerts.html'), 'divAlert'))
        
        return {'status':'success'}
