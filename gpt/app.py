import os
import json
import flask

import ai

from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()
app = flask.Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

ALL_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']

if not os.path.isfile('stats.json'):
    with open('stats.json', 'w') as f:
        json.dump({}, f)

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

@app.route('/<path:subpath>', methods=ALL_METHODS)
def api_proxy(subpath):
    return ai.respond_to_request(flask.request, subpath)

@app.route('/robots.txt')
def robots():
    return flask.Response('User-agent: *\nDisallow: /', mimetype='text/plain')

@app.route('/favicon.ico')
def favcion():
    return flask.Response('', mimetype='image/x-icon')

@app.route('/stats/<key>')
def get_stat(key):
    key = key.replace('--', '/')
    with open('stats.json', 'r') as stats_file:
        stats = json.loads(stats_file.read())

    value = stats.get(key, 0)
    return {'value': value}

app.run(port=7711, debug=True)
