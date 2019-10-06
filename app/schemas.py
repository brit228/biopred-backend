import graphene

import firebase_admin
from firebase_admin import auth
from firebase_admin import credentials
from firebase_admin import firestore

import google.auth

import datetime
import os

cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
  'projectId': 'biopred',
})
db = firestore.client()

class RNAProteinMonomer(graphene.ObjectType):
    resabbrev = graphene.String()
    interaction = graphene.Float()

class RNAProteinPredictionResult(graphene.ObjectType):
    sequence = graphene.String()
    result = graphene.List(RNAProteinMonomer)
    jobname = graphene.String()
    timestamp = graphene.DateTime()
    status = graphene.String()

class RNAProteinPredictionInput(graphene.InputObjectType):
    sequence = graphene.String(required=True)
    jobname = graphene.String(required=True)

class Query(graphene.ObjectType):
    check_in = graphene.Field(graphene.Int)
    complete_registration = graphene.Field(graphene.Boolean, typ=graphene.String(required=True))
    delete_me = graphene.Field(graphene.Boolean)
    my_rna_protein_predictions = graphene.Field(graphene.List(RNAProteinPredictionResult))
    all_rna_protein_predictions = graphene.Field(graphene.List(RNAProteinPredictionResult))
    make_rna_protein_prediction = graphene.Field(graphene.Boolean, inp=graphene.Argument(RNAProteinPredictionInput, required=True))

    def resolve_check_in(parent, info):
        uid = info.context.get_json().get('authentication', {}).get('uid', '')
        atk = info.context.get_json().get('authentication', {}).get('accessToken', '')
        assert uid != '' and atk != ""
        assert uid == auth.verify_id_token(atk)['uid']
        docs = [d for d in db.collection('users').where('uid', '==', uid).stream()]
        assert len(docs) > 0
        doc = docs[0]
        return doc.get('limit')

    def resolve_complete_registration(parent, info, typ):
        uid = info.context.get_json().get('authentication', {}).get('uid', '')
        atk = info.context.get_json().get('authentication', {}).get('accessToken', '')
        assert uid != '' and typ != ''
        try:
            auth.get_user(uid)
        except ValueError:
            assert False
        except auth.AuthError:
            assert False
        docs = db.collection('users').where('uid', '==', uid).stream()
        assert len([d for d in docs]) == 0
        db.collection('users').add({
            'uid': uid,
            'type': typ,
            'limit': 1000,
            'created': datetime.datetime.now(),
            'lastIncrease': datetime.datetime.now(),
            'total': 1000
        })
        return True

    def resolve_delete_me(parent, info):
        uid = info.context.get_json().get('authentication', {}).get('uid', '')
        atk = info.context.get_json().get('authentication', {}).get('accessToken', '')
        assert uid != '' and atk != ""
        assert uid == auth.verify_id_token(atk)['uid']
        docs = [d for d in db.collection('users').where('uid', '==', uid).stream()]
        assert len(docs) > 0
        docs[0].reference.delete()
        auth.delete_user(uid)
        return True

    def resolve_my_rna_protein_predictions(parent, info):
        uid = info.context.get_json().get('authentication', {}).get('uid', '')
        atk = info.context.get_json().get('authentication', {}).get('accessToken', '')
        assert uid != '' and atk != ""
        assert uid == auth.verify_id_token(atk)['uid']
        docs = [d for d in db.collection('users').where('uid', '==', uid).stream()]
        assert len(docs) > 0
        return [{
            'sequence': d.get('sequence'),
            'result': d.get('result'),
            'jobname': d.get('jobname'),
            'timestamp': d.get('timestamp'),
            'status': d.get('status')
        } for d in db.collection(
            'jobs/rnaprotein/jobs'
        ).where(
            'user', '==', uid
        ).where(
            'status', '<', 'processing'
        ).order_by(
            'status'
        ).order_by(
            'timestamp', direction=firestore.Query.DESCENDING
        ).limit(
            100
        ).stream()]

    def resolve_all_rna_protein_predictions(parent, info):
        return [{
            'sequence': d.get('sequence'),
            'result': d.get('result'),
            'jobname': d.get('jobname'),
            'timestamp': d.get('timestamp'),
            'status': d.get('status')
        } for d in db.collection(
            'jobs/rnaprotein/jobs'
        ).where(
            'status', '<', 'processing'
        ).order_by(
            'status'
        ).order_by(
            'timestamp', direction=firestore.Query.DESCENDING
        ).limit(
            100
        ).stream()]

    def resolve_make_rna_protein_prediction(parent, info, inp):
        uid = info.context.get_json().get('authentication', {}).get('uid', '')
        atk = info.context.get_json().get('authentication', {}).get('accessToken', '')
        assert uid != '' and atk != ""
        assert uid == auth.verify_id_token(atk)['uid']
        docs = [d for d in db.collection('users').where('uid', '==', uid).stream()]
        assert len(docs) > 0
        assert docs[0].get('limit') > 0
        docs[0].reference.update({'limit': docs[0].get('limit') - 1})
        db.collection('jobs/rnaprotein/jobs').add({
            'user': uid,
            'sequence': inp['sequence'],
            'result': [],
            'jobname': inp['jobname'],
            'timestamp': datetime.datetime.now(),
            'status': 'processing'
        })
        return True
        

predictSchema = graphene.Schema(query=Query, types=[RNAProteinMonomer, RNAProteinPredictionInput, RNAProteinPredictionResult])
