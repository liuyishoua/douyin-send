"""Live Agent directory; local account ownership controls all bindings and history."""
import json
import os
import time
from pathlib import Path
from flask import request
from .channel_client import ChannelClient


def register_channel(app, service):
    config=Path(os.environ.get('CHANNEL_CONFIG_FILE') or Path(__file__).resolve().parents[1]/'.local/web/channel.json')
    with service.db.connect() as db:
        db.executescript("""CREATE TABLE IF NOT EXISTS channel_bindings (
            account_id TEXT, purpose TEXT, data TEXT, PRIMARY KEY(account_id,purpose));
            CREATE TABLE IF NOT EXISTS channel_submissions (
            account_id TEXT, event_id TEXT, data TEXT, PRIMARY KEY(account_id,event_id));""")
    def client(): return ChannelClient(config)
    def scope(aid):
        account=service.accounts.get(str(aid))
        return account, str(account.get('uid') or account['id'])
    def saved(owner):
        with service.db.connect() as db:
            row=db.execute("SELECT data FROM channel_bindings WHERE account_id=? AND purpose='dm'", (owner,)).fetchone()
        return json.loads(row['data']) if row else None
    def remember(owner, result):
        event_id=result.get('id') or result.get('event_id')
        with service.db.connect() as db:
            row=db.execute('SELECT data FROM channel_submissions WHERE account_id=? AND event_id=?', (owner,event_id)).fetchone()
        return json.loads(row['data']) if row else None
    def bind(channel, owner, agent_id):
        if not isinstance(agent_id,str) or not agent_id: raise ValueError('请选择一个 Agent')
        binding=channel.bind(owner, 'dm', agent_id);route=binding['route'];agent=binding.get('agent') or route.get('agent') or {}
        snapshot={'agent_id':route['agent_id'],'agent_name':agent.get('name',''), 'route_id':route['id'],'route_version':route.get('version')}
        with service.db.connect() as db:
            db.execute('INSERT OR REPLACE INTO channel_bindings VALUES(?,?,?)',(owner,'dm',json.dumps(snapshot,ensure_ascii=False)))
        return snapshot
    def catalog():
        account,owner=scope(request.args.get('account_id',''));result=client().catalog();previous=saved(owner)
        if not previous:
            matches=[a for a in result['agents'] if a.get('name')=='抖音-'+account.get('name','')]
            if len(matches)==1:previous={'agent_id':matches[0]['id'],'agent_name':matches[0]['name']}
        return {**result,'account_id':account['id'],'binding':previous}
    def bindings():
        data=request.get_json() or {};_,owner=scope(data.get('account_id',''))
        if data.get('purpose','dm')!='dm':raise ValueError('不支持的用途')
        return bind(client(),owner,data.get('agent_id'))
    def history():
        _,owner=scope(request.args.get('account_id',''))
        with service.db.connect() as db:
            rows=db.execute('SELECT data FROM channel_submissions WHERE account_id=? ORDER BY rowid DESC LIMIT 100',(owner,)).fetchall()
        return {'items':[json.loads(r['data']) for r in rows]}
    def submit():
        data=request.get_json() or {};aid=str(data.get('account_id',''));uid=str(data.get('uid',''))
        account,owner=scope(aid)
        snapshot=service.conversation.list(uid,{'account_id':aid,'limit':20})
        context={'peer_id':uid,'messages':[{k:m.get(k) for k in ('record_id','message_id','text','message','direction','message_type','attempted_at')} for m in snapshot['items']]}
        text=data.get('text','根据最近对话起草简短自然的中文回复。');message_id=data.get('message_id')
        if not isinstance(text,str) or len(text)>4000:raise ValueError('处理要求最多 4000 字')
        if not isinstance(message_id,str) or not 8<=len(message_id)<=160:raise ValueError('请提供唯一消息 ID')
        channel=client();identity=bind(channel,owner,data.get('agent_id') or (saved(owner) or {}).get('agent_id'))
        result=channel.send(owner,message_id,text,category='reply_draft',conversation_id=uid,context=context,surface='dm',event_type='dm.draft_requested',route_id=identity['route_id'])
        event_id=result.get('id') or result.get('event_id')
        if not event_id:raise ValueError('Channel 未返回任务标识')
        value={'id':event_id,'message_id':message_id,'peer_id':uid,'created':time.time(),**identity}
        with service.db.connect() as db:
            db.execute('INSERT OR IGNORE INTO channel_submissions VALUES(?,?,?)',(owner,event_id,json.dumps(value,ensure_ascii=False)))
        return {**result,'agent_snapshot':remember(owner,result)},202
    def status(event_id):
        _,owner=scope(request.args.get('account_id',''))
        return {**client().status(event_id,owner),'agent_snapshot':remember(owner,{'id':event_id})}
    app.add_url_rule('/api/channel/catalog','channel_catalog',catalog)
    app.add_url_rule('/api/channel/bindings','channel_bindings',bindings,methods=['POST'])
    app.add_url_rule('/api/channel/history','channel_history',history)
    app.add_url_rule('/api/channel/messages','channel_submit',submit,methods=['POST'])
    app.add_url_rule('/api/channel/messages/<event_id>','channel_status',status)
