import graphene

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import google.auth
from google.cloud import pubsub

import requests

import datetime


cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
  'projectId': 'biopred',
})
db = firestore.client()

publisher = pubsub.PublisherClient()
topic_path = publisher.topic_path('biopred', 'jobs')


class Item(graphene.InputObjectType):
    sequence = graphene.String()
    term = graphene.String()
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
    # get_item_search = graphene.Field(Item)

    def resolve_post_prediction_jobs(parent, info, inputs):
        output = []
        for item in parent:
            doc_ref = db.collection('jobs').document()
            doc_ref.set(item)
            doc_ref.update({
                "status": "pending",
                "timestamp": datetime.datetime.now()
            })
            publisher.publish(topic_path, doc_ref.path.encode('utf-8'))
            output.append(doc_ref.path)
        return output

    # def resolve_get_item_search(parent, info):
    #     xml = "<orgPdbQuery><queryType>org.pdb.query.simple.AdvancedKeywordQuery</queryType><description>Text Search for: {}</description><keywords>{}</keywords></orgPdbQuery>".format(
    #         item['searchTerm'],
    #         item['searchTerm']
    #     )
    #     r = requests.post(
    #         "https://www.rcsb.org/pdb/rest/search",
    #         headers={
    #             'Content-Type': 'application/xml'
    #         },
    #         data=xml
    #     )

predictSchema = graphene.Schema(query=Query, types=[Item, Prediction, PredictionList])
