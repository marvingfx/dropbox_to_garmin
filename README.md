# Wahoo dropbox to garmin connect
This is a very simple implementation to get your Wahoo .fit files from Dropbox and upload them to Garmin Connect.

## Prerequisites
* You have set up the "upload to Dropbox" option for your Wahoo account.

## Usage
1. create a Dropbox app from the instructions from https://www.dropbox.com/developers/apps/create. Choose the regular Dropbox API. Choose "Full Dropbox" for the access type.
1. Clone the repo
2. Create a file called `credentials.env` in the root of the project with the following information. You can get the token via the app console (use the "Generated access token" functionality). You may also use your key and secret to make an authentication script to get the token.
~~~
#DROPBOX_APP_KEY=key <- not used for now
#DROPBOX_APP_SECRET=secret <- not used for now
DROPBOX_APP_TOKEN=token
GARMIN_USERNAME=username
GARMIN_PASSWORD=password
~~~
3. Run `docker-compose up`

## TODO
* The authentication with dropbox is still limited. For now, you will have to generate your own token. In the future there should be a way to pass through your authorization code to generate a token. Saving this token might be handy as well.
* Keep track of files that are not already downloaded from dropbox/uploaded to garmin connect.
* Add more flexibility in terms of folders to download to/from.
* Improve logging.