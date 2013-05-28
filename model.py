import utils
import logging
from google.appengine.ext import db

class User(db.Model):
    name = db.StringProperty(required = True)
    password_hash = db.StringProperty(required = True)
    email = db.StringProperty()
        
    @classmethod
    def by_name(cls, name):
        user = User.all().filter('name =', name).get()
        return user
    
    @classmethod    
    def save_user(cls, username, password):
        user = User(name = username,password_hash = utils.make_pw_hash(username,password))
        user.put()
        return user
    
    @classmethod
    def delete(cls,id):     
        user = User.get_by_id(int(id))
        if user:
            db.delete(user)

class UploadedFile(db.Model):
    name = db.StringProperty(required = True)  
    file = db.BlobProperty(required = True)
    content_type = db.StringProperty(required = True)
    size = db.IntegerProperty()

    @classmethod
    def by_name(cls, name):
        return UploadedFile.all().filter('name =', name).get()
    
    @classmethod    
    def save(cls, name, file, content_type):
        logging.info('file in kb: %s',len(file) / float(1024))
        uploaded_file = UploadedFile(name = name, file = file, content_type = content_type, size = int(len(file) / float(1024)))
        uploaded_file.put()
    
    @classmethod
    def update(cls, uploaded_file, name, file, content_type):
        uploaded_file.name = name
        uploaded_file.file = file
        uploaded_file.content_type = content_type
        uploaded_file.put()
        
        
    @classmethod
    def delete(cls,id):     
        uploaded_file = UploadedFile.get_by_id(int(id))
        if uploaded_file:
            db.delete(uploaded_file)
            
    @classmethod
    def get_uploaded_file(cls, id): 
       return UploadedFile.get_by_id(int(id))

    @classmethod
    def get_all_files(cls):
        return UploadedFile.all()
   
 