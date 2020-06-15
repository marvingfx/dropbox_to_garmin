import flask
from flask import Response
from flask import request
from hashlib import sha256
from garminexport import garminclient
import dropbox
import hmac
import os

DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET")
DROPBOX_APP_TOKEN = os.environ.get("DROPBOX_APP_TOKEN")
GARMIN_USERNAME = os.environ.get("GARMIN_USERNAME")
GARMIN_PASSWORD = os.environ.get("GARMIN_PASSWORD")
PORT = os.environ.get('PORT', 8080)

app = flask.Flask(__name__)


@app.route('/dropbox')
def handle_dropbox_request():
    challenge_header = request.args.get('challenge')
    if challenge_header is not None:
        response = Response(request.args.get('challenge'))
        response.headers['Content-Type'] = 'text/plain'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    signature_header = request.headers.get('X-Dropbox-Signature')
    if signature_header is None or not hmac.compare_digest(signature_header, hmac.new(str.encode(DROPBOX_APP_SECRET), request.data, sha256).hexdigest()):
        return flask.abort(403)

    sync_dropbox_to_garmin()
    return Response('successfully connected to garmin and dropbox and synced files')


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(PORT))


def filter_files(metadata: dropbox.dropbox.files.Metadata) -> bool:
    # TODO add multiple filter criteria (such as has been downloaded already)
    return isinstance(metadata, dropbox.dropbox.files.FileMetadata)


def get_dropbox_client(token: str = None, key: str = None, secret: str = None) -> dropbox.Dropbox:
    client = None

    if token:
        try:
            client = dropbox.Dropbox(oauth2_access_token=token)
        except Exception as e:
            print(f"Could not use token to authenticate: {e}")
            client = None

    if client is None:
        raise Exception("Could not authenticate. Did you supply the correct credentials")

    return client


def sync_dropbox_to_garmin():
    dropbox_client = get_dropbox_client(token=DROPBOX_APP_TOKEN, key=DROPBOX_APP_KEY, secret=DROPBOX_APP_SECRET)
    all_files_in_folder = dropbox_client.files_list_folder(path="/Apps/WahooFitness").entries
    files_to_download = list(filter(filter_files, all_files_in_folder))

    if len(files_to_download):
        try:
            os.mkdir("data")
        except OSError:
            print("Error in creating folder")

        garmin_connect_client = garminclient.GarminClient(username=GARMIN_USERNAME, password=GARMIN_PASSWORD)
        garmin_connect_client.connect()

        for file in files_to_download:
            dropbox_client.files_download_to_file(download_path=f"./data/{file.name}", path=file.path_lower)
            try:
                activity = garmin_connect_client.upload_activity(file=f"./data/{file.name}")
                print(activity)
            except Exception as e:
                print(f"Could not upload activity: {e}")

        garmin_connect_client.disconnect()
