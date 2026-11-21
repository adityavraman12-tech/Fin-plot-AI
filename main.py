# FinPilot API. Educational demonstration; review before handling real financial data.
import os,sqlite3,secrets,hashlib,hmac,base64,json,time,re
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from fastapi import FastAPI,HTTPException,Depends,Header,UploadFile,File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,Field
from typing import Literal,Optional

SECRET=os.getenv('FINPILOT_SECRET','')
if len(SECRET)<32: raise RuntimeError('Set FINPILOT_SECRET to a random string of at least 32 characters')
DB=os.getenv('FINPILOT_DB','finpilot.sqlite3')
app=FastAPI(title='FinPilot Integrated API',version='2.0.0')
origins=[x.strip() for x in os.getenv('CORS_ORIGINS','http://localhost:8000,http://localhost:5500').split(',') if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=False,allow_methods=['GET','POST','PUT','PATCH','DELETE'],allow_headers=['Authorization','Content-Type'])
@contextmanager
def db():
    con=sqlite3.connect(DB,timeout=15);con.row_factory=sqlite3.Row
    try: yield con;con.commit()
    finally: con.close()
with db() as c:
    c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE NOT NULL,name TEXT,password_hash TEXT NOT NULL,created_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id INTEGER NOT NULL,expires INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS transactions(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL,merchant TEXT NOT NULL,amount REAL NOT NULL,transaction_date TEXT NOT NULL,category TEXT NOT NULL,transaction_type TEXT NOT NULL,description TEXT DEFAULT '',FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE INDEX IF NOT EXISTS idx_tx_owner ON transactions(user_id,transaction_date);
    CREATE TABLE IF NOT EXISTS settings(user_id INTEGER NOT NULL,kind TEXT NOT NULL,data TEXT NOT NULL,PRIMARY KEY(user_id,kind));
    CREATE TABLE IF NOT EXISTS profiles(user_id INTEGER PRIMARY KEY,data TEXT NOT NULL);''')
def password_hash(password,salt=None):
    salt=salt or secrets.token_bytes(16)
    key=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,260000)
    return base64.b64encode(salt+key).decode()
def verify_password(password,stored):
    try:
        raw=base64.b64decode(stored);return hmac.compare_digest(base64.b64decode(password_hash(password,raw[:16]))[16:],raw[16:])
    except Exception:return False
def token_hash(token):return hashlib.sha256(token.encode()).hexdigest()
def identity(authorization:Optional[str]=Header(None)):
    if not authorization or not authorization.startswith('Bearer '):raise HTTPException(401,'Sign in required')
    token=authorization[7:]
    with db() as c:
        row=c.execute('SELECT user_id FROM sessions WHERE token_hash=? AND expires>?',(token_hash(token),int(time.time()))).fetchone()
    if not row:raise HTTPException(401,'Session expired or invalid')
    return row['user_id']
def owned(user_id,uid):
    if str(user_id)!=str(uid):raise HTTPException(403,'Account access denied')
class AuthIn(BaseModel):
    email:str=Field(min_length=5,max_length=254)
    password:str=Field(min_length=10,max_length=256)
    name:str=Field(default='',max_length=100)
class TxIn(BaseModel):
    user_id:str
    merchant:str=Field(min_length=1,max_length=180)
    amount:float=Field(gt=0,le=100000000)
    transaction_date:date
    category:str=Field(default='Other',max_length=60)
    transaction_type:Literal['expense','income','debit','credit']='expense'
    description:str=Field(default='',max_length=500)
class TxPatch(BaseModel):
    category:str=Field(min_length=1,max_length=60)
class Alerts(BaseModel):
    category:float=Field(ge=0,le=1e9)
    dining:float=Field(ge=0,le=1e9)
    repeat:int=Field(ge=2,le=10000)
class Review(BaseModel):
    month:str=Field(default='',max_length=7)
    income:str|float=''
    spending:str|float=''
    headline:str=Field(default='',max_length=180)
    notes:str=Field(default='',max_length=3000)
class ProfileIn(BaseModel):
    user_id:str|int|None=None
    monthly_income:float=Field(default=0,ge=0)
    monthly_fixed_expenses:float=Field(default=0,ge=0)
    current_savings:float=Field(default=0,ge=0)
    emergency_fund:float=Field(default=0,ge=0)
    financial_goal:str=Field(default='',max_length=200)
    goal_amount:float=Field(default=0,ge=0)
    goal_deadline:str|None=None
@app.get('/')
def root():return {'message':'FinPilot Integrated API is running','version':'2.0.0'}
@app.get('/health')
def health():return {'status':'ok'}
def login_response(uid,email,name):
    token=secrets.token_urlsafe(36)
    with db() as c:c.execute('INSERT INTO sessions VALUES(?,?,?)',(token_hash(token),uid,int(time.time())+86400))
    return {'access_token':token,'token_type':'bearer','user':{'id':uid,'email':email,'name':name}}
@app.post('/api/auth/signup',status_code=201)
def signup(body:AuthIn):
    email=body.email.strip().lower()
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email):raise HTTPException(422,'Invalid email')
    if not any(x.isdigit() for x in body.password) or not any(x.isalpha() for x in body.password):raise HTTPException(422,'Password must include letters and numbers')
    with db() as c:
        if c.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone():raise HTTPException(409,'Account already exists')
        cur=c.execute('INSERT INTO users(email,name,password_hash,created_at) VALUES(?,?,?,?)',(email,body.name,password_hash(body.password),int(time.time())))
        uid=cur.lastrowid
    return login_response(uid,email,body.name)
@app.post('/api/auth/login')
def login(body:AuthIn):
    with db() as c: row=c.execute('SELECT * FROM users WHERE email=?',(body.email.strip().lower(),)).fetchone()
    if not row or not verify_password(body.password,row['password_hash']):raise HTTPException(401,'Invalid credentials')
    return login_response(row['id'],row['email'],row['name'])
@app.get('/api/auth/me')
def me(uid:int=Depends(identity)):
    with db() as c:r=c.execute('SELECT id,email,name FROM users WHERE id=?',(uid,)).fetchone()
    return {'user':dict(r)}
@app.post('/api/auth/logout')
def logout(authorization:str|None=Header(None),uid:int=Depends(identity)):
    with db() as c:c.execute('DELETE FROM sessions WHERE token_hash=?',(token_hash(authorization[7:]),))
    return {'ok':True}
@app.get('/api/transactions/')
def tx_list(user_id:str,uid:int=Depends(identity)):
    owned(user_id,uid)
    with db() as c:rows=c.execute('SELECT id,merchant,amount,transaction_date,category,transaction_type,description FROM transactions WHERE user_id=? ORDER BY transaction_date DESC,id DESC',(uid,)).fetchall()
    return [dict(r) for r in rows]
@app.post('/api/transactions/',status_code=201)
def tx_create(body:TxIn,uid:int=Depends(identity)):
    owned(body.user_id,uid)
    with db() as c:
        cur=c.execute('INSERT INTO transactions(user_id,merchant,amount,transaction_date,category,transaction_type,description) VALUES(?,?,?,?,?,?,?)',(uid,body.merchant.strip(),body.amount,body.transaction_date.isoformat(),body.category,'income' if body.transaction_type in ('income','credit') else 'expense',body.description))
        return {'id':cur.lastrowid,'saved':True}
@app.patch('/api/transactions/{txid}')
def tx_update(txid:int,body:TxPatch,uid:int=Depends(identity)):
    with db() as c:
        cur=c.execute('UPDATE transactions SET category=? WHERE id=? AND user_id=?',(body.category,txid,uid))
        if not cur.rowcount:raise HTTPException(404,'Transaction not found')
    return {'ok':True}
@app.delete('/api/transactions/{txid}')
def tx_delete(txid:int,uid:int=Depends(identity)):
    with db() as c:
        cur=c.execute('DELETE FROM transactions WHERE id=? AND user_id=?',(txid,uid))
        if not cur.rowcount:raise HTTPException(404,'Transaction not found')
    return {'ok':True}
@app.get('/api/profile/{user_id}')
def get_profile(user_id:str,uid:int=Depends(identity)):
    owned(user_id,uid)
    with db() as c:r=c.execute('SELECT data FROM profiles WHERE user_id=?',(uid,)).fetchone()
    return json.loads(r['data']) if r else {'monthly_income':0,'monthly_fixed_expenses':0,'current_savings':0,'emergency_fund':0,'financial_goal':'','goal_amount':0,'notes':''}
@app.put('/api/profile/{user_id}')
def put_profile(user_id:str,body:ProfileIn,uid:int=Depends(identity)):
    owned(user_id,uid)
    if body.user_id is not None:owned(body.user_id,uid)
    with db() as c:c.execute('INSERT INTO profiles(user_id,data) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET data=excluded.data',(uid,body.model_dump_json()))
    return {'ok':True}
def get_setting(uid,kind):
    with db() as c:r=c.execute('SELECT data FROM settings WHERE user_id=? AND kind=?',(uid,kind)).fetchone()
    return json.loads(r['data']) if r else (dict(category=20000,dining=5000,repeat=2) if kind=='alerts' else {})
def set_setting(uid,kind,data):
    with db() as c:c.execute('INSERT INTO settings(user_id,kind,data) VALUES(?,?,?) ON CONFLICT(user_id,kind) DO UPDATE SET data=excluded.data',(uid,kind,json.dumps(data)))
    return data
@app.get('/api/settings/alerts')
def get_alerts(uid:int=Depends(identity)):return get_setting(uid,'alerts')
@app.put('/api/settings/alerts')
def put_alerts(body:Alerts,uid:int=Depends(identity)):return set_setting(uid,'alerts',body.model_dump())
@app.get('/api/settings/review')
def get_review(uid:int=Depends(identity)):return get_setting(uid,'review')
@app.put('/api/settings/review')
def put_review(body:Review,uid:int=Depends(identity)):return set_setting(uid,'review',body.model_dump())
@app.post('/api/transactions/upload')
def upload(user_id:str,file:UploadFile=File(...),uid:int=Depends(identity)):
    owned(user_id,uid)
    raise HTTPException(501,'CSV import requires a validated parser; disabled rather than accepting unsafe uploads')
