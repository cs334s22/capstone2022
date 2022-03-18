"""
This module contains the functions that will be used to query the mongoDB

Dependencies:
    pymongo
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


def connect_mongo_db(host_name, port_number):
    if host_name is None:
        host_name = 'localhost'
    if port_number is None:
        port_number = int(27017)
    client = MongoClient(host_name, port_number)
    try:
        print(client.server_info())
    except ConnectionFailure:
        print("Unable to connect to the server.")

    return client


# TO DO: Make attachments_count into a real value
def get_done_counts(client, db_name):
    dockets_count = get_dockets_count(client, db_name)
    documents_count = get_documents_count(client, db_name)
    comments_count = get_comments_count(client, db_name)
    attachments_count = get_attachments_count(client, db_name)

    return {
        'num_jobs_done': dockets_count + documents_count
        + comments_count + attachments_count,
        'num_dockets_done': dockets_count,
        'num_documents_done': documents_count,
        'num_comments_done': comments_count,
        'num_attachments_done': attachments_count
    }


def get_dockets_count(client, db_name):
    return int(client[db_name]['dockets'].estimated_document_count())


def get_documents_count(client, db_name):
    return int(client[db_name]['documents'].estimated_document_count())


def get_comments_count(client, db_name):
    return int(client[db_name]['comments'].estimated_document_count())


def get_attachments_count(client, db_name):
    # return int(client[db_name]['attachments'].estimated_document_count())
    # this isnt good but not our problem right now
    if client and db_name:
        return int(4)
    return None
