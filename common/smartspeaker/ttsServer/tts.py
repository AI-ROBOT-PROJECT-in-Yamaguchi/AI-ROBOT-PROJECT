import pyttsx3
from http.server import HTTPServer,BaseHTTPRequestHandler
import urllib
import urllib.request
import urllib.parse
from socketserver import ThreadingMixIn
import uuid
import os
import os.path
import traceback
import time
from gtts import gTTS


class TTSEngine:
    def __init__(self):
        self.engine=pyttsx3.init()

    def convert(self,text,filename,**option):
        for key in option:
            if(key == "rate"):
                self.engine.setProperty(key,int(option[key]))
            elif(key == "volume"):
                self.engine.setProperty(key,float(option[key]))
            elif(key == "voice"):
                self.engine.setProperty(key,self.engine.getProperty("voices")[int(option[key])].id)
        self.engine.setProperty("voice","japanese")
        self.engine.save_to_file(text,filename)
        self.engine.runAndWait()
        time.sleep(1)

    def getOption(self,key):
        return self.engine.getProperty(key)

def serverRun(server_class=HTTPServer,handler_class=BaseHTTPRequestHandler):
    server_address = ('',int(os.environ.get('PORT',5000)))
    httpd = server_class(server_address,handler_class)
    httpd.serve_forever()

class httpHandler(BaseHTTPRequestHandler):
    def analyzeQuery(self,query):
        if(len(query)>0):
            return {
                        key:urllib.parse.unquote(value.replace("+"," "))
                        for key,value in 
                        [
                            equation.split("=")
                            for equation in query.split("&")
                        ]
                    }
        else:
            return {} 

    def analyzeUrl(self,url):
        res={}
        url = urllib.parse.urlparse(url)
        if(len(url.path)==0 or url.path[0]!='/'):
            url["path"]="/"+url.path
        else:
            res["path"]=url.path
        base,ext = os.path.splitext(res["path"])
        res["base"]=base
        res["ext"]=ext[1:]
        res["query"]=self.analyzeQuery(url.query)
        return res

    def analyzeRequest(self,method):
        request=self.analyzeUrl(self.path)
        if(method=="POST"):
            request["query"]=self.analyzeQuery(self.rfile.read(int(self.headers["Content-Length"])).decode())
        return request

    def sendResponse(self,response):
        if("code" in response):
            self.send_response(response["code"])
        else:
            return
        if("header" in response):
            for key in response["header"]:
                self.send_header(key,response["header"][key])
        self.end_headers()
        if("body" in response):
            self.wfile.write(response["body"])

    def response_file(self,filename,contentType):
        with open(filename,"rb") as f:
            self.sendResponse(
                {
                    "code":200,
                    "header":{
                        "Content-Type":contentType
                    },
                    "body":f.read(-1)
                }
            )

    def response_tts(self,text,ext,**opt):
        #engine=TTSEngine()
        filename="./"+str(uuid.uuid1())[:10].replace("-","")+"."+ext
        print("tmpfile:"+filename)
        #engine.convert(text,filename,**opt)
        gTTS(text=text,**opt).save(filename)
        self.response_file(filename,"audio/"+ext)
        os.remove(filename)

    def response_getOption(self,key):
        engine=TTSEngine()
        self.sendResponse(
            {
                "code":200,
                "header":{
                    "Content-Type":"text/plain"
                },
                "body":str(engine.getOption(key)).encode()
            }
        )

    def response_redirect(self,path):
        self.sendResponse(
            {
                "code":303,
                "header":{
                    "Location":path
                }
            }
        )

    def response_notFound(self):
        self.sendResponse(
            {
                "code":404,
                "header":{
                    "Content-Type":"text/plain"
                },
                "body":"404 Not found".encode()
            }
        )
    
    def response_error(self):
        self.sendResponse(
            {
                "code":500,
                "header":{
                    "Content-Type":"text/plain"
                },
                "body":(traceback.format_exc()).encode()
            }
        )

    def response(self,url):
        try:
            if(url["path"] == "/"):
                self.response_redirect("/index.html")
            elif(url["path"] == "/index.html"):
                self.response_file("index.html","text/html")
            elif(url["path"] == "/getOption"):
                self.response_getOption(url["query"]["key"])
            elif(url["ext"] in ("wav","mp3")):
                option={
                        key:url["query"][key]
                        for key in url["query"]
                        if not key in ("text","ext")
                    }
                self.response_tts(url["query"]["text"],url["ext"],**option)
            else:
                self.response_notFound()
        except Exception as e:
            self.response_error()

    def printRequest(self,request):
        print(request)
        
    def do_GET(self):
        print("GET:"+self.path)
        req=self.analyzeRequest("GET")
        self.printRequest(req)
        self.response(req)
        self.close_connection=True

    def do_POST(self):
        print("POST:"+self.path)
        req=self.analyzeRequest("POST")
        self.printRequest(req)
        self.response(req)
        self.close_connection=True

class MultiThreadServer(ThreadingMixIn,HTTPServer):
    pass

serverRun(HTTPServer,httpHandler)
