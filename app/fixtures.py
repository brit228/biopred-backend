import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import google.auth
from google.cloud import pubsub

import requests

cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
  'projectId': 'biopred',
})
db = firestore.client()

publisher = pubsub.PublisherClient()
topic_path = publisher.topic_path('biopred', 'jobs')

def postPredictionJobs(items):
    output = []
    for item in items:
        doc_ref = db.collection('jobs').document()
        doc_ref.set(item)
        doc_ref.update({
            "status": "pending",
            "timestamp": 
        })
        publisher.publish(topic_path, doc_ref.path.encode('utf-8'))
        output.append(doc_ref.path)
    return output

def getItemSearch(items):
    output = []
    for item in items:
        if item['searchType']  == 5:
            xml = "<orgPdbQuery><queryType>org.pdb.query.simple.AdvancedKeywordQuery</queryType><description>Text Search for: {}</description><keywords>{}</keywords></orgPdbQuery>".format(
                item['searchTerm'],
                item['searchTerm']
            )
            r = requests.post(
                "https://www.rcsb.org/pdb/rest/search",
                headers={
                    'Content-Type': 'application/xml'
                },
                data=xml
            )
            
        elif item['searchType']  == 6:
            output.append(item)
        elif item['searchType']  == 7:
            output.append(item)
    return output
