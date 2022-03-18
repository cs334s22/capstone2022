"""
This module creates the dashboard application that queries
    the redis and mongo databases to return stats about
    the number of jobs in progress/complete and the status
    of the containers.

Dependencies:
    docker, dotenv, flask, flask_cors, os, pymongo, redis
"""
import os
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from redis import Redis
from mirrdash.sum_mongo_counts import connect_mongo_db, get_done_counts
from dotenv import load_dotenv
import docker


class Dashboard:
    def __init__(self, redis_server, docker_server, mongo_client):
        self.app = Flask(__name__)
        self.redis = redis_server
        self.docker = docker_server
        self.mongo = mongo_client
        CORS(self.app, resources={r'/data': {'origins': '*'}})


def get_jobs_stats(database):
    jobs_waiting = int(database.llen('jobs_waiting_queue'))
    jobs_in_progress = int(database.hlen('jobs_in_progress'))
    jobs_total_minus_jobs_done = jobs_waiting + jobs_in_progress

    client_ids = database.get('total_num_client_ids')
    clients_total = int(client_ids) if client_ids is not None else 0

    return {
        'num_jobs_waiting': jobs_waiting,
        'num_jobs_in_progress': jobs_in_progress,
        'jobs_total': jobs_total_minus_jobs_done,
        'clients_total': clients_total
    }


def get_container_stats(client):
    stats = {}
    for container in client.containers.list():
        name = get_container_name(container.name)
        status = container.status
        stats[name] = status
    return stats


def get_container_name(container_name):
    """
    Docker container names may be created with hyphens,
    so we replace them with underscores.
    """
    name = container_name.replace('-', '_')
    long_name_lst = name.split('_')
    long_name_lst.pop(0)
    long_name_lst.pop(-1)
    return '_'.join(long_name_lst)


def create_server(database, docker_server, mongo_client):
    dashboard = Dashboard(database, docker_server, mongo_client)

    @dashboard.app.route('/', methods=['GET'])
    def _index():
        return render_template(
            'index.html'
        )

    @dashboard.app.route('/data', methods=['GET'])
    def _get_dashboard_data():
        """ returns data as json and request status code """
        # Get the jobs stats in the redis db
        data = get_jobs_stats(dashboard.redis)

        # Get the number of jobs done from the mongo db
        # and add it to the data
        # TO DO: 'attachments_count' is hardwired. Needs to have it
        # added in from plumbing.
        jobs_done_info = get_done_counts(dashboard.mongo, 'mirrulations')
        data.update(jobs_done_info)

        # Add this value to the total jobs
        # TO DO: This should go away entirely when Redis is
        # removed from this process
        # TO DO: When this happens, change the variable name
        # in get_done_counts to simplify
        data['jobs_total'] += jobs_done_info['num_jobs_done']

        # Add container info to data
        container_information = get_container_stats(dashboard.docker)
        data.update(container_information)

        return jsonify(data), 200

    return dashboard


if __name__ == '__main__':
    load_dotenv()
    mongo_host = os.getenv('MONGO_HOSTNAME')
    server = create_server(Redis(os.getenv('REDIS_HOSTNAME')),
                           docker.from_env(),
                           connect_mongo_db(mongo_host, 27017))
    server.app.run(port=5000)
