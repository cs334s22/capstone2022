from flask import Flask, jsonify, render_template
from flask_cors import CORS
from redis import Redis
import docker


class Dashboard:
    def __init__(self, redis_server, docker_server):
        self.app = Flask(__name__)
        self.redis = redis_server
        self.docker = docker_server
        CORS(self.app, resources={r'/data': {'origins': '*'}})


def get_jobs_stats(database):
    jobs_waiting = int(database.llen('jobs_waiting_queue'))
    jobs_in_progress = int(database.hlen('jobs_in_progress'))
    jobs_done = int(database.hlen('jobs_done'))
    jobs_total = jobs_waiting + jobs_in_progress + jobs_done
    client_ids = database.get('total_num_client_ids')
    clients_total = int(client_ids) if client_ids is not None else 0
    return {
        'num_jobs_waiting': jobs_waiting,
        'num_jobs_in_progress': jobs_in_progress,
        'num_jobs_done': jobs_done,
        'jobs_total': jobs_total,
        'clients_total': clients_total
    }

def get_container_name(container):
    name = container.name.replace('-', '_')
    long_name_lst = name.split('_')
    long_name_lst.pop(0)
    long_name_lst.pop(-1)
    return '_'.join(long_name_lst)


def get_container_stats(client):
    stats = {}
    for container in client.containers.list():
        name = get_container_name(container)
        status = container.status
        stats[name] = status
    return stats


def create_server(database, docker_server):
    dashboard = Dashboard(database, docker_server)

    @dashboard.app.route('/', methods=['GET'])
    def _index():
        return render_template(
            'index.html'
        )

    @dashboard.app.route('/data', methods=['GET'])
    def _get_dashboard_data():
        data = get_jobs_stats(dashboard.redis)
        container_information = get_container_stats(dashboard.docker)
        data.update(container_information)
        return jsonify(data), 200

    return dashboard


if __name__ == '__main__':
    server = create_server(Redis('redis'), docker.from_env())
    server.app.run(port=5000)
