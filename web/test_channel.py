"""Channel receives only the selected account's local conversation projection."""
import unittest
import tempfile
from .db import Database
from types import SimpleNamespace
from unittest.mock import Mock, patch

from flask import Flask

from .channel_bridge import register_channel


class ChannelBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.db = Database(self.tmp.name)
        self.accounts = Mock()
        self.accounts.get.return_value = {'id': 'local-a', 'uid': 'platform-a'}
        self.conversation = Mock()
        self.conversation.list.return_value = {'items': [{
            'message_id': 'incoming-1', 'text': '合成测试消息', 'direction': 'incoming',
            'cookie': 'must-not-forward', 'raw': {'authorization': 'must-not-forward'},
        }]}
        self.channel = Mock()
        self.channel.bind.return_value = {'route':{'id':'own-route','agent_id':'new-agent','version':1},'agent':{'name':'新 Agent'}}
        self.channel.catalog.return_value = {'agents':[{'id':'new-agent','name':'新 Agent'}],'routes':[]}
        self.channel.send.return_value = {'event_id': 'event-1', 'state': 'queued'}
        self.channel.status.return_value = {'state': 'succeeded'}
        client_patch = patch('web.channel_bridge.ChannelClient', return_value=self.channel)
        client_patch.start()
        self.addCleanup(client_patch.stop)
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_error_handler(ValueError, lambda error: ({'error': str(error)}, 400))
        register_channel(app, SimpleNamespace(accounts=self.accounts, conversation=self.conversation, db=self.db))
        self.client = app.test_client()
        self.payload = {'account_id': 'local-a', 'uid': 'peer-a', 'message_id': 'unique-message-1','agent_id':'new-agent'}

    def test_submission_uses_account_identity_and_whitelisted_local_context(self):
        response = self.client.post('/api/channel/messages', json=self.payload)
        self.assertEqual(response.status_code, 202)
        self.accounts.get.assert_called_once_with('local-a')
        self.conversation.list.assert_called_once_with('peer-a', {'account_id': 'local-a', 'limit': 20})
        args, kwargs = self.channel.send.call_args
        self.assertEqual(args[:2], ('platform-a', 'unique-message-1'))
        self.assertEqual(kwargs['route_id'], 'own-route')
        self.channel.bind.assert_called_once_with('platform-a','dm','new-agent')
        self.assertEqual(kwargs['category'], 'reply_draft')
        self.assertEqual(kwargs['conversation_id'], 'peer-a')
        self.assertEqual(kwargs['surface'], 'dm')
        self.assertEqual(kwargs['event_type'], 'dm.draft_requested')
        self.assertEqual(kwargs['context']['messages'][0]['text'], '合成测试消息')
        self.assertNotIn('cookie', kwargs['context']['messages'][0])
        self.assertNotIn('raw', kwargs['context']['messages'][0])

    def test_unknown_account_never_reaches_channel(self):
        self.accounts.get.side_effect = ValueError('账号不存在')
        response = self.client.post('/api/channel/messages', json=self.payload)
        self.assertEqual(response.status_code, 400)
        self.conversation.list.assert_not_called()
        self.channel.send.assert_not_called()

    def test_result_lookup_is_bound_to_selected_account(self):
        response = self.client.get('/api/channel/messages/event-1?account_id=local-a')
        self.assertEqual(response.status_code, 200)
        self.channel.status.assert_called_once_with('event-1', 'platform-a')

    def test_unbound_account_uses_local_identity_and_missing_message_id_is_rejected(self):
        self.accounts.get.return_value = {'id': 'local-a', 'uid': None}
        self.client.post('/api/channel/messages', json=self.payload)
        self.assertEqual(self.channel.send.call_args.args[0], 'local-a')
        self.channel.send.reset_mock()
        self.payload.pop('message_id')
        self.assertEqual(self.client.post('/api/channel/messages', json=self.payload).status_code, 400)
        self.channel.send.assert_not_called()


    def test_live_directory_and_immutable_history(self):
        self.assertEqual(self.client.get('/api/channel/catalog?account_id=local-a').json['agents'][0]['name'],'新 Agent')
        self.channel.catalog.return_value['agents'][0]['name']='改名 Agent'
        self.assertEqual(self.client.get('/api/channel/catalog?account_id=local-a').json['agents'][0]['name'],'改名 Agent')
        self.client.post('/api/channel/messages',json=self.payload)
        self.channel.bind.return_value['agent']['name']='后续改名'
        self.client.post('/api/channel/messages',json=self.payload)
        self.assertEqual(self.client.get('/api/channel/messages/event-1?account_id=local-a').json['agent_snapshot']['agent_name'],'新 Agent')
        self.accounts.get.return_value={'id':'local-b','uid':'platform-b'}
        self.assertEqual(self.client.get('/api/channel/history?account_id=local-b').json['items'],[])
        self.channel.catalog.side_effect=ValueError('不可用')
        self.assertEqual(self.client.get('/api/channel/catalog?account_id=local-b').status_code,400)

    def test_missing_agent_does_not_submit(self):
        self.payload.pop('agent_id')
        self.assertEqual(self.client.post('/api/channel/messages',json=self.payload).status_code,400)
        self.channel.send.assert_not_called()


if __name__ == '__main__':
    unittest.main()
