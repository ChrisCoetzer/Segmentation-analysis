import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from src.gemini_chat import ChatError, reply


class GeminiChatTests(unittest.TestCase):
    def test_history_roles_and_header_only_credential(self):
        response = io.BytesIO(json.dumps({'candidates': [{'content': {'parts': [
            {'thought': True, 'text': 'private reasoning'}, {'text': 'Hello there'}
        ]}}]}).encode())
        with patch('src.gemini_chat.urlopen', return_value=response) as send:
            answer = reply('test-secret', [
                {'role': 'user', 'content': 'Hi'},
                {'role': 'assistant', 'content': 'Hello'},
                {'role': 'user', 'content': 'Again'},
            ])
        request = send.call_args.args[0]
        self.assertEqual(request.full_url, 'https://aiplatform.googleapis.com/v1/publishers/google/models/gemini-3.8-flash:generateContent')
        payload = json.loads(request.data)
        self.assertEqual(answer, 'Hello there')
        self.assertEqual([m['role'] for m in payload['contents']], ['user', 'model', 'user'])
        self.assertNotIn('test-secret', request.full_url)
        self.assertNotIn('test-secret', request.data.decode())
        self.assertEqual(request.get_header('X-goog-api-key'), 'test-secret')

    def test_errors_do_not_expose_provider_details(self):
        error = HTTPError('https://example.invalid', 429, 'test-secret', {}, io.BytesIO(b'test-secret'))
        with patch('src.gemini_chat.urlopen', side_effect=error):
            with self.assertRaises(ChatError) as caught:
                reply('test-secret', [{'role': 'user', 'content': 'Hi'}])
        self.assertIn('usage limit', str(caught.exception))
        self.assertNotIn('test-secret', str(caught.exception))

    def test_no_text_and_network_failure(self):
        for response in ({'promptFeedback': {'blockReason': 'SAFETY'}}, {'candidates': []}):
            with patch('src.gemini_chat.urlopen', return_value=io.BytesIO(json.dumps(response).encode())):
                with self.assertRaises(ChatError):
                    reply('test-secret', [{'role': 'user', 'content': 'Hi'}])
        with patch('src.gemini_chat.urlopen', side_effect=URLError('test-secret')):
            with self.assertRaisesRegex(ChatError, 'Could not reach'):
                reply('test-secret', [{'role': 'user', 'content': 'Hi'}])

    def test_permission_error_explains_required_access_without_raw_details(self):
        body = {'error': {'message': 'test-secret private account details',
                          'details': [{'reason': 'IAM_PERMISSION_DENIED'}]}}
        error = HTTPError('https://example.invalid', 403, 'Forbidden', {},
                          io.BytesIO(json.dumps(body).encode()))
        with patch('src.gemini_chat.urlopen', side_effect=error):
            with self.assertRaises(ChatError) as caught:
                reply('test-secret', [{'role': 'user', 'content': 'Hi'}])
        self.assertIn('aiplatform.endpoints.predict', str(caught.exception))
        self.assertNotIn('test-secret', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
