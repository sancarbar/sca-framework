#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import webapp2
import jinja2
import logging
import json
import utils
import model
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.api import channel

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), 
                               autoescape=True, extensions=['jinja2.ext.i18n'])
						   
#Web Sockets Tokens
channel_id = 'test'

memcache_key = 'example'

#Update memcache
def get_example(update = False):
    example = memcache.get(memcache_key)
    if example is None or update:
        #example = model.Example.get_all()  load data model
        memcache.set(memcache_key, example)  #Update memcache
    return example 

class WebHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
        
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
        
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
    
    def render_params(self, template, parameters):
        template = jinja_env.get_template(template)
        self.response.out.write(template.render(parameters))
    
    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_txt)
        
    def set_secure_cookie(self, name, val):
        cookie_val = utils.make_secure_val(val)
        self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (name, cookie_val))
    
    def set_order_cookie(self, order):
        self.response.headers.add_header('Set-Cookie', 'order=%s; Path=/order' % order)
            
    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and utils.check_secure_val(cookie_val)
    
    def read_order_cookie(self):
        cookie_val = self.request.cookies.get('order')
        return cookie_val

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        
    def send_web_message(self, channel_id, message):
        if message and channel_id:
            channel.send_message(channel_id, message)
            
    def get_current_user(self):
        uid = self.read_secure_cookie('user_id')
        user = None
    	if uid and model.User.get_by_id(int(uid)):
            user = model.User.get_by_id(int(uid))
        return user
        
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        #uid = self.read_secure_cookie('user_id')
        #self.user = uid and User.by_id(int(uid))
        if self.request.url.endswith('.json'):
            self.format = 'json'
        else:
            self.format = 'html'


#AJAX Support
class RPCHandler(webapp.RequestHandler):
    """ Allows the functions defined in the RPCMethods class to be RPCed."""
    def __init__(self, request=None, response=None):
        webapp.RequestHandler.__init__(self, request = request, response = response)
        self.methods = RPCMethods()

    def get(self):
        func = None

        action = self.request.get('action')
        if action:
            if action[0] == '_':
                self.error(403) # access denied
                return
            else:
                func = getattr(self.methods, action, None)

        if not func:
            self.error(404) # file not found
            return

        args = ()
        while True:
            key = 'arg%d' % len(args)
            val = self.request.get(key)
            if val:
                args += (json.loads(val),)
            else:
                break
        result = func(*args)
        logging.info("result: %s",result)
        self.response.out.write(json.dumps(result))

#AJAX Support
class RPCMethods:
    """ Defines the methods that can be RPCed.
    NOTE: Do not allow remote callers access to private/protected "_*" methods.
    """

    def Add(self, *args):
        # The JSON encoding may have encoded integers as strings.
        # Be sure to convert args to any mandatory type(s).
        ints = [int(arg) for arg in args]
        return sum(ints)

class Login(WebHandler):
    def get(self):
        self.render('login.html')
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        logging.info("User: %s", username)
        user = model.User.by_name(username)
        if user and utils.valid_pw(username, password, user.password_hash):
            logging.info("User Valid %s", user.name)
            self.set_secure_cookie('user_id',str(user.key().id()))
            self.redirect("/")
        else:    
            self.render('login.html',username = username,error = 'Invalid login')

class FileHandler(WebHandler):
    def get(self):
        object = model.db.get(self.request.get("file_id"))
        logging.info("object unicoded %s",object.content_type.encode('unicode-escape'))
        if object.file:
            self.response.headers['Content-Type'] = object.content_type.encode('unicode-escape')
            self.response.out.write(object.file)
        else:
            self.error(404)
            

class Signup(WebHandler):
    def get(self):
        parameters = {'title': 'Signup',
                      'user': self.get_current_user(),
                      'logout_url': '/logout'}
        self.render_params('signup.html', parameters)
        
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')
        if not utils.valid_username(username) or not utils.valid_password(password) or (not utils.valid_email(email) and "" != email) or password != verify:
            errorUsername = ""
            errorPassword = ""
            errorVerify = ""
            errorEmail = ""
            if not utils.valid_username(username):
                errorUsername = "That's not a valid username."
            if not utils.valid_password(password):
                errorPassword = "That wasn't a valid password."
            if not utils.valid_email(email) and "" != email:
                errorEmail = "That's not a valid email."
            if password != verify:
                errorVerify = "Your passwords didn't match."
            self.render('signup.html',errorUsername=errorUsername,errorPassword=errorPassword,errorVerify=errorVerify,errorEmail=errorEmail, username=username, email=email)
        else:
            if not model.User.by_name(username):
                user = model.User.save_user(username,password)
                self.set_secure_cookie('user_id',str(user.key().id()))
                self.redirect('/')
            else:
                errorUsername = 'That user already exists.'
                self.render('signup.html',errorUsername=errorUsername)

class Logout(WebHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        self.redirect("/")
        
class WebServicesHandlerREST(WebHandler):
    def get(self,id):
        logging.info("GET ItemREST %s",id)

    def post(self,id):
        logging.info("POST ItemREST %s",id)
        
class AjaxTest(WebHandler):
    def get(self):
        parameters = {'title': 'AJAX Test',
                      'user': self.get_current_user()}
        self.render_params('ajax.html', parameters)
        
class MessageWebSocketHandler(WebHandler):
    def get(self):
        parameters = {'title': 'WEB Socket Messenger'}
        self.render_params('messenger_websocket.html', parameters)
        
class WebSocketHandler(WebHandler):
    def get(self):
        global channel_id
        parameters = {'title': 'WEB Sockets Test',
                      'token': channel.create_channel(channel_id),
                      'user': self.get_current_user()
                      }
        self.render_params('websockets.html', parameters)
        
    def post(self):
        message = {'message': self.request.get('message')}
        global channel_id
        self.send_web_message(channel_id, json.dumps(message))
        parameters = {'title': 'WEB Socket Messenger'}
        self.render_params('messenger_websocket.html', parameters)

class FileUploaderHandler(WebHandler):
    def get(self):
        parameters = {'title':'File Uploader',
                        'files': model.UploadedFile.get_all_files()}
        self.render_params('uploadFile.html', parameters)
    def post(self):
        file = self.request.get("file")
        file_name = self.request.POST['file'].filename
        error = utils.validate_uploaded_file(file, file_name)
        if(not error):
            model.UploadedFile.save(file_name, file, self.request.POST['file'].type)
        parameters = {'title': 'File Uploader',
                      'files': model.UploadedFile.get_all_files(),
                        'error': error}
        self.render_params('uploadFile.html', parameters)


		
class MainHandler(WebHandler):
    def get(self):
        parameters = {'title': 'Index',
                      'user': self.get_current_user(),
                      'logout_url': '/logout'}
        self.render_params('index.html', parameters)
        


app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/signup', Signup),
                               ('/rest/([0-9]+)', WebServicesHandlerREST),
                               ('/file', FileHandler),
                               ('/rpc', RPCHandler),
                               ('/ajax', AjaxTest),
                               ('/websocket', WebSocketHandler),
                               ('/messenger_websocket', MessageWebSocketHandler),
                               ('/upload', FileUploaderHandler)
                               ],debug=True)
