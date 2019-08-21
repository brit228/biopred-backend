from flask import request, Flask
from flask_cors import CORS, cross_origin
from flask_graphql import GraphQLView

from .schemas import predictSchema

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.add_url_rule('/graph', view_func=GraphQLView.as_view('graphql', schema=predictSchema, graphiql=True))

@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response
