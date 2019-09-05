import graphene

import firebase_admin
from firebase_admin import auth
from firebase_admin import credentials
from firebase_admin import firestore

import google.auth
from google.cloud import pubsub

import requests

import datetime
import os

cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
  'projectId': 'biopred',
})
db = firestore.client()

publisher = pubsub.PublisherClient()
topic_path = publisher.topic_path('biopred', 'jobs')


class Item(graphene.InputObjectType):
    sequence = graphene.String()
    searchType = graphene.String(required=True)
    itemType = graphene.String(required=True)

class Prediction(graphene.InputObjectType):
    item1 = graphene.Field(Item, required=True)
    item2 = graphene.Field(Item, required=True)
    predSubSeqItem1 = graphene.Boolean(required=True)
    predSubSeqItem2 = graphene.Boolean(required=True)

class PredictionList(graphene.InputObjectType):
    predictions = graphene.List(Prediction)

class Query(graphene.ObjectType):
    post_prediction_jobs = graphene.Field(graphene.List(graphene.String), inputs=graphene.Argument(PredictionList, required=True))

    def resolve_post_prediction_jobs(parent, info, inputs):
        uid = info.context.get_json().get('authentication', {}).get('uid', '')
        atk = info.context.get_json().get('authentication', {}).get('accessToken', '')
        assert uid != '' and atk != ""
        assert uid == auth.verify_id_token(atk)['uid']
        docs = [d for d in db.collection('users').where('uid', '==', uid).stream()]
        assert len(docs) > 0
        assert docs[0].get('limit') > len(inputs['predictions'])
        docs[0].reference.update({"limit": docs[0].get('limit')-len(inputs['predictions'])})
        output = []
        for item in inputs['predictions']:
            doc_ref = db.collection('jobs').document()
            doc_ref.set(item)
            doc_ref.update({
                "status": "processing",
                "uid": uid,
                "timestamp": datetime.datetime.now()
            })
            publisher.publish(topic_path, doc_ref.path.encode('utf-8'))
            output.append(doc_ref.path)
        return output

predictSchema = graphene.Schema(query=Query, types=[Item, Prediction, PredictionList])
