#coding=utf-8
from bottle import route, run, template, request, static_file
import uuid
import requests
import re
import threading
import os

files={}

@route('/download', method='POST')
def download():
    url = request.forms.get('url')
    uid = str(uuid.uuid1())
    timer = threading.Timer(3, writeContent,(url,uid))
    timer.start()
    print(uid)
    return '''<a href="/retrieve?uid={uniqueID}">Retrival Link (please wait for the file to be downloaded)</a>'''.format(uniqueID=uid)
    
def writeContent(url,uid):
    print(url)
    r = requests.get(url)
    filename=getFilename(r,url)
    file_path = "{path}/{file}".format(path=save_path, file=uid)
    if os.path.exists(file_path)==True:
        os.remove(file_path)  
    fw=open(file_path,"wb")
    fw.write(r.content)
    fw.close()
    files[uid]=filename
    print("downloaded")

@route('/retrieve', method='GET')   
def retrieve():
    uid = str(request.query.uid)
    print(uid)
    if uid in files:
        filename=files[uid]
    else:
        filename=uid
    file_path = "{path}/{file}".format(path=save_path, file=uid)
    if os.path.exists(file_path)==True:
        return static_file(uid, root=save_path, download=filename) 
    else:
        return "not yet downloaded"
    
    
def getFilename(r,url):
    fname="default"
    try:
        if "Content-Disposition" in r.headers.keys():
            fname = re.findall("filename=(.+)", r.headers["Content-Disposition"])[0]
            fname=fname.replace("\"","")
        else:
            fname = url.split("/")[-1]
    except Exception as e:
        print('Error:',e)
    return fname

@route('/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='www')    

    
def clean():
    for filename in os.listdir(save_path):
        file_path = "{path}/{file}".format(path=save_path, file=filename)
        os.remove(file_path)
    
save_path = "./temp/"
if not os.path.exists(save_path):
    os.makedirs(save_path)

timer = threading.Timer(60*60*2, clean)
timer.start()

run(server="paste",host='0.0.0.0', port=51040)   