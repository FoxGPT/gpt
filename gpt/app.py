"""Flask runner for the project."""
import os
import json
import flask
import openai
import traceback

import ai

from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

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
    with open('stats.json', 'r') as stats_file:
        stats = json.loads(stats_file.read())

    stats = {
        'total': stats['*'],
        'chat': stats['chat/completions'] + stats['engines/gpt-3.5-turbo/chat/completions'],
        'completions': stats['engines/text-davinci-003/completions'],
        'images': stats['images/generations'],
    }
    return stats

@app.route('/')
def index():
    return flask.render_template('index.html', examples=get_examples(), rate_limits=RATE_LIMITS, stats=get_stats())

@app.route('/<path:subpath>', methods=ALL_METHODS)
def api_proxy(subpath):
    with open('req.log', 'a') as req_log:
        req_log.write(f'{flask.request.data} {flask.request.get_json()}\n')

    try:
        return ai.proxy_api(flask.request, subpath)
    except Exception as e:
        with open('error.log', 'a') as error_log:
            full_error_traceback = f'{e} {traceback.format_exc()}'

            error_log.write(f'{full_error_traceback}\n')

        return {
            'error': 'Sorry, an error occurred. Please contact us: https://discord.gg/SCymptZmUK'
        }

@app.route('/robots.txt')
def robots():
    return flask.Response('User-agent: *\nDisallow: /', mimetype='text/plain')

@app.route('/favicon.ico')
def favcion():
    return flask.Response('', mimetype='image/x-icon')

@app.route('/playground/images')
def playground_view():
    return flask.render_template('playground-images.html')

@app.route('/playground/api/image')
@limiter.limit('5 per minute')
@limiter.limit('1 per second')
def playground_api():
    prompt = flask.request.args.get('prompt')

    if not prompt:
        return flask.Response(status=400)

    openai.api_key = ''
    openai.api_base = "https://gpt.bot.nu"

    img = openai.Image.create(
        prompt=prompt,
        n=1,
        size='512x512',
    )

    return img.data[0].url

app.run(port=7711, debug=True)
