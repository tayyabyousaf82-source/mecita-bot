import sqlite3, json, os
from datetime import datetime

class Database:
 def __init__(self):
  self.db_path = os.environ.get('DATABASE_PATH','cita.db')
 def init(self):
  with sqlite3.connect(self.db_path) as c:
   c.execute('''CREATE TABLE IF NOT EXISTS searches(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,tramite TEXT,provincia TEXT,nie TEXT,nombre TEXT,telefono TEXT,email TEXT,status TEXT DEFAULT 'active',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
 def save_search(self,user_id,data):
  with sqlite3.connect(self.db_path) as c:
   cur=c.execute('INSERT INTO searches(user_id,tramite,provincia,nie,nombre,telefono,email)VALUES(?,?,?,?,?,?,?)',(user_id,data['tramite'],data['provincia'],data['nie'],data['nombre'],data['telefono'],data.get('email','')))
   return cur.lastrowid
 def get_user_searches(self,user_id):
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row
   return [dict(r) for r in c.execute('SELECT * FROM searches WHERE user_id=? AND status="active"',(user_id,))]
 def cancel_search(self,sid,uid):
  with sqlite3.connect(self.db_path) as c:
   c.execute('UPDATE searches SET status="cancelled" WHERE id=? AND user_id=?',(sid,uid))
 def mark_booked(self,sid,details):
  with sqlite3.connect(self.db_path) as c:
   c.execute('UPDATE searches SET status="booked",appointment_details=? WHERE id=?',(json.dumps(details),sid))
