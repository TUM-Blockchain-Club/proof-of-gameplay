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


insertVideo(20, b'lalalaafsfsdfslal')
insertInput(20, b'lalalaaaaaaa')
verify(20)

