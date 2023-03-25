import os
import flask

import ai

from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()
app = flask.Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

ALL_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']

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

@app.route('/<path:subpath>', methods=ALL_METHODS)
def api_proxy(subpath):
    return ai.respond_to_request(flask.request, subpath)

app.run(port=7711, debug=True)
