"""Flask runner for the project."""
import os
import json
import flask
import openai
import traceback
import requests
import ai
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
import pdb
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

RATE_LIMITS = ['40000 per day', '4000 per hour', '100 per minute', '10 per second']
ALL_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']

load_dotenv()
app = flask.Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=RATE_LIMITS,
    storage_uri='memory://',
)

if not os.path.isfile('stats.json'):
    with open('stats.json', 'w') as f:
        json.dump({}, f)

def get_examples():
    """Returns the content of the example files for the API usage."""

    examples = []
    for name in os.listdir('gpt/examples/'):
        if not name.startswith('.'):
            with open(os.path.join('gpt/examples', name)) as f:
                examples.append({
                    'extension': name.split('.')[-1],
                    'name': name.split('.')[0],
                    'code': f.read(),
                })
    
    return examples

def get_stats():
    """Returns the stats for the API usage."""
    with open('stats.json', 'r') as stats_file:
        stats = json.loads(stats_file.read())

    stats = {
        'total': stats['*'],
        'chat': stats['chat/completions'] + stats['engines/gpt-3.5-turbo/chat/completions'],
        'text': stats['engines/text-davinci-003/completions'],
        'image': stats['images/generations'],
        'audio': stats['audio/transcriptions'],
    }
    return stats

# SEO, etc.

@app.route('/robots.txt')
def robots():
    return flask.Response('User-agent: *\nAllow: /\nSitemap: https://api.hypere.app/sitemap.xml', mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    return flask.Response(open('gpt/static/sitemap.xml', 'r').read(), mimetype="text/xml")

@app.route('/favicon.ico')
def favicon():
    return flask.Response('', mimetype='image/x-icon')

# ====

@app.route('/')
def index():
    return flask.render_template('index.html', examples=get_examples(), rate_limits=RATE_LIMITS, stats=get_stats(), title='Home')

import requests
import os

@app.route('/<path:subpath>', methods=ALL_METHODS)
def api_proxy(subpath):
    """Proxy API requests to OpenAI."""
    with open('req.log', 'a') as req_log:
        req_log.write(f'{flask.request.data} {flask.request.get_json()}\n')
    pdb.set_trace()
    params = flask.request.args.copy()
    method = flask.request.method
    content = flask.request.data
    json_data = flask.request.get_json(silent=True)
    is_stream = json_data.get('stream', False) if json_data else False

    try:
        if is_stream:
            return flask.Response(
                ai.proxy_api(
                    method=method,
                    content=content,
                    path=subpath,
                    json_data=json_data,
                    params=params,
                    is_stream=True
                ),
                mimetype='text/event-stream',
            )
        else:
            # If file is attached, send it along with the request
            file = flask.request.files.get('file')
            if file:
                # Save file to disk temporarily
                file_path = os.path.join('/tmp', file.filename)
                file.save(file_path)

                # Create multipart/form-data payload
                payload = {
                    'model': (None, flask.request.form.get('model')),
                    'file': (file.filename, open(file_path, 'rb'), 'application/octet-stream')
                }

                # Send request with payload
                prox_resp = ai.proxy_api(
                    method=method,
                    content=payload,
                    path=subpath,
                    json_data=json_data,
                    params=params,
                    files=payload,
                    is_stream=False,
                )

                # Delete temporary file
                os.remove(file_path)

                # Return response from API
                return prox_resp
            else:
                prox_resp = ai.proxy_api(
                    method=method,
                    content=content,
                    path=subpath,
                    json_data=json_data,
                    params=params,
                    is_stream=False
                )
                return prox_resp

    except Exception as e:
        with open('error.log', 'a') as error_log:
            full_error_traceback = f'{e} {traceback.format_exc()}'

            error_log.write(f'{full_error_traceback}\n')

        return flask.Response(
            {
            'error': 'Sorry, an error occurred. Please contact us: https://discord.gg/SCymptZmUK'
            },
            status=500,
            mimetype='application/json'
        )

@app.route('/donate')
def donate_view():
    return flask.render_template('donate.html', title='Donate')

@app.route('/playground/images')
def playground_view():
    return flask.render_template('playground-images.html', title='Playground')

@app.route('/playground/api/image')
@limiter.limit('5 per minute')
@limiter.limit('1 per second')
def playground_api():
    prompt = flask.request.args.get('prompt')

    if not prompt:
        return flask.Response(status=400)

    openai.api_key = ''
    openai.api_base = "https://api.hypere.app"

    img = openai.Image.create(
        prompt=prompt,
        n=1,
        size='512x512',
    )

    return img.data[0].url

app.run(port=7711, debug=True)