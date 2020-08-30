import firebase_admin
from firebase_admin import credentials, firestore


class Database(object):
    def __init__(self, credentials_dict):
        cred = credentials.Certificate(credentials_dict)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def add_user(self, user_id: str, token: str):
        document_ref = self.db.collection(u'dropbox_users').document(user_id)
        document_ref.set({
            u'token': token
        })

    def update_user(self, user_id: str, cursor: str):
        document_ref = self.db.collection(u'dropbox_users').document(user_id)
        document_ref.update({
            u'cursor': cursor
        })

    def get_field(self, user_id: str, field: str) -> str:
        document_ref = self.db.collection(u'dropbox_users').document(user_id)
        document = document_ref.get()

        if document.exists:
            document_dict = document.to_dict()

            if field in document_dict:
                return document_dict[field]
            else:
                raise Exception(f'Could not find {field} for user')

        else:
            raise Exception(f'Could not find {field} for user')
