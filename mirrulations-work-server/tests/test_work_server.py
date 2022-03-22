from json import dumps
from fakeredis import FakeRedis, FakeServer
from pytest import fixture
from mirrserver.work_server import create_server
from mirrmock.mock_flask_server import mock_work_server


@fixture(name='mock_server')
def fixture_mock_server():
    return mock_work_server(create_server)


def test_create_server_not_connected():
    redis_server = FakeServer()
    mock_db = FakeRedis(server=redis_server)
    redis_server.connected = False
    assert create_server(mock_db) is None


def test_create_mock_database(mock_server):
    assert mock_server.redis is not None


def test_create_mock_server(mock_server):
    assert mock_server.app is not None


def test_new_mock_database_is_empty(mock_server):
    assert mock_server.redis.keys() == []


def test_data_entry_in_mock_database_is_correct(mock_server):
    mock_server.redis.set('val1', 1)
    assert mock_server.redis.get('val1').decode() == '1'


def test_data_entry_changes_in_mock_database(mock_server):
    mock_server.redis.set('val1', 1)
    mock_server.redis.set('val1', 2)
    assert mock_server.redis.get('val1').decode() != '1'
    assert mock_server.redis.get('val1').decode() == '2'


def test_data_deleted_from_mock_database_is_gone(mock_server):
    mock_server.redis.set('val1', 1)
    assert mock_server.redis.get('val1').decode() == '1'
    mock_server.redis.delete('val1')
    assert mock_server.redis.get('val1') is None


def test_get_job_without_client_id_is_unauthorized(mock_server):
    response = mock_server.client.get('/get_job')
    assert response.status_code == 401
    expected = {'error': 'Client ID was not provided'}
    assert response.get_json() == expected


def test_get_job_with_invalid_client_id_is_unauthorized(mock_server):
    mock_server.redis.incr('total_num_client_ids')
    params = {'client_id': 2}
    response = mock_server.client.get('/get_job', query_string=params)
    assert response.status_code == 401
    expected = {'error': 'Invalid client ID'}
    assert response.get_json() == expected


def test_get_job_has_no_available_job(mock_server):
    mock_server.redis.incr('total_num_client_ids')
    params = {'client_id': 1}
    response = mock_server.client.get('/get_job', query_string=params)
    assert response.status_code == 403
    expected = {'error': 'There are no jobs available'}
    assert response.get_json() == expected


def test_get_job_returns_single_job(mock_server):
    mock_server.redis.incr('total_num_client_ids')
    params = {'client_id': 1}
    job = {'job_id': 1, 'url': 'url'}
    mock_server.redis.rpush('jobs_waiting_queue', dumps(job))
    response = mock_server.client.get('/get_job', query_string=params)
    assert response.status_code == 200
    expected = {'job': {'1': 'url'}}
    assert response.get_json() == expected


def test_get_waiting_job_is_now_in_progress_and_not_waiting(mock_server):
    mock_server.redis.incr('total_num_client_ids')
    params = {'client_id': 1}
    job = {'job_id': 3, 'url': 'url'}
    mock_server.redis.rpush('jobs_waiting_queue', dumps(job))
    mock_server.client.get('/get_job', query_string=params)
    assert mock_server.redis.llen('jobs_waiting_queue') == 0
    keys = mock_server.redis.hkeys('jobs_in_progress')
    assert mock_server.redis.hget('jobs_in_progress',
                                  keys[0]).decode() == 'url'


def test_put_results_message_body_contains_no_results(mock_server):
    response = mock_server.client.put('/put_results', json=dumps({}))
    assert response.status_code == 403
    assert response.json['error'] == 'The body does not contain the results'


def test_put_results_with_zero_jobs_in_progress(mock_server):
    mock_server.redis.incr('total_num_client_ids')
    mock_server.redis.hset('jobs_in_progress', 2, '')
    data = dumps({'results': {'': ''}})
    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert mock_server.redis.hget('jobs_in_progress', 2).decode() == ''
    assert response.status_code == 403


def test_put_results_returns_directory_error(mock_server):
    mock_server.redis.incr('total_num_client_ids')
    data = dumps({'results': {'': ''}, 'directory': None})
    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 403
    expected = {'error': 'No directory was included or was incorrect'}
    assert response.get_json() == expected


def test_put_results_without_client_id(mock_server):
    data = dumps({'results': {'': ''}, 'directory': None})
    response = mock_server.client.put('/put_results', json=data)
    assert response.status_code == 401
    assert response.get_json() == {'error': 'Client ID was not provided'}


def test_put_results_with_non_numerical_client_id(mock_server):
    data = dumps({'results': {'': ''}, 'directory': None})
    params = {'client_id': 'a'}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 401
    assert response.get_json() == {'error': 'Invalid client ID'}


def test_client_attempts_to_put_job_that_it_did_not_get(mock_server):
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    mock_server.redis.hset('client_jobs', 2, 2)
    mock_server.redis.set('total_num_client_ids', 2)
    data = dumps({'job_id': 2, 'directory': 'dir/dir',
                  'results': {2: 3}})
    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 403
    expected = {'error': 'The client ID was incorrect'}
    assert response.get_json() == expected


def test_client_attempts_to_put_job_that_does_not_exist(mock_server):
    mock_server.redis.set('total_num_client_ids', 1)
    data = dumps({'job_id': 2, 'directory': 'dir/dir',
                  'results': {2: 3}})
    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 403
    expected = {'error': 'The job being completed was not in progress'}
    assert response.get_json() == expected


def test_put_resuts_no_database(mock_server, mocker):

    mock_write_results(mocker)
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    mock_server.redis.hset('client_jobs', 2, 1)
    mock_server.redis.set('total_num_client_ids', 1)

    data = dumps({'job_id': 2, 'results': {"errors": [{
        "status": "500",
        "title": "INTERNAL_SERVER_ERROR",
        "detail": "Cannot connect to the database"}]}})

    params = {'client_id': 1}
    mock_server.redis_server.connected = False
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 500
    # Not sure this is the best way to do this...
    expected = {'error': 'Cannot connect to the database'}
    assert response.get_json() == expected


def test_put_results_returns_correct_job(mock_server, mocker):

    mock_write_results(mocker)
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    mock_server.redis.hset('client_jobs', 2, 1)
    mock_server.redis.set('total_num_client_ids', 1)
    data = dumps({'job_id': 2, 'directory': 'dir/dir',
                  'results': {'data': {
                      'type': 'dockets'
                  }}})
    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 200
    expected = {'success': 'The job was successfully completed'}
    assert response.get_json() == expected
    assert len(mock_server.data.added) == 1


def test_put_results_returns_correct_attachment_job(mock_server, mocker):

    mock_write_results(mocker)
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    mock_server.redis.hset('client_jobs', 2, 1)
    mock_server.redis.set('total_num_client_ids', 1)
    data = dumps({'job_id': 2, 'directory': 'dir/dir',
                  'results': {'data': {
                      'attachments_text': ['foo'],
                      'type': 'dockets'
                  }}})
    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 200
    expected = {'success': 'The job was successfully completed'}
    assert response.get_json() == expected
    assert len(mock_server.data.added) == 1


def test_put_results_returns_500_error_from_regulations(mock_server, mocker):

    mock_write_results(mocker)
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    mock_server.redis.hset('client_jobs', 2, 1)
    mock_server.redis.set('total_num_client_ids', 1)

    data = dumps({'job_id': 2, 'results': {"errors": [{
        "status": "500",
        "title": "INTERNAL_SERVER_ERROR",
        "detail": "Incorrect result size: expected 1, actual 2"}]}})

    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 200
    # Not sure this is the best way to do this...
    expected = {'success': 'The job was successfully completed'}
    assert response.get_json() == expected

    assert mock_server.redis.hlen('invalid_jobs') == 1
    assert mock_server.redis.hlen('jobs_done') == 0
    assert mock_server.redis.hlen('jobs_in_progress') == 0


def test_put_results_returns_404_error_from_regulations(mock_server, mocker):

    mock_write_results(mocker)
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    mock_server.redis.hset('client_jobs', 2, 1)
    mock_server.redis.set('total_num_client_ids', 1)

    data = dumps({'job_id': 2, 'results': {"errors": [{
        "status": "404",
        "title": "The document ID could not be found."}]}})

    params = {'client_id': 1}
    response = mock_server.client.put('/put_results',
                                      json=data, query_string=params)
    assert response.status_code == 200
    # Not sure this is the best way to do this...
    expected = {'success': 'The job was successfully completed'}
    assert response.get_json() == expected

    assert mock_server.redis.hlen('invalid_jobs') == 1
    assert mock_server.redis.hlen('jobs_done') == 0
    assert mock_server.redis.hlen('jobs_in_progress') == 0


def test_server_handles_client_error_to_access_api_endpoint(mock_server):
    mock_server.redis.set('total_num_client_ids', 1)
    mock_server.redis.hset('jobs_in_progress', 2, 3)
    data = dumps({'job_id': 2, 'directory': -1,
                  'results': {'error': 'Endpoint not found'}})
    params = {'client_id': 1}
    mock_server.client.put('/put_results', json=data, query_string=params)
    invalid_jobs = mock_server.redis.hkeys('invalid_jobs')
    assert len(invalid_jobs) == 1


def test_total_num_client_ids_is_increased_on_get_client_id_call(mock_server):
    previous_number_of_ids = mock_server.redis.get('total_num_client_ids')
    assert previous_number_of_ids is None
    mock_server.client.get('/get_client_id')
    assert int(mock_server.redis.get('total_num_client_ids')) == 1


def test_get_client_id_sends_correct_id(mock_server):
    mock_server.redis.set('total_num_client_ids', 1)
    assert int(mock_server.redis.get('total_num_client_ids')) == 1
    response = mock_server.client.get('/get_client_id')
    assert response.json['client_id'] == 2


def test_database_returns_error_when_database_does_not_exist(mock_server):
    params = {'client_id': 1}
    mock_server.redis_server.connected = False
    response = mock_server.client.get('/get_job', query_string=params)
    assert response.json['error'] == 'Cannot connect to the database'
    assert response.status_code == 500


def test_get_client_id_returns_tuple_when_no_success(mock_server):
    mock_server.redis_server.connected = False
    response = mock_server.client.get('/get_client_id')
    assert response.json['error'] == 'Cannot connect to the database'
    assert response.status_code == 500


def mock_write_results(mocker):
    mocker.patch(
        'mirrserver.work_server.write_results',
        return_value=None
    )
