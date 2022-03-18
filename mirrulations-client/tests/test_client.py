import os
from functools import partial
from pytest import fixture, raises
import requests
import requests_mock
import mirrclient.client
from mirrclient.client import Client, NoJobsAvailableException
from mirrclient.client import is_environment_variables_present
# from mirrclient.client import execute_client_task
from mirrclient.client import read_client_id


BASE_URL = 'http://work_server:8080'


@fixture(autouse=True)
def mock_env():
    os.environ['WORK_SERVER_HOSTNAME'] = 'work_server'
    os.environ['WORK_SERVER_PORT'] = '8080'
    os.environ['API_KEY'] = 'TESTING_KEY'


@fixture(name='mock_requests')
def fixture_mock_requests():
    return requests_mock.Mocker()


def test_client_url():
    client = Client()
    assert client.url == BASE_URL


def test_client_gets_existing_client_id(mocker):
    client = Client()
    mock_client_id = 99
    write_mock_client_id(mocker)
    read_mock_client_id(mocker, mock_client_id)
    client.get_client_id()
    assert mock_client_id == client.client_id


def test_client_gets_client_id_from_server(mock_requests, mocker):
    client = Client()
    mock_client_id = 9
    read_mock_client_id(mocker, -1)
    write_mock_client_id(mocker)
    with mock_requests:
        mock_requests.get(
            f'{BASE_URL}/get_client_id',
            json={'client_id': mock_client_id}
        )
        client.get_client_id()
        assert mock_client_id == client.client_id


def test_client_gets_job(mock_requests):
    client = Client()
    with mock_requests:
        mock_requests.get(
            f'{BASE_URL}/get_job',
            json={'job': {'1': 1}},
            status_code=200
        )
        assert ('1', 1) == client.get_job()


def test_client_throws_exception_when_no_jobs(mock_requests):
    client = Client()
    with mock_requests:
        mock_requests.get(
            f'{BASE_URL}/get_job',
            json={'error': 'No jobs available'},
            status_code=403
        )

        with raises(NoJobsAvailableException):
            client.get_job()


def test_client_sleeps_when_no_jobs_available(mock_requests, mocker):
    client = Client()
    read_mock_client_id(mocker, 1)
    mock_assure_request(mocker)
    mock_get_job(mocker)
    with mock_requests:
        mock_requests.get(
            f'{BASE_URL}/get_job',
            json={'error': 'No jobs available'},
            status_code=400
        )
        assert client.get_job() is None


def test_client_sends_job_results(mock_requests, mocker):
    client = Client()
    mock_job_id = '1'
    mock_job_result = {'data': {'id': mock_job_id,
                       'attributes': {'agencyId': 'NOAA'}}}
    mock_client_id = 999
    read_mock_client_id(mocker, mock_client_id)

    with mock_requests:
        mock_requests.get(
            f'{BASE_URL}/get_client_id',
            json={'client_id': 999},
            status_code=200
        )
        mock_requests.put(
            f'{BASE_URL}/put_results',
            json={'success': 'The job was successfully completed'},
            status_code=200
        )
        try:
            client.send_job_results(mock_job_id, mock_job_result)
        except requests.exceptions.HTTPError as exception:
            assert False, f'raised an exception: {exception}'


def test_client_completes_job_requested(mock_requests, mocker):
    mocker.patch('time.sleep')
    client = Client()
    mock_client_id = 9
    read_mock_client_id(mocker, mock_client_id)

    with mock_requests:
        mock_requests.get(
            f'{BASE_URL}/get_client_id',
            json={'client_id': mock_client_id},
            status_code=200
        )
        mock_requests.get(
            f'{BASE_URL}/get_job',
            json={'job': {'1': 'http://test.com'}},
            status_code=200
        )
        mock_requests.put(
            f'{BASE_URL}/put_results',
            json={'success': 'The job was successfully completed'},
            status_code=200
        )
        mock_requests.get(
            'http://test.com',
            json={'data': {'id': '1', 'attributes': {'agencyId': 'NOAA'}}},
            status_code=200
        )

        try:
            # execute_client_task(client)
            client.execute_task()
        except requests.exceptions.HTTPError as exception:
            assert False, f'Raised an exception: {exception}'


def test_attempt_request_raises_connection_exception(mock_requests, mocker):
    # This needs to be reviewed IS THIS A BAD TEST?
    mock_raise_connection_error(mocker)
    with mock_requests:
        mock_requests.get(
            f'{BASE_URL}/get_job',
            status_code=400

        )
        try:
            mirrclient.client.assure_request(requests.get,
                                             f'{BASE_URL}/get_job', 0)
        except requests.exceptions.ConnectionError as exception:
            assert True, f'raised an exception: {exception}'
        # assert response is None


def test_read_client_id_success(tmpdir):
    file = tmpdir.join('test_read.txt')
    file.write('1')
    assert int(file.read()) == read_client_id(str(file))


def test_read_client_id_file_not_found():
    assert read_client_id('nonexistent.txt') == -1


def test_write_client_id(tmpdir):
    file = tmpdir.join('test_write.txt')
    client = Client()
    client.write_client_id(str(file))
    assert file.read() == '-1'


def test_check_all_env_values():
    assert is_environment_variables_present() is True


def test_check_no_env_values():
    # Need to delete env variables set by mock_env fixture
    del os.environ['WORK_SERVER_HOSTNAME']
    del os.environ['WORK_SERVER_PORT']
    del os.environ['API_KEY']
    assert is_environment_variables_present() is False


def test_check_no_hostname():
    # Need to delete hostname env variable set by mock_env fixture
    del os.environ['WORK_SERVER_HOSTNAME']
    assert is_environment_variables_present() is False


def test_check_no_server_port():
    # Need to delete server port env variable set by mock_env fixture
    del os.environ['WORK_SERVER_PORT']
    assert is_environment_variables_present() is False


def test_check_no_api_key():
    # Need to delete api key env variable set by mock_env fixture
    del os.environ['API_KEY']
    assert is_environment_variables_present() is False


def mock_assure_request(mocker):
    mocker.patch(
        'mirrclient.client.Client.get_job',
        side_effect=partial(mirrclient.client.assure_request, sleep_time=0)
    )


def mock_get_job(mocker):
    mocker.patch(
        'mirrclient.client.Client.get_job',
        return_value=None
    )


def mock_raise_connection_error(mocker):
    mocker.patch(
        'requests.get',
        side_effect=requests.exceptions.ConnectionError
    )


def read_mock_client_id(mocker, value):
    mocker.patch(
        'mirrclient.client.read_client_id',
        return_value=value
    )


def write_mock_client_id(mocker):
    mocker.patch(
        'mirrclient.client.Client.write_client_id',
        return_value=''
    )


def test_client_handles_missing_docket_id(mock_requests, mocker):
    client = Client()
    mock_job_id = '1'
    mock_job_result = {'data': {'id': mock_job_id,
                       'attributes': {'agencyId': 'NOAA',
                                      "docketId": None}}}
    mock_client_id = 999
    read_mock_client_id(mocker, mock_client_id)

    with mock_requests:
        mock_requests.get(
            f'{BASE_URL}/get_client_id',
            json={'client_id': 999},
            status_code=200
        )
        mock_requests.put(
            f'{BASE_URL}/put_results',
            json={'success': 'The job was successfully completed'},
            status_code=200
        )
        try:
            client.send_job_results(mock_job_id, mock_job_result)
        except requests.exceptions.HTTPError as exception:
            assert False, f'raised an exception: {exception}'


def test_client_returns_500_error_to_server(mock_requests, mocker):

    mocker.patch('time.sleep')
    client = Client()
    mock_client_id = 9
    read_mock_client_id(mocker, mock_client_id)

    with mock_requests:
        mock_requests.get(
            f'{BASE_URL}/get_client_id',
            json={'client_id': mock_client_id},
            status_code=200
        )
        mock_requests.get(
            f'{BASE_URL}/get_job',
            json={'job': {'1': 'http://test.com'}},
            status_code=200
        )
        mock_requests.put(
            f'{BASE_URL}/put_results',
            json={'success': 'The job was successfully completed'},
            status_code=200
        )

        regulation_response = {"errors": [{
            "status": "500",
            "title": "INTERNAL_SERVER_ERROR",
            "detail": "Incorrect result size: expected 1, actual 2"}]
        }

        mock_requests.get(
            'http://test.com',
            json=regulation_response,
            status_code=500
        )

        try:
            client.execute_task()
        except requests.exceptions.HTTPError as exception:
            assert False, f'Raised an exception: {exception}'

        response = mock_requests.request_history[-1]
        assert 'errors' in response.json()


def test_client_returns_404_error_to_server(mock_requests, mocker):

    mocker.patch('time.sleep')
    client = Client()
    mock_client_id = 9
    read_mock_client_id(mocker, mock_client_id)

    with mock_requests:
        mock_requests.get(
            f'{BASE_URL}/get_client_id',
            json={'client_id': mock_client_id},
            status_code=200
        )
        mock_requests.get(
            f'{BASE_URL}/get_job',
            json={'job': {'1': 'http://test.com'}},
            status_code=200
        )
        mock_requests.put(
            f'{BASE_URL}/put_results',
            json={'success': 'The job was successfully completed'},
            status_code=200
        )

        regulation_response = {"errors": [{
            "status": "404",
            "title": "The document ID could not be found."}]}

        mock_requests.get(
            'http://test.com',
            json=regulation_response,
            status_code=404
        )

        try:
            client.execute_task()
        except requests.exceptions.HTTPError as exception:
            assert False, f'Raised an exception: {exception}'

        response = mock_requests.request_history[-1]
        assert 'errors' in response.json()


def test_client_returns_400_error_to_server(mock_requests, mocker):

    mocker.patch('time.sleep')
    client = Client()
    mock_client_id = 9
    read_mock_client_id(mocker, mock_client_id)

    with mock_requests:
        mock_requests.get(
            f'{BASE_URL}/get_client_id',
            json={'client_id': mock_client_id},
            status_code=200
        )
        mock_requests.get(
            f'{BASE_URL}/get_job',
            json={'job': {'1': 'http://test.com'}},
            status_code=200
        )
        mock_requests.put(
            f'{BASE_URL}/put_results',
            json={'success': 'The job was successfully completed'},
            status_code=200
        )

        regulation_response = {"errors": [{
            "status": "400",
            "title": "The document ID could not be found."}]}

        mock_requests.get(
            'http://test.com',
            json=regulation_response,
            status_code=400
        )

        try:
            client.execute_task()
        except requests.exceptions.HTTPError as exception:
            assert False, f'Raised an exception: {exception}'

        response = mock_requests.request_history[-1]
        assert 'errors' in response.json()


def test_client_returns_403_error_to_server(mock_requests, mocker):

    mocker.patch('time.sleep')
    client = Client()
    mock_client_id = 9
    read_mock_client_id(mocker, mock_client_id)

    with mock_requests:
        mock_requests.get(
            f'{BASE_URL}/get_client_id',
            json={'client_id': mock_client_id},
            status_code=200
        )
        mock_requests.get(
            f'{BASE_URL}/get_job',
            json={'job': {'1': 'http://test.com'}},
            status_code=200
        )
        mock_requests.put(
            f'{BASE_URL}/put_results',
            json={'success': 'The job was successfully completed'},
            status_code=200
        )

        regulation_response = {"errors": [{
            "status": "403",
            "title": "The document ID could not be found."}],
            "error": "API limit reached."
        }

        mock_requests.get(
            'http://test.com',
            json=regulation_response,
            status_code=403
        )

        try:
            client.execute_task()
        except requests.exceptions.HTTPError as exception:
            assert False, f'Raised an exception: {exception}'

        response = mock_requests.request_history[-1]
        assert 'errors' in response.json()


def test_api_call_has_api_key(mock_requests):
    client = Client()
    client.api_key = 'KEY12345'
    with mock_requests:
        mock_requests.get(
            'http://regulations.gov/job',
            json={'data': {'foo': 'bar'}},
            status_code=200
        )

        # client.perform_job('http://regulations.gov/job', 'KEY12345')
        client.perform_job('http://regulations.gov/job')

        assert '?api_key=KEY12345' in mock_requests.request_history[0].url
