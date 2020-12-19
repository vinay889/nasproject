from flask import Flask, jsonify, send_from_directory, request, make_response
from flask_sqlalchemy import SQLAlchemy
import sys
import uuid
import jwt
import datetime
from functools import wraps
from flask_cors import CORS
from smb.SMBConnection import SMBConnection
import os
# from numpy import around
from config import SQLALCHEMY_DATABASE_URI,cifs_host_name,cifs_server_name,cifs_server_ip
from werkzeug.utils import secure_filename



app = Flask(__name__)
CORS(app)
# cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.config['SECRET_KEY']='Th8hFdRV5K2Ykws3cr3t'
app.config['SQLALCHEMY_DATABASE_URI']=SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


#database initialized
db = SQLAlchemy(app)

#Users table created
class Users(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	public_id = db.Column(db.String(50))
	name = db.Column(db.String(50))
	password = db.Column(db.String(50))


# Token authentication function
def token_required(f):
	@wraps(f)
	def decorator(*args, **kwargs):
		token = None
		# print(request.__dict__)
		if 'x-access-tokens' in request.headers:
			token = request.headers['x-access-tokens']
		if not token:
			return jsonify({'message': 'a valid token is missing'})
		try:
			data = jwt.decode(token, app.config['SECRET_KEY'])
			current_user = Users.query.filter_by(public_id=data['public_id']).first()
		except Exception as e:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			filename = exception_traceback.tb_frame.f_code.co_filename
			line_number = exception_traceback.tb_lineno
			print("Exception type: ", exception_type,"\n File name: ", filename,"\n Line number: ", line_number)
			print("Exception: ",e)
			return jsonify({'message': 'token is invalid'})

		return f(current_user, *args, **kwargs)

	return decorator

count=0
#login function
@app.route('/api/login', methods=['GET', 'POST'])
def login_user():
	auth = request.authorization
	if not auth or not auth.username or not auth.password:
		return make_response('could not verify', 401, {'WWW.Authentication': 'Basic real: "login required"'})
	try:
		# Authentication
		if auth.username == "USER1" and auth.password == "vinay143":
			pass
		else:
			return jsonify({"message":"Username or Password is wrong"})
		# getting details from database if present
		user_det = Users.query.filter_by(name=auth.username).first()
		if user_det is None:
			publicID = str(uuid.uuid4())
			new_user = Users(public_id=publicID,name=auth.username,password=auth.password)
			db.session.add(new_user)
			db.session.commit()
			token = jwt.encode({'public_id': publicID, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=20)}, app.config['SECRET_KEY'])
		else:
			token = jwt.encode({'public_id': user_det.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=20)}, app.config['SECRET_KEY'])
		return jsonify({'token' : token.decode('UTF-8')})
	except Exception as e:
		exception_type, exception_object, exception_traceback = sys.exc_info()
		filename = exception_traceback.tb_frame.f_code.co_filename
		line_number = exception_traceback.tb_lineno
		print("Exception type: ", exception_type,"\n File name: ", filename,"\n Line number: ", line_number)
		print("Exception: ",e)
		return jsonify({'message': str(e)})

#to get the file list in starting
@app.route('/api/filelist',methods=['GET','POST'])
@token_required
def filelist(current_user):
	folder_name = request.args.get('folder_name')
	res=getFileList(current_user,folder_name)
	return jsonify(res)

#to download file
@app.route('/api/downloadfile',methods=['GET'])
@token_required
def downlod_file(current_user):
	path = request.args.get('path')
	service_name = request.args.get('service_name')
	if downloadFile(current_user,service_name,path):
		return send_from_directory('./','download',as_attachment=True)
	return False

#to get shared folders in smb server
@app.route('/api/folderlist',methods=['GET'])
@token_required
def folderList(current_user):
	# current_user={'name':'ivtree','password':'ivtree123'}
	res=getFolderlist(current_user)
	return jsonify(res)

#to get file list inside folder
@app.route('/api/folderfilelist',methods=['GET','POST'])
@token_required
def folderFileList(current_user):
	if request.method == 'GET':
		service_name = request.args.get('service_name')
		path = request.args.get('path')
		res=getFolderFileList(current_user,service_name,path)
		return jsonify(res)
	else:
		return jsonify([])

@app.route('/api/uploadFile',methods=['POST'])
@token_required
def uploadFileToServer(current_user):
	try:
		service_name = request.form['service_name']
		path = request.form['path']
		print(service_name,path)
		if 'file' not in request.files:
			return "File not uploaded"
		file = request.files['file']
		if file.filename == '':
			return "File not uploaded"
		if file:
			filename = secure_filename(file.filename)
			path=path+'/'+filename
			uploadFile(current_user,service_name,path,file)
			return "File uploaded"
		else:
			return "File not uploaded"
	except Exception as e:
		exception_type, exception_object, exception_traceback = sys.exc_info()
		filename = exception_traceback.tb_frame.f_code.co_filename
		line_number = exception_traceback.tb_lineno
		print("Exception type: ", exception_type,"\n File name: ", filename,"\n Line number: ", line_number)
		print("Exception: ",e)
		return jsonify(e)


def getFileList(current_user,folder_name):
	userID = current_user.name
	password = current_user.password
	service_name = folder_name
	file_list=[]
	try:
		conn = SMBConnection(userID, password, cifs_host_name, cifs_server_name, use_ntlm_v2 = True)
		conn.connect(cifs_server_ip, 139)
		res = conn.listPath(service_name,'/',timeout=30)
		for i in range(len(res)):
			filename = res[i].filename
			if filename in [".",".."]:
				pass
			else:
				file_size = res[i].file_size
				fil_size = file_size/1024
				filesize=f'{fil_size:.2f}'
				last_write_time = (datetime.datetime.fromtimestamp(res[i].last_write_time)).strftime('%Y-%m-%d %H:%M:%S')
				create_time = (datetime.datetime.fromtimestamp(res[i].create_time)).strftime('%Y-%m-%d %H:%M:%S')
				if res[i].file_attributes == 32:
					file_type = "file"
				elif res[i].file_attributes == 16:
					file_type = "DIR"
				else:
					file_type = "Other"
				file_list.append({'file_name':filename,'size':filesize,'last_write_time':last_write_time,'create_time':create_time,'file_type':file_type,'service_name':service_name,'path':''})
	except Exception as e:
		exception_type, exception_object, exception_traceback = sys.exc_info()
		filename = exception_traceback.tb_frame.f_code.co_filename
		line_number = exception_traceback.tb_lineno
		print("Exception type: ", exception_type,"\n File name: ", filename,"\n Line number: ", line_number)
		print("Exception: ",e)
	# print(file_list)
	return file_list

def getFolderlist(current_user):
	userID = current_user.name
	password = current_user.password
	folder_list=[]
	try:
		conn = SMBConnection(userID, password, cifs_host_name, cifs_server_name, use_ntlm_v2 = True)
		conn.connect(cifs_server_ip, 139)
		Response = conn.listShares(timeout=30)
		for i in range(len(Response)):
			folder_list.append(Response[i].name)
	except Exception as e:
		exception_type, exception_object, exception_traceback = sys.exc_info()
		filename = exception_traceback.tb_frame.f_code.co_filename
		line_number = exception_traceback.tb_lineno
		print("Exception type: ", exception_type,"\n File name: ", filename,"\n Line number: ", line_number)
		print("Exception: ",e)
	return folder_list

def getFolderFileList(current_user,service_name,path):
	userID = current_user.name
	password = current_user.password
	file_list=[]
	try:
		conn = SMBConnection(userID, password, cifs_host_name, cifs_server_name, use_ntlm_v2 = True)
		conn.connect(cifs_server_ip, 139)
		res = conn.listPath(service_name,path,timeout=30)
		for i in range(len(res)):
			filename = res[i].filename
			if filename in [".",".."]:
				pass
			else:
				file_size = res[i].file_size
				fil_size = file_size/1024
				filesize=f'{fil_size:.2f}' 
				last_write_time = (datetime.datetime.fromtimestamp(res[i].last_write_time)).strftime('%Y-%m-%d %H:%M:%S')
				create_time = (datetime.datetime.fromtimestamp(res[i].create_time)).strftime('%Y-%m-%d %H:%M:%S')
				if res[i].file_attributes == 32:
					file_type = "file"
				elif res[i].file_attributes == 16:
					file_type = "DIR"
				else:
					file_type = "Other"
				file_list.append({'file_name':filename,'size':filesize,'last_write_time':last_write_time,'create_time':create_time,'file_type':file_type,'service_name':service_name,'path':path})
	except Exception as e:
		exception_type, exception_object, exception_traceback = sys.exc_info()
		filename = exception_traceback.tb_frame.f_code.co_filename
		line_number = exception_traceback.tb_lineno
		print("Exception type: ", exception_type,"\n File name: ", filename,"\n Line number: ", line_number)
		print("Exception: ",e)
	# print(file_list)
	return file_list

def downloadFile(current_user,service_name,path):
	userID = current_user.name
	password = current_user.password
	try:
		conn = SMBConnection(userID, password, cifs_host_name, cifs_server_name, use_ntlm_v2 = True)
		conn.connect(cifs_server_ip, 139)
		with open('./download','wb') as fp:
			print(path)
			file_attributes, filesize = conn.retrieveFile(service_name, path, fp)
	except Exception as e:
		exception_type, exception_object, exception_traceback = sys.exc_info()
		filename = exception_traceback.tb_frame.f_code.co_filename
		line_number = exception_traceback.tb_lineno
		print("Exception type: ", exception_type,"\n File name: ", filename,"\n Line number: ", line_number)
		print("Exception: ",e)
		return False
	return True

def uploadFile(current_user,service_name,path,file):
	userID = current_user.name
	password = current_user.password
	try:
		conn = SMBConnection(userID, password, cifs_host_name, cifs_server_name, use_ntlm_v2 = True)
		conn.connect(cifs_server_ip, 139)
		conn.storeFile(service_name, path, file)
	except Exception as e:
		exception_type, exception_object, exception_traceback = sys.exc_info()
		filename = exception_traceback.tb_frame.f_code.co_filename
		line_number = exception_traceback.tb_lineno
		print("Exception type: ", exception_type,"\n File name: ", filename,"\n Line number: ", line_number)
		print("Exception: ",e)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
