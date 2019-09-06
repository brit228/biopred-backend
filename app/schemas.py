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

class PredictionResult(graphene.ObjectType):
    sequence1 = graphene.String()
    sequence2 = graphene.String()
    type1 = graphene.String()
    type2 = graphene.String()
    predSubSeqItem1 = graphene.Boolean()
    predSubSeqItem2 = graphene.Boolean()
    predSubSeqItem3 = graphene.Boolean()
    results = graphene.List(graphene.List(graphene.Float))
    timestamp = graphene.DateTime()

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
    get_prediction_results = graphene.Field(graphene.List(PredictionResult), inputs=graphene.Argument(graphene.Int))
    get_my_prediction_results = graphene.Field(graphene.List(PredictionResult), inputs=graphene.Argument(graphene.Int))

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

    def resolve_get_prediction_results(parent, info, inputs):
        docs = db.collection('jobs').where('status', '==', 'complete').order_by(
            'timestamp', direction=firestore.Query.DESCENDING
        ).limit(1000).stream()
        i = 0
        out = []
        for d in docs:
            if i < inputs*20 and i > (inputs-1)*20:
                out.append({
                    "sequence1": d.get('item1').get('sequence'),
                    "sequence2": d.get('item2').get('sequence'),
                    "type1": d.get('item1').get('itemType'),
                    "type2": d.get('item2').get('itemType'),
                    "predSubSeqItem1": d.get('predSubSeqItem1'),
                    "predSubSeqItem2": d.get('predSubSeqItem2'),
                    "predSubSeqItem3": d.get('item2').get('searchType') != 'ALL',
                    "results": [x['value'] for x in d.get('result')],
                    "timestamp": d.get('timestamp')
                })
            elif i >= inputs*20:
                break
            i += 1
        return out

    def resolve_get_my_prediction_results(parent, info, inputs):
        uid = info.context.get_json().get('authentication', {}).get('uid', '')
        atk = info.context.get_json().get('authentication', {}).get('accessToken', '')
        assert uid != '' and atk != ""
        assert uid == auth.verify_id_token(atk)['uid']
        docs = [d for d in db.collection('users').where('uid', '==', uid).stream()]
        assert len(docs) > 0
        docs = db.collection('jobs').where('uid', '==', uid).where('status', '==', 'complete').order_by(
            'timestamp', direction=firestore.Query.DESCENDING
        ).limit(1000).stream()
        i = 0
        out = []
        for d in docs:
            if i < inputs*20 and i > (inputs-1)*20:
                out.append({
                    "sequence1": d.get('item1').get('sequence'),
                    "sequence2": d.get('item2').get('sequence'),
                    "type1": d.get('item1').get('itemType'),
                    "type2": d.get('item2').get('itemType'),
                    "predSubSeqItem1": d.get('predSubSeqItem1'),
                    "predSubSeqItem2": d.get('predSubSeqItem2'),
                    "predSubSeqItem3": d.get('item2').get('searchType') != 'ALL',
                    "results": [x['value'] for x in d.get('result')],
                    "timestamp": d.get('timestamp')
                })
            elif i >= inputs*20:
                break
            i += 1
        return out

predictSchema = graphene.Schema(query=Query, types=[Item, Prediction, PredictionList, PredictionResult])
