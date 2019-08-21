import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import google.auth
from google.cloud import pubsub

from enum import Enum

cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
  'projectId': 'biopred',
})
db = firestore.client()

publisher = pubsub.PublisherClient()
topic_path = publisher.topic_path('biopred', 'jobs')

itemType = {
    "PROTEIN": 0,
    "DNA": 1,
    "RNA": 2,
    "NA": 3,
    "LIGAND": 4
}

searchType = {
    "TERM": 5,
    "IDCHAIN": 6,
    "SEQUENCE": 7
}

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
    return [doc.to_dict()['chain'] for doc in db.collection('protein').limit(1).stream()]
