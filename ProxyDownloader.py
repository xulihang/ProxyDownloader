#coding=utf-8
from bottle import route, run, template, request, static_file
import uuid
import requests
import re
import threading
import os

files={}
uidsWithNameAndLengthAsKey={}
equivalent={}

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
    r = requests.get(url, stream=True)
    filename=getFilename(r,url)
    filnameAndLength=filename+"	"+r.headers["Content-Length"]
    
    if alreadyDownloaded(filnameAndLength,uid)==True:
        return
    
    percent_path = "{path}/{file}".format(path=save_path, file=uid+"-percent")
    file_path = "{path}/{file}".format(path=save_path, file=uid)
    if os.path.exists(file_path)==True:
        os.remove(file_path)
    
    fw = open(file_path, "wb")
    for chunk in r.iter_content(chunk_size=512):
      if chunk:
          fw.write(chunk)
          writePercent(r,percent_path)    
    fw.close()
    
    files[uid]=filename
    
    uidList=[]
    if filnameAndLength in uidsWithNameAndLengthAsKey:
        uidList=uidsWithNameAndLengthAsKey[filnameAndLength]
    uidList.append(uid)
    uidsWithNameAndLengthAsKey[filnameAndLength]=uidList
    
    print("downloaded")

def writePercent(r,percent_path):
    length=int(r.headers["Content-Length"])
    length_remaining=r.raw.length_remaining
    remainingPercent=1.0
    remainingPercent=length_remaining/length
    percent=1-remainingPercent
    f=open(percent_path,"w")
    f.write(str(percent))
    f.close()
    
def alreadyDownloaded(filnameAndLength,currentUid):
    if filnameAndLength in uidsWithNameAndLengthAsKey:
        uidList=uidsWithNameAndLengthAsKey[filnameAndLength]
        for uid in uidList:
            if str(readPercent(uid))==str(1.0):
                file_path = "{path}/{file}".format(path=save_path, file=uid)
                if os.path.exists(file_path)==True:
                    equivalent[currentUid]=uid
                    print("already downloaded")
                    return True
    return False        

    
    
    
@route('/retrieve', method='GET')   
def retrieve():
    uid = str(request.query.uid)
    print(uid)
    if uid in equivalent:
        uid=equivalent[uid]
    
    if uid in files:
        filename=files[uid]
    else:
        filename=uid
    
    file_path = "{path}/{file}".format(path=save_path, file=uid)
    percent=readPercent(uid)
    
    if os.path.exists(file_path)==True and str(percent)==str(1.0):
        return static_file(uid, root=save_path, download=filename) 
    else:
        return "percent: "+str(percent)
    

def readPercent(uid):
    percent_path = "{path}/{file}".format(path=save_path, file=uid+"-percent")
    percent=0.0
    if os.path.exists(percent_path)==True:
        f=open(percent_path,"r")
        percent=f.read()
        f.close()
    return percent

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