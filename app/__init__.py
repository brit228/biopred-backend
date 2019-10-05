from flask import request, Flask
from flask_cors import CORS, cross_origin
from flask_graphql import GraphQLView

from firebase_admin import auth

import datetime

from .schemas import predictSchema, db

app = Flask(__name__)
cors = CORS(app)
app.add_url_rule('/graph', view_func=GraphQLView.as_view('graphql', schema=predictSchema, graphiql=True))
        