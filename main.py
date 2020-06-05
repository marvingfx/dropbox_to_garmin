import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect
from garminexport import garminclient
import os

DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET")
DROPBOX_APP_TOKEN = os.environ.get("DROPBOX_APP_TOKEN")
GARMIN_USERNAME = os.environ.get("GARMIN_USERNAME")
GARMIN_PASSWORD = os.environ.get("GARMIN_PASSWORD")


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

    # TODO this part is not working as of now (interactive input in docker containers is hard xD)
    # if client is None and (key or secret):
    #     auth_flow = DropboxOAuth2FlowNoRedirect(DROPBOX_APP_KEY, DROPBOX_APP_SECRET)
    #     auth_url = auth_flow.start()
    #     print(f"go to {auth_url}")
    #     auth_code = input("Enter the authorization code here: ").strip()
    #
    #     try:
    #         oauth_result = auth_flow.finish(auth_code)
    #         access_token = oauth_result.access_token
    #         expires_at = oauth_result.expires_at
    #         refresh_token = oauth_result.refresh_token
    #         client = dropbox.Dropbox(oauth2_access_token=access_token,
    #                                          oauth2_refresh_token=refresh_token,
    #                                          oauth2_access_token_expiration=expires_at)
    #     except Exception as e:
    #         print(f"Could not authenticate {e}")
    #         client = None

    if client is None:
        raise Exception("Could not authenticate. Did you supply the correct credentials")

    return client


if __name__ == "__main__":
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
