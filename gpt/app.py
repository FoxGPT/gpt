"""Flask runner for the project."""
import os
import json
import flask
import openai
import traceback
import requests
import ai
from flask import jsonify
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_ipban import IpBan


RATE_LIMITS = ['30000 per day', '2000 per hour', '60 per minute', '5 per second']
ALL_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']

load_dotenv()
app = flask.Flask(__name__)
ip_ban = IpBan(persist=True, record_dir='ipban')
ip_ban.init_app(app)
CORS(app)
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
        'chat': stats['chat/completions'] + stats['engines/gpt-3.5-turbo/chat/completions'] + stats['engines/gpt-3.5-turbo/completions'],
        'text': stats['engines/text-davinci-003/completions'],
        'image': stats['images/generations'],
        'audio': stats['audio/transcriptions'],
        'other' : stats['*'] - stats['chat/completions'] - stats['engines/gpt-3.5-turbo/chat/completions'] - stats['engines/text-davinci-003/completions'] - stats['images/generations'] - stats['audio/transcriptions'] - stats['engines/gpt-3.5-turbo/completions']
    }
    return stats

def get_tokens():
    """Returns the tokens for the API usage."""
    with open('tokens.json', 'r') as tokens_file:
        tokens = json.loads(tokens_file.read())
    tokens = {
        'total': tokens['text'] + tokens['chat']+ tokens['gpt4'],
        'chat': tokens['chat']+ tokens['gpt4'],
        'text': tokens['text']
    }
    return tokens
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


@app.route('/block/<path:ip>')
def block_it(ip):
    if (flask.request.headers.get('Authorization') == os.getenv('BLOCK_AUTH')):
        url_params = flask.request.args
        # Retrieve parameters using get() 
        perm = True if url_params.get('perm') == 'true' else False
        if perm:

            ip_ban.block([ip], permanent=True)
            return 'ok'
        else:
            ip_ban.block([ip])
            return 'ok'
    else:
        return flask.Response('Unauthorized: You are not admin.', 401)


@app.route('/unblock/<path:ip>')
def un_block_it(ip):
    ''' Remove an IP from the blacklist '''
    if (flask.request.headers.get('Authorization') == os.getenv('BLOCK_AUTH')):
        ip_ban.remove(ip)
        return 'ok'
    else:
        return flask.Response('Unauthorized: You are not admin.', 401)

@app.route('/whitelist/<string:ip>', methods=['PUT', 'DELETE'])
def whitelist_ip(ip):
    ''' Add or remove an IP from the whitelist '''
    if (flask.request.headers.get('Authorization') == os.getenv('BLOCK_AUTH')):
        result = 'error: unknown method'
        if flask.request.method == 'PUT':
            result = 'Added.  {} entries in the whitelist'.format(ip_ban.ip_whitelist_add(ip))
        elif flask.request.method == 'DELETE':
            result = '{} removed'.format(ip) if ip_ban.ip_whitelist_remove(ip) else '{} not in whitelist'.format(ip)
        return result
    else:
        return flask.Response('Unauthorized: You are not admin.', 401)

@app.route('/listblocked')
def listblocked():
    ''' List all blocked IPs '''
    if (flask.request.headers.get('Authorization') == os.getenv('BLOCK_AUTH')):
        blocklist = ip_ban.get_block_list()
        if len(blocklist) == 0:
            return 'No blocked IPs'
        else:
            return blocklist
    else:
        return flask.Response('Unauthorized: You are not admin.', 401)


@app.route('/', methods=ALL_METHODS)
def index():
    return flask.render_template('index.html', examples=get_examples(), rate_limits=RATE_LIMITS, stats=get_stats(), tokens=get_tokens(), title='Home')

import requests
import os
USERKEYS_FILE = os.getenv('USERKEYS_FILE')
STATS_AUTH = os.getenv('STATS_AUTH')

def check_token(key):
    with open(USERKEYS_FILE, 'r') as f:
        data = json.load(f)
    for user_id, values in data.items():
        if values['key'] == key:
            return user_id
    
    return False

def check_gpt4(key):
    with open(USERKEYS_FILE, 'r') as f:
        data = json.load(f)
    for user_id, values in data.items():
        if values['key'] == key:
            return user_id if values['gpt4'] else False
    return False

@app.route('/stats', methods=['GET'])

def stats():
    if flask.request.headers.get('Authorization') == STATS_AUTH:
        tokens = json.load(open('tokens.json'))
        stats = json.load(open('stats.json'))
        total = (
            stats['images/generations'] * 0.02 +
            tokens['gpt4']//1000 * 0.06 +
            tokens['chat']//1000 * 0.002 +
            tokens['text']//1000 * 0.02 +
            stats['audio/transcriptions'] * 0.006 +
            ((stats['*'] - stats['chat/completions'] - stats['engines/gpt-3.5-turbo/chat/completions'] - stats['engines/text-davinci-003/completions'] - stats['images/generations'] - stats['audio/transcriptions'] - stats['engines/gpt-3.5-turbo/completions']) // 1000 * 0.0004)
        )
        response_data = {
            "totalcost": total,
            "totalrequests": stats['*']
        }
        return jsonify(response_data)
    else:
        return 'unauthorized', 401

@app.route('/<path:subpath>', methods=['OPTIONS'])
def handle_options(subpath):
    response = flask.make_response()
    response.headers.set('Access-Control-Allow-Origin', '*')
    response.headers.set('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    response.headers.set('Access-Control-Allow-Headers', 'Authorization, Content-Type')
    return response


@app.route('/<path:subpath>', methods=ALL_METHODS)
def api_proxy(subpath):
    """Proxy API requests to OpenAI."""
    if not 'audio' in subpath:
        # log requests. before logging, check if the size of req.log is higher than 100mb. if so, delete it.
        if os.path.getsize('req.log') > 100000000:
            os.remove('req.log')
            # create a new file
            with open('req.log', 'w') as req_log:
                req_log.write(f'{flask.request.data} {flask.request.get_json()}\n')  
        else:        
            with open('req.log', 'a') as req_log:
                req_log.write(f'{flask.request.data} {flask.request.get_json()}\n')

    params = flask.request.args.copy()
    method = flask.request.method
    content = flask.request.data
    json_data = flask.request.get_json(silent=True)
    is_stream = json_data.get('stream', False) if json_data else False
    ip_address = flask.request.headers.get('CF-Connecting-IP', flask.request.remote_addr)

    try:
        file = flask.request.files.get('file')
        auth_header = flask.request.headers.get('Authorization')
        # auth_token is the text in auth_header that starts with fg- so we need to remove the "Bearer " part if it exists (of course, unless auth_header is None)
        if auth_header is None:
            auth_token = None
        elif auth_header.startswith('Bearer '):
            auth_token = auth_header[7:]
            print("s")
        else:
            auth_token = auth_header
            print("else")
        print(auth_token)
        # if auth_token is not just Bearer, log it to keys.log (if the file doesn't exist, create it)(if the token is already in the file, don't log it)
        if auth_token:
            if not os.path.exists('keys.log'):
                with open('keys.log', 'w') as keys_log:
                    keys_log.write(f'{auth_token}\n')
            else:
                with open('keys.log', 'r') as keys_log:
                    if auth_token not in keys_log.read():
                        with open('keys.log', 'a') as keys_log:
                            keys_log.write(f'{auth_token}\n')
        if not auth_token:
            return flask.Response('{"error": {"code": "unauthorized", "message": "You need an API key to use FoxGPT. You can get one in our discord server: https://discord.gg/ftSSNcPQgM"}}', 403)
        if not check_token(auth_token):
            return flask.Response('{"error": {"code": "unauthorized", "message": "Invalid API key. Check your API key and try again. If you don\'t have one, you can get a key in our discord server: https://discord.gg/ftSSNcPQgM"}}', 403)
        if not file:
            contentjson = json.loads(content)
            if 'model' in contentjson:
                if ('gpt-4' in subpath or 'gpt-4' in contentjson['model']) and check_gpt4(auth_token) == False:
                    return flask.Response('{"error": {"code": "unauthorized_gpt_4", "message": "You are not allowed to use GPT-4."}}', 403)
        # count requests for each auth token in requests.json
        with open('tokens.json', 'r') as f:
            tokens = json.load(f)
        if auth_token in tokens:
            tokens[auth_token] += 1
        else:
            tokens[auth_token] = 1
        with open('tokens.json', 'w') as f:
            json.dump(tokens, f)
        if is_stream:
            status_code, lines = ai.proxy_api(
                    method=method,
                    content=content,
                    path=subpath,
                    json_data=json_data,
                    params=params,
                    is_stream=True,
                    auth=auth_token,
                    ip=ip_address
                )
            return flask.Response(
                lines,
                status_code,
                mimetype='text/event-stream'
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
                    is_stream=False,
                    auth=auth_token,
                    ip=ip_address
                )
                return prox_resp

    except Exception as e:
        with open('error.log', 'a') as error_log:
            full_error_traceback = f'{e} {traceback.format_exc()}'

            error_log.write(f'{full_error_traceback}\n')

        return flask.Response(
            {
            'error': 'Sorry, an error occurred. Please contact us: https://discord.gg/E8E2TnE75D'
            },
            status=500,
            mimetype='application/json'
        )
@app.after_request
def apply_caching(response):
    response.headers["X-Accel-Buffering"] = "no"
    return response
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
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7711, debug=True)