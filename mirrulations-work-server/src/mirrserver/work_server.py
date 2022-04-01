import os
from flask import Flask, json, jsonify, request
import redis
from mirrcore.data_storage import DataStorage


class WorkServer:
    def __init__(self, redis_server):
        self.app = Flask(__name__)
        self.redis = redis_server
        self.data = DataStorage()


def check_for_database(workserver):
    # This will either succeed or raise an exception
    workserver.redis.ping()


def check_valid_request_client_id(workserver, client_id):
    if client_id is None:
        return False, jsonify({'error': 'Client ID was not provided'}), 401
    if not check_client_id_is_valid(workserver, client_id):
        return False, jsonify({'error': 'Invalid client ID'}), 401
    return (True,)


def get_job(workserver):
    check_for_database(workserver)
    client_id = request.args.get('client_id')
    success, *values = check_valid_request_client_id(workserver, client_id)
    if not success:
        return False, values[0], values[1]
    if workserver.redis.llen('jobs_waiting_queue') == 0:
        return False, jsonify({'error': 'No jobs available'}), 403
    job = json.loads(workserver.redis.lpop('jobs_waiting_queue'))
    job_id = job['job_id']
    url = job['url']
    job_type = job.get('job_type', 'other')
    workserver.redis.hset('jobs_in_progress', job_id, url)
    workserver.redis.hset('client_jobs', job_id, client_id)
    return True, job_id, url, job_type


def check_results(workserver, data, client_id):
    directory = data.get('directory')
    if directory is not None:
        filename_start = directory.rfind('/')
    if directory is None or filename_start == -1:
        error = {'error': 'No directory was included or was incorrect'}
        return False, jsonify(error), 403
    job_id = data.get('job_id', -1)
    expected_client_id = workserver.redis.hget('client_jobs', job_id)
    if (workserver.redis.hget('jobs_in_progress', job_id) is None or
            expected_client_id is None):
        error = {'error': 'The job being completed was not in progress'}
        return False, jsonify(error), 403
    if client_id != int(expected_client_id):
        error = {'error': 'The client ID was incorrect'}
        return False, jsonify(error), 403
    return (True, directory[:filename_start])


def write_results(directory, path, data):
    try:
        os.makedirs(f'/data/{directory}')
    except FileExistsError:
        print(f'Directory already exists in root: /data/{directory}')
    with open(f'/data/{path}', 'w+', encoding='utf8') as file:
        file.write(json.dumps(data))


def put_results(workserver, data):
    check_for_database(workserver)
    client_id = request.args.get('client_id')
    files = request.files.getlist('files')
    success, *values = check_valid_request_client_id(workserver, client_id)
    if not success:
        return False, values[0], values[1]
    if 'error' in data['results'] or 'errors' in data['results']:
        job_id = data['job_id']
        result = workserver.redis.hget('jobs_in_progress', job_id)
        workserver.redis.hdel('jobs_in_progress', job_id)
        workserver.redis.hset('invalid_jobs', job_id, result)
        return (True,)
    success, *results = check_results(workserver, data, int(client_id))
    if not success:
        return (success, *results)
    job_id = data['job_id']
    workserver.redis.hdel('jobs_in_progress', job_id)
    if 'attachments_text' in data['results']['data'].keys():
        print(data['results']['data']['attachments_text'])
        if files:
            for file in files:
                file.save(os.path.join('/capstone2022/attachments', file.filename))
    else:
        write_results(results[0], data['directory'], data['results'])
    workserver.data.add(data['results'])
    return (True,)


def get_client_id(workserver):
    check_for_database(workserver)
    workserver.redis.incr('total_num_client_ids')
    return True, int(workserver.redis.get('total_num_client_ids'))


def check_client_id_is_valid(workserver, client_id):
    check_for_database(workserver)
    num_ids = workserver.redis.get('total_num_client_ids')
    total_ids = 0 if num_ids is None else int(num_ids)
    if not client_id.isdigit():
        return False
    client_id = int(client_id)
    return 0 < client_id <= total_ids


def create_server(database):
    '''Create server, add endpoints, and return the server'''
    workserver = WorkServer(database)

    @workserver.app.route('/get_job', methods=['GET'])
    def _get_job():
        try:
            success, *values = get_job(workserver)
            if not success:
                return tuple(values)
            return jsonify({'job': {str(values[0]): values[1],
                            'job_type': values[2]}}), 200
        except redis.exceptions.ConnectionError:
            body = {'error': 'Cannot connect to the database'}
            return jsonify(body), 500

    @workserver.app.route('/put_results', methods=['PUT'])
    def _put_results():
        try:
            data = json.loads(request.get_json())
            if data is None or data.get('results') is None:
                body = {'error': 'The body does not contain the results'}
                return jsonify(body), 403
            success, *values = put_results(workserver, data)
            if not success:
                return tuple(values)
            return jsonify({'success': 'Job was successfully completed'}), 200
        except redis.exceptions.ConnectionError:
            body = {'error': 'Cannot connect to the database'}
            return jsonify(body), 500

    @workserver.app.route('/get_client_id', methods=['GET'])
    def _get_client_id():
        try:
            success, *values = get_client_id(workserver)
            if not success:
                return tuple(values)
            return jsonify({'client_id': values[0]}), 200
        except redis.exceptions.ConnectionError:
            body = {'error': 'Cannot connect to the database'}
            return jsonify(body), 500

    return workserver


if __name__ == '__main__':
    try:
        r = redis.Redis('redis')
        r.keys('*')
        server = create_server(r)
        server.app.run(host='0.0.0.0', port=8080, debug=False)
    except redis.exceptions.ConnectionError:
        print('There is no Redis database to connect to.')
