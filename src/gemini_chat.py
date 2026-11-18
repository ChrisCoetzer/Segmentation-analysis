"""Agent Platform / Vertex express-mode text client using server-side API keys."""
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_MODEL = 'gemini-3.8-flash'


class ChatError(Exception):
    """A message that is safe to display to the visitor."""


def reply(api_key, messages, model=DEFAULT_MODEL, *, system_instruction=None, tools=None, tool_handler=None):
    if not re.fullmatch(r'[a-zA-Z0-9._-]+', model):
        raise ChatError('The configured Gemini model name is invalid.')
    payload = {
        'contents': [
            {'role': 'model' if m['role'] == 'assistant' else 'user',
             'parts': [{'text': m['content']}]} for m in messages
        ],
        'systemInstruction': {'parts': [{'text': system_instruction or
            'You are a helpful, concise assistant beside the Campaign Runway demo. '
            'This is a basic chat connection. You cannot see the page, access its data, '
            'change parameters, or run a guided tour yet. Be clear about those limits '
            'when relevant; do not invent campaign results.'}]},
    }
    if tools:
        payload['tools'] = tools
    for _ in range(5):
        result = _generate(api_key, model, payload)
        candidates = result.get('candidates') or []
        content = candidates[0].get('content', {}) if candidates else {}
        parts = content.get('parts', [])
        calls = [p['functionCall'] for p in parts if p.get('functionCall')]
        if calls:
            if not tool_handler or len(calls) > 8:
                raise ChatError('The requested site actions could not be processed. Try one change at a time.')
            responses = []
            for call in calls:
                response = tool_handler(call.get('name'), call.get('args', {}))
                responses.append({'functionResponse': {'name': call.get('name'), 'response': response}})
            # Preserve all model parts, including thought signatures, exactly.
            payload['contents'].extend([content, {'role': 'user', 'parts': responses}])
            continue
        answer = '\n'.join(p['text'] for p in parts if p.get('text') and not p.get('thought')).strip()
        if not answer:
            raise ChatError('Gemini did not return a text reply. Try rephrasing your message.')
        return answer
    raise ChatError('The analyst reached its action limit. Please try a simpler request.')


def _generate(api_key, model, payload):
    request = Request(
        f'https://aiplatform.googleapis.com/v1/publishers/google/models/{model}:generateContent',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'x-goog-api-key': api_key},
        method='POST',
    )
    try:
        with urlopen(request, timeout=60) as response:
            result = json.load(response)
    except HTTPError as exc:
        # Do not display provider error bodies: they can contain request details.
        try:
            error = json.load(exc).get('error', {})
            reasons = {d.get('reason') for d in error.get('details', []) if isinstance(d, dict)}
        except (ValueError, AttributeError, OSError):
            reasons = set()
        if exc.code == 403 and 'IAM_PERMISSION_DENIED' in reasons:
            raise ChatError(
                'Google denied model access (IAM_PERMISSION_DENIED). Ask the project '
                'administrator to check the identity associated with this API key '
                'and its aiplatform.endpoints.predict permission.'
            ) from None
        explanations = {
            400: 'Gemini rejected the request. Check the API key and model configuration.',
            401: 'Gemini could not authenticate. Check the server API key.',
            403: 'Gemini access was denied. Check the API key permissions and project access.',
            404: 'The configured Gemini model is unavailable for this project.',
            429: 'Gemini is at its usage limit. Please try again shortly or check project quota.',
        }
        raise ChatError(explanations.get(exc.code, 'Gemini is unavailable. Please try again shortly.')) from None
    except (URLError, TimeoutError, OSError):
        raise ChatError('Could not reach Gemini. Please try again shortly.') from None
    except (ValueError, UnicodeError):
        raise ChatError('Gemini returned an unreadable reply. Please try again.') from None
    return result
