import os,tempfile,importlib,sys
from fastapi.testclient import TestClient

def test_security_and_crud(monkeypatch,tmp_path):
 monkeypatch.setenv('FINPILOT_SECRET','x'*48);monkeypatch.setenv('FINPILOT_DB',str(tmp_path/'test.sqlite3'))
 sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parents[1]/'backend'))
 sys.modules.pop('main',None);m=importlib.import_module('main');c=TestClient(m.app)
 assert c.get('/health').status_code==200
 assert c.get('/api/transactions/',params={'user_id':'1'}).status_code==401
 def signup(email):
  r=c.post('/api/auth/signup',json={'email':email,'password':'TestPassword123','name':'Test'});assert r.status_code==201,r.text;return r.json()
 a=signup('one@example.test');b=signup('two@example.test')
 ah={'Authorization':'Bearer '+a['access_token']};bh={'Authorization':'Bearer '+b['access_token']}
 aid=a['user']['id'];bid=b['user']['id']
 assert c.get('/api/transactions/',params={'user_id':bid},headers=ah).status_code==403
 tx={'user_id':str(aid),'merchant':'Demo','amount':120,'transaction_date':'2026-11-20','category':'Dining','transaction_type':'expense'}
 r=c.post('/api/transactions/',json=tx,headers=ah);assert r.status_code==201,r.text;tid=r.json()['id']
 assert c.get('/api/transactions/',params={'user_id':aid},headers=ah).json()[0]['merchant']=='Demo'
 assert c.patch(f'/api/transactions/{tid}',json={'category':'Other'},headers=bh).status_code==404
 assert c.delete(f'/api/transactions/{tid}',headers=bh).status_code==404
 assert c.patch(f'/api/transactions/{tid}',json={'category':'Groceries'},headers=ah).status_code==200
 assert c.post('/api/transactions/',json={**tx,'amount':-1},headers=ah).status_code==422
 assert c.put('/api/settings/alerts',json={'category':5000,'dining':1000,'repeat':3},headers=ah).status_code==200
 assert c.get('/api/settings/alerts',headers=bh).json()['category']!=5000
 assert c.put('/api/settings/review',json={'month':'2026-11','headline':'November','notes':'Test'},headers=ah).status_code==200
 assert c.get('/api/settings/review',headers=ah).json()['headline']=='November'
 assert c.post('/api/auth/logout',json={},headers=ah).status_code==200
 assert c.get('/api/settings/alerts',headers=ah).status_code==401
