# Wahoo dropbox to garmin connect
This is a container that listens to changes in your dropbox folder. It will download the Wahoo fit files and sync them to Garmin Connect.
## Prerequisites
* You have set up the "upload to Dropbox" option for your Wahoo account.

## Usage
* Create a Dropbox app from the instructions from https://www.dropbox.com/developers/apps/create. Choose the regular Dropbox API. Choose "Full Dropbox" for the access type.
* Clone the repo
* Create a file called `credentials.env` in the root of the project with the following information. You can get the token via the app console (use the "Generated access token" functionality). You may also use your key and secret to make an authentication script to get the token. Enter these variables in the appropriate section if running on Google Cloud (Cloud Run).
```
#DROPBOX_APP_KEY=dropbox app key
#DROPBOX_APP_SECRET=dropbox app secret
FIREBASE_SERVICE_ACCOUNT=base64 encoded service account json for now
FLASK_SECRET=random key
GARMIN_USERNAME=garmin connect username
GARMIN_PASSWORD=garmin connect password
```
* Deploy your container (using Google Cloud)
* Register your container in the webhook section of your dropbox application (the container will handle the challenge part)
* Your container will now react on changes in dropbox

## TODO
* Find better way to share service account credentials
* Add more flexibility in terms of folders to download to/from.