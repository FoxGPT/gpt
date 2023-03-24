import os
import uuid
import httpx
import flask
import openai
import random

from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()
app = flask.Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

ALL_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']

def get_key():
    with open('/top-secret/gpt/api.key', encoding='utf8') as keys_file:
        keys = keys_file.read().splitlines()

    key = random.choice(keys)
    key = f'sk-{key.replace(",", "T3BlbkFJ")}'
    return key

@app.route('/')
def index():
    examples = []

    for name in os.listdir('gpt/examples/'):
        if not name.startswith('.'):
            with open(os.path.join('gpt/examples', name)) as f:
                examples.append({
                    'extension': name.split('.')[-1],
                    'name': name.split('.')[0],
                    'code': f.read(),
                })

    return flask.render_template('index.html', examples=examples)

@app.route('/robots.txt')
def robots():
    return flask.Response('User-agent: *\nDisallow: /', mimetype='text/plain')

def default_user():
    return str(uuid.uuid4())

@app.route('/<path:subpath>', methods=ALL_METHODS)
def api_proxy(subpath):
    params = flask.request.args.copy()
    params.pop('request-method', None)

    resp = httpx.request(
        method=flask.request.args.get('request-method', flask.request.method),
        url=f'https://api.openai.com/v1/{subpath.replace("v1/", "")}',
        headers={
            'Authorization': f'Bearer {get_key()}',
            'Content-Type': 'application/json'
        },
        data=flask.request.data,
        json=flask.request.get_json(silent=True),
        params=params,
        timeout=30,
    )

    return resp.json()

app.run(port=7711, debug=True)
