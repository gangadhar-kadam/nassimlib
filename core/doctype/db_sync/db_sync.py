# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt
from __future__ import unicode_literals
import webnotes
from install_erpnext import exec_in_shell
from webnotes.utils import get_base_path, today
import os

class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	def sync_db(self):
		self.remote_to_local()
		self.local_to_remote()		

	def remote_to_local(self):
		#webnotes.errprint("in remote_to_local ")
		remote_settings = self.get_remote_settings()
		#webnotes.errprint("after remote setting return ")
		local_settings = self.get_local_settings()
		#webnotes.errprint("after local setting return ")
		#if table != 'tabSingles':
		try:
				webnotes.errprint("in remote_to_local try ")
				#cc="""mysqldump --host='%(host_id)s'  -u %(remote_dbuser)s -p'%(remote_dbuserpassword)s' %(remote_dbname)s  > %(file_path)s/databasedunp.sql"""%remote_settings
				#webnotes.errprint(cc)
				#dd="""mysqldump --host='%(host_id)s'  -u %(remote_dbuser)s -p'%(remote_dbuserpassword)s' %(remote_dbname)s  > %(file_path)s/databasedunp.sql"""%remote_settings
				#webnotes.errprint(dd)			
				exec_in_shell("""mysqldump --host='%(host_id)s'  -u %(remote_dbuser)s -p'%(remote_dbuserpassword)s' %(remote_dbname)s > %(file_path)s/databasedunp.sql"""%remote_settings)
				#ee="""mysql -u %(dbuser)s -p'%(dbuserpassword)s' %(dbname)s < %(file_path)s/databasedunp.sql"""%local_settings
				#webnotes.errprint(ee)
				#exec_in_shell(ee)
		except Exception as inst: 
				webnotes.msgprint(inst)

	def sync_active_status(self):
		import MySQLdb
		webnotes.errprint([self.doc.host_id, self.doc.remote_dbuser, self.doc.remote_dbuserpassword, self.doc.remote_dbname])
		db = MySQLdb.connect(self.doc.host_id, self.doc.remote_dbuser, self.doc.remote_dbuserpassword, self.doc.remote_dbname)
		cursor = db.cursor()
		is_active = cursor.execute("select value from `tabSingles` where doctype='Global Defaults' and field='is_active'")
		webnotes.errprint(is_active)
		webnotes.conn.sql("update tabSingles set value = '%s' where doctype='Global Defaults' and field='is_active'"%(is_active),debug=1)
		webnotes.conn.sql("commit")
		cursor.execute("commit")


	def get_remote_settings(self):
	    	#webnotes.errprint("in get_remote_settings")
		table=['databasedunp']
		return {'host_id':self.doc.host_id, 'host_ssh_user':self.doc.host_ssh_user, 'host_ssh_password':self.doc.host_ssh_password, 
			'remote_dbuser':self.doc.remote_dbuser, 'remote_dbuserpassword': self.doc.remote_dbuserpassword, 
			'remote_dbname': self.doc.remote_dbname, 'file_path':os.path.join(get_base_path(), "public", "files"), 				'file_name':table[0].replace(' ','_'),'tab': table[0]}

	def get_local_settings(self):
		table=['databasedunp']
		return {'dbuser':self.doc.dbuser, 'dbuserpassword': self.doc.dbuserpassword, 'dbname': self.doc.dbname, 'file_path':os.path.join(get_base_path(), "public", "files"),'file_name':table[0].replace(' ','_'), 'tab': table[0]}


@webnotes.whitelist(allow_guest=True)
def sync_db_out():
	webnotes.errprint("test")
	from webnotes.model.code import get_obj,get_server_obj
	get_obj('DB SYNC', 'DB SYNC').sync_db()
