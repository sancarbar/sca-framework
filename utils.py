import os
import webapp2
import jinja2
import logging
import cgi
import re
import hashlib
import random
import string
import hmac


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASSWORD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'


secret = '0}~3_dw|I3)@,07c(!=~5c6MD:"v,T'
valid_files_extensions = ['.png','.jpg','.gif','.jpeg','.mp3']
status_pending = "pending"
status_ready = "ready"
status_delivered = "delivered"
#Larger file size supported by GAE
MAX_FILE_SIZE = 1048576

def valid_username(username):
    return USER_RE.match(username)

def valid_password(password):
    return PASSWORD_RE.match(password)

def valid_email(email):
    return EMAIL_RE.match(email)
    
def make_salt():
	return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt=make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)

def valid_pw(name, pw, h):
    salt = h.split(',')[1]
    return h == make_pw_hash(name, pw, salt)
    
def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val
        	
def validate_uploaded_file(file, file_name):
    global valid_files_extensions
    global MAX_FILE_SIZE
    if len(file) >= MAX_FILE_SIZE:
        return 'The uploaded file '+file_name + ' is too big, max size allowed is 1MB'
    for extension in valid_files_extensions:
        if file_name.endswith(extension) or file_name.endswith(extension.upper()):
            return None
    return 'Invalid file extension'

             
	    