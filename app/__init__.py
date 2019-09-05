from flask import request, Flask
from flask_cors import CORS, cross_origin
from flask_graphql import GraphQLView

from firebase_admin import auth

import datetime

from .schemas import predictSchema, db

app = Flask(__name__)
cors = CORS(app)
app.add_url_rule('/graph', view_func=GraphQLView.as_view('graphql', schema=predictSchema, graphiql=True))

@app.route('/', methods=['GET'])
def checkInBase():
    uid = request.get_json().get('uid', '')
    if uid != '':
        try:
            auth.get_user(uid)
        except ValueError:
            return '{"error": "invalid uid"}'
        except auth.AuthError:
            return '{"error": "user does not exist"}'
        docs = db.collection('users').where('uid', '==', uid).stream()
        doc = [d for d in docs][0]
        return '{"limit": '+doc.get('limit')+'}'

@app.route('/complete', methods=['POST'])
def completeRegistration():
    uid = request.get_json().get('uid', '')
    typ = request.get_json().get('typ', '')
    if uid != '' and typ != '':
        try:
            auth.get_user(uid)
        except ValueError:
            return "ERROR: invalid uid"
        except auth.AuthError:
            return "ERROR: user does not exist"
        docs = db.collection('users').where('uid', '==', uid).stream()
        if len([d for d in docs]) > 0:
            return "ERROR: user registration already completed"
        db.collection('users').add({
            'uid': uid,
            'type': typ,
            'limit': 1000,
            'created': datetime.datetime.now(),
            'lastIncrease': datetime.datetime.now(),
            'total': 1000
        })
        return "SUCCESS"
    return "ERROR: uid and type not complete"