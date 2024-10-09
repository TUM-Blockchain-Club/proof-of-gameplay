import requests
import base64


def insertVideo(id, content):   
    fileContentB64 = base64.b64encode(content)
    json = {'playerID': id, 'fileContent': fileContentB64.decode('utf-8')}
    r = requests.post('http://127.0.0.1:5000/video', json=json)
    print(r.text)

def insertInput(id, content):
    fileContentB64 = base64.b64encode(content)
    json = {'playerID': id, 'fileContent': fileContentB64.decode('utf-8')}
    r = requests.post('http://127.0.0.1:5000/inputs', json=json)
    print(r.text)

def verify(id):
    json = {'playerID': id}
    r = requests.post('http://127.0.0.1:5000/verify', json=json)
    print(r.text)



with open("bigMsg.mp4", "rb") as f:
    data = f.read()
    insertVideo(570978, data)
    inputss = """timestamp,event\n
                    1728440536.912487,Key down\n
                    1728440537.7617981,Key down\n
                    1728440538.3267615,Key down\n
                    1728440538.8919914,Key down\n
                    1728440539.416842,Key down\n
                    1728440539.9445367,Key down\n
                    1728440540.388739,Key down\n
                    1728440540.9105444,Key down\n
                    1728440541.679038,Key down\n
                    1728440542.202866,Key down\n
                    1728440542.5667918,Key down\n
                    1728440542.9312754,Key down\n
                    1728440543.3348107,Key down\n
                    1728440544.2647312,Key down\n
                    1728440544.7109435,Key down\n
                    1728440545.2340498,Key down\n
                    1728440545.8787706,Key down\n
                    1728440546.360577,Key down\n
                    1728440546.8468964,Key down\n
                    1728440547.1710625,Key down\n
                    1728440548.0610025,Key down\n
                    1728440548.5848339,Key down\n
                    1728440548.8268871,Key down\n
                    1728440549.0319767,Key down\n
                    1728440549.2323492,Key down\n
                    1728440549.6379147,Key down"""
    insertInput(570978, bytes(inputss, 'utf-8'))
    verify(570978)

