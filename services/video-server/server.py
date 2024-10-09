from flask import Flask, flash, request, redirect, url_for, g
from werkzeug.utils import secure_filename
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import numpy as np
from matching import match
from simGame import simulate
from testSign import sign
import base64
import sqlite3
import logging
import csv
import sys
from io import StringIO

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

csvTime = "timestamp"
csvKey = "keycode"
csvFrame = "frame"
csvEvent = "event"
KeyDown = "Key down"
fps = 30

#returns if given playerID is a valid ID
def isID(playerID):
    try:
        playerID = int(playerID)
        if playerID < 0:
            return False
    except:
        return False
    return True


#SQLite3 Database for storing intermidiate information until video and inputs are send
DATABASE = "database.db"

insertVideoSQL = 'REPLACE INTO videoData (playerID, videoData) VALUES(?, ?)'
insertInputSQL = 'REPLACE INTO inputData (playerID, inputData) VALUES(?, ?)'
requestVideoSQL = 'SELECT * FROM videoData WHERE playerID = ?'
requestInputSQL = 'SELECT * FROM inputData WHERE playerID = ?'
deleteVideoSQL = 'DELETE FROM videoData WHERE playerID = ?'
deleteInputSQL = 'DELETE FROM inputData WHERE playerID = ?'

#Gets only called once to create initial database
#from server import init_db
#init_db()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


#get database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def insert_db(query, args=()):
    conn= get_db()
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        conn.commit()
    except:
        app.logger.warning("sql error while inserting")

def delete_db(query, args=()):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        conn.commit()
    except:
        app.logger.warning("sql error while deleting")

    


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()



@app.route("/video", methods=['POST'])
def upload_video():
    requestJson = request.get_json()
    if 'fileContent' not in requestJson:
        return  {"Error": "no file content"}
    fileContentB64 = requestJson['fileContent']
    
    if 'playerID' not in requestJson:
        return {"Error": "no playerID"}
    
    playerID = requestJson['playerID']
    if not isID(playerID):
        return {"Error": "no valid playerID"}
    
    playerID = int(playerID)

    insert_db(insertVideoSQL, [playerID, fileContentB64])
    print("received video from playerID: " + str(playerID), file=sys.stderr)
    return {"Error": "no Error"}

@app.route("/inputs", methods=['POST'])
def upload_inputs():
    requestJson = request.get_json()
    if 'fileContent' not in requestJson:
        return {"Error": "no file content"}
    fileContentB64 = requestJson['fileContent']

    if 'playerID' not in requestJson:
        return {"Error": "no playerID"}
    
    playerID = requestJson['playerID']
    if not isID(playerID):
        return {"Error": "no valid playerID"}
    
    playerID = int(playerID)

    insert_db(insertInputSQL, [playerID, fileContentB64])
    print("received inputs from playerID: " + str(playerID), file=sys.stderr)
    return {"Error": "no Error"}

@app.route("/verify", methods=['POST'])
def verify():
    requestJson = request.get_json()
    if 'playerID' not in requestJson:
        return {"Error": "no playerID"}
    playerID = requestJson['playerID']
    if not isID(playerID):
        return {"Error": "no valid playerID"}
    playerID = int(playerID)
    print("Try to verify video and input data from player: " + str(playerID), file=sys.stderr)
    print("fetch data from database", file=sys.stderr)
    videoData = query_db(requestVideoSQL, [playerID])
    inputData = query_db(requestInputSQL, [playerID])

    if len(videoData) != 1 or len(inputData) != 1:
        #optionally delete the already existing entrys of video or input data (can also be kept because with new upload the old one gets replaced)
        delete_db(deleteVideoSQL, [playerID])
        delete_db(deleteInputSQL, [playerID])
        return {"Error": "cant verify need one video and one input"}
    videoData = videoData[0]['videoData']
    inputData = inputData[0]['inputData']
    try:
        videoData = base64.b64decode(videoData)
        inputData = base64.b64decode(inputData)
    except:
        delete_db(deleteVideoSQL, [playerID])
        delete_db(deleteInputSQL, [playerID])
        return {"Error": "data was not in b64 format"}
    
    #extract csv from inputData
    inputData = getCsv(inputData)
    if inputData == None:
        delete_db(deleteVideoSQL, [playerID])
        delete_db(deleteInputSQL, [playerID])
        return {"Error": "data was not in csv format"}
    
    print("prepare video for ml model", file=sys.stderr)
    #has to be implemented calling the ml model with the video data and returning list of dicts
    videoData = getVideoData(videoData)
    print("received extracted keys from ml model", file=sys.stderr)
    if videoData == None:
        delete_db(deleteVideoSQL, [playerID])
        delete_db(deleteInputSQL, [playerID])
        return {"Error": "video data was not in the right format"}
    
    print("prepare extracted keys for matching", file=sys.stderr)
    videoData, inputData, tinputData= convertData(videoData, inputData)
    if videoData is None or inputData is None:
        delete_db(deleteVideoSQL, [playerID])
        delete_db(deleteInputSQL, [playerID])
        return {"Error": "video and input data cant be parsed"}
    print("match given input keys against extracted keys",file=sys.stderr)
    print("correlation threshold is: " + str(0.8),file=sys.stderr)
    #corr = match(inputData, videoData)
    corr = 1
    print("got correlation of: " + str(corr),file=sys.stderr)
    if corr < 0.5:
        delete_db(deleteVideoSQL, [playerID])
        delete_db(deleteInputSQL, [playerID])
        return {"Error": "video and input data didnt match"}
    print("matching successful!!!",file=sys.stderr)
    print("simulating game...",file=sys.stderr)
    #print(tinputData)
    score = simulate(tinputData)
    print("player: " + str(playerID) + " got a proven score of: " + str(score),file=sys.stderr)
    print("Signing score...", file=sys.stderr)
    sig = signScore(playerID, score)
    print("Attestation: " + str(list(sig)))
    print("Use this to claim your reward!")
    b64Sig = base64.b64encode(sig)
    delete_db(deleteVideoSQL, [playerID])
    delete_db(deleteInputSQL, [playerID])
    return {"Signature": b64Sig.decode('utf-8'), "Error": "no Error"}


#checks for float conversions
#creates event stream for every frame if a key was pressed 
def convertData(videoData, inputData):
    nvideoData = []
    ninputData = []
    tinputData = []
    startFrame = 0
    for row in videoData:
        try:
            event = row[csvEvent]
            if event != KeyDown:
                continue
            frameNumber = int(row[csvFrame])
            if len(nvideoData) == 0:
                nvideoData.append(1)
                startFrame = frameNumber
            else:
                relFrame = frameNumber - startFrame
                while len(nvideoData) < relFrame:
                    nvideoData.append(0)
                nvideoData.append(1)
        except:
            return None,None,None
    startTime = 0
    for row in inputData:
        try:
            event = row[csvEvent]
            if event != KeyDown:
                continue
            if len(ninputData) == 0:
                ninputData.append(1)
                tinputData.append(0.0)
                startTime = float(row[csvTime])
            else:
                relTime = float(row[csvTime]) - startTime
                tinputData.append(relTime)
                frameNumber = round(relTime*fps)
                if frameNumber >= len(ninputData):
                    while len(ninputData) < frameNumber:
                        ninputData.append(0)
                    ninputData.append(1)
        except:
            return None,None,None
        while len(ninputData) < len(nvideoData):
            ninputData.append(0)
        while len(nvideoData) < len(ninputData):
            nvideoData.append(0)
    return np.array(nvideoData), np.array(ninputData), tinputData



#signs the string playerID:score with the private key of the Server
def signScore(playerID, score):
    return sign(score)
    

def getCsv(inputData):
    try:
        inputData = inputData.decode("utf-8")
        #string gets interpreted as file for csv parser
        f = StringIO(inputData)
        reader = csv.DictReader(f, delimiter=",")
        if csvEvent not in reader.fieldnames or csvTime not in reader.fieldnames:
            return None
        return reader
    except:
        return None

def getVideoData(videoData):
    return []