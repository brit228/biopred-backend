from flask import request, Flask
from flask_cors import CORS, cross_origin
from flask_graphql import GraphQLView

import datetime

from .schemas import predictSchema, db

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.add_url_rule('/graph', view_func=GraphQLView.as_view('graphql', schema=predictSchema, graphiql=True))

@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    header['Access-Control-Allow-Headers'] = '*'
    return response

@app.route('/complete', methods=['POST'])
def completeRegistration():
    uid = request.get_json().get('uid', '')
    typ = request.get_json().get('typ', '')
    if uid != '' and typ != '':
        try:
            print(auth.get_user(uid))
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