from flask import Flask, flash, request, redirect, url_for, g
from werkzeug.utils import secure_filename
import base64
import sqlite3
import logging
import csv
from io import StringIO

app = Flask(__name__)


csvTime = "timestamp"
csvKey = "keycode"

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
        return {"Error": "data was not in b64 format"}
    
    #extract csv from inputData
    csvInputData = getCsv(inputData)
    if csvInputData == None:
        return {"Error": "data was not in csv format"}
    
    #has to be implemented calling the ml model with the video data and returning list of dicts
    videoData = getVideoData(videoData)
    if videoData == None:
        return {"Error": "video data was not in the right format"}
    
    videoData, inputData = convertData(videoData, inputData)
    if videoData is None or inputData is None:
        return {"Error": "video and input data cant be parsed"}

    if not match(videoData, inputData):
        return {"Error": "video and input data didnt match"}

    score = simulateGame(inputData)
    sig = signScore(playerID, score)

    return {"Signature": sig, "Error": "no Error"}


#checks for float conversions
def convertData(videoData, inputData):
    nvideoData = []
    ninputData = []
    for row in videoData:
        try:
            nvideoData.append((float(row[csvTime]),int(row[csvKey])))
        except:
            return None,None
    for row in inputData:
        try:
            ninputData.append((float(row[csvTime]),int(row[csvKey])))
        except:
            return None,None
    return nvideoData, ninputData


#returns true if video and input data match
def match(videoData, inputData):

    #can also be made fancy by adding how long the distance between keys are
    wrongKeys = 0
    #can be made fancy by punishing times not linearly 
    timeOffset = 0.0
    sizeV = len(videoData)
    sizeI = len(inputData)

    itSize = min(sizeV, sizeI)
    for i in range(0,itSize-1):
        timeDiffV = videoData[i+1][0] - videoData[i][0]
        timeDiffI = inputData[i+1][0] - inputData[i][0]
        timeOffset += abs(timeDiffI - timeDiffV)

        if videoData[i][1] != inputData[i][1]:
            wrongKeys += 1

    return rating(wrongKeys, timeOffset, itSize)


#can be made really fancy!!!
#here one avg missed second equals one avg wrong key
def rating(wrongKeys, timeOffset, itSize):
    timeOffsetAvg = timeOffset/itSize
    wrongKeysAvg = wrongKeysAvg/itSize

    if wrongKeysAvg > 0.2:
        return False
    if timeOffsetAvg > 500:
        return False
    return True

#returns the score of the game simulated by the inputData
def simulateGame(inputData):
    return 0

#signs the string playerID:score with the private key of the Server
def signScore(playerID, score):
    return ""

def getCsv(inputData):
    try:
        inputData = inputData.decode("utf-8")
        #string gets interpreted as file for csv parser
        f = StringIO(inputData)
        reader = csv.DictReader(f, delimiter=",")
        if csvKey not in reader.fieldnames or csvTime not in reader.fieldnames:
            return None
        return reader
    except:
        return None

def getVideoData(videoData):
    return [{"test": 1}, {"test2": 2}]