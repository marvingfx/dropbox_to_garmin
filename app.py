import flask
from flask import Response, redirect, request, session, url_for, render_template
from hashlib import sha256
from garminexport import garminclient
import threading
import dropbox
import hmac
import os
import logging
import json
import urllib.parse
import base64
from db.database import Database

DROPBOX_APP_KEY = os.environ.get('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.environ.get('DROPBOX_APP_SECRET')
DROPBOX_APP_TOKEN = os.environ.get('DROPBOX_APP_TOKEN')
GARMIN_USERNAME = os.environ.get('GARMIN_USERNAME')
GARMIN_PASSWORD = os.environ.get('GARMIN_PASSWORD')
FIREBASE_SERVICE_ACCOUNT = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
FLASK_SECRET = os.environ['FLASK_SECRET']
PORT = os.environ.get('PORT', 8080)

app = flask.Flask(__name__)
app.secret_key = FLASK_SECRET
db = Database(json.loads(base64.decodebytes(str.encode(FIREBASE_SERVICE_ACCOUNT))))

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter(fmt='%(asctime)-19s.%(msecs)03d | %(levelname)s | %(name)s: %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def filter_files(metadata: dropbox.dropbox.files.Metadata) -> bool:
    return isinstance(metadata, dropbox.dropbox.files.FileMetadata) and metadata.path_lower.endswith('.fit')


def get_url(route):
    host = urllib.parse.urlparse(request.url).hostname
    url = url_for(
        route,
        _external=True,
        _scheme='http' if host in ['127.0.0.1', 'localhost', '0.0.0.0'] else 'https'
    )

    return url


def sync_dropbox_to_garmin(user_id: str):
    token = db.get_field(user_id, 'token')
    dropbox_client = dropbox.Dropbox(oauth2_access_token=token)
    files_to_download = []
    has_more = True

    while has_more:
        try:
            cursor: str = db.get_field(user_id, 'cursor')
        except Exception as e:
            logger.info('Could not find cursor')
            cursor: str = ''

        if cursor:
            result = dropbox_client.files_list_folder_continue(cursor)
        else:
            result = dropbox_client.files_list_folder(path='/Apps/WahooFitness')

        files_to_download = files_to_download + list(filter(filter_files, result.entries))

        cursor = result.cursor
        db.update_user(user_id=user_id, cursor=cursor)

        has_more = result.has_more

    logger.info(f'Found {len(files_to_download)} to sync')

    if len(files_to_download):
        try:
            os.mkdir('data')
        except OSError:
            logger.info('Error in creating folder')

        garmin_connect_client = garminclient.GarminClient(username=GARMIN_USERNAME, password=GARMIN_PASSWORD)
        garmin_connect_client.connect()

        for file in files_to_download:
            logging.info(f'Downloading {file.name}')
            dropbox_client.files_download_to_file(download_path=f'./data/{file.name}', path=file.path_lower)
            try:
                activity = garmin_connect_client.upload_activity(file=f'./data/{file.name}')
                logger.info(f'Successfully uploaded {activity}')
            except Exception as e:
                logger.info(f'Could not upload activity: {e}')

        garmin_connect_client.disconnect()


@app.route('/oauth_callback')
def oauth_callback():
    auth_result = get_dropbox_auth_flow().finish(request.args)
    user_id = auth_result.account_id
    access_token = auth_result.access_token
    db.add_user(user_id, token=access_token)

    return redirect(url_for('done'))


def get_dropbox_auth_flow():
    return dropbox.DropboxOAuth2Flow(
        consumer_key=DROPBOX_APP_KEY,
        consumer_secret=DROPBOX_APP_SECRET,
        redirect_uri=get_url('oauth_callback'),
        session=session,
        csrf_token_session_key='dropbox-csrf-token'
    )


@app.route('/login')
def login():
    return redirect(get_dropbox_auth_flow().start())


@app.route('/done')
def done():
    return render_template('done.html')


@app.route('/dropbox', methods=['get'])
def challenge():
    logger.info('Recorded challenge, returning challenge header')
    response = Response(request.args.get('challenge'))
    response.headers['Content-Type'] = 'text/plain'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.route('/dropbox', methods=['POST'])
def handle_dropbox_request():
    signature_header = request.headers.get('X-Dropbox-Signature')
    if signature_header is None or not hmac.compare_digest(signature_header,
                                                           hmac.new(str.encode(DROPBOX_APP_SECRET),
                                                                    request.data,
                                                                    sha256).hexdigest()
                                                           ):
        logger.info('Invalid request, aborting')
        return flask.abort(403)

    for user_id in json.loads(request.data)['list_folder']['accounts']:
        threading.Thread(target=sync_dropbox_to_garmin, args=[user_id]).start()

    return Response('Syncing files')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(PORT))
