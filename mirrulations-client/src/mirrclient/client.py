import time
import os
import sys
from json import dumps, loads, load
from dotenv import load_dotenv
import requests
from requests.exceptions import ConnectionError as RequestConnectionError
from requests.exceptions import HTTPError, RequestException


class NoJobsAvailableException(Exception):
    pass


class Client:

    def __init__(self):
        work_server_hostname = os.getenv('WORK_SERVER_HOSTNAME')
        work_server_port = os.getenv('WORK_SERVER_PORT')
        self.url = f'http://{work_server_hostname}:{work_server_port}'
        self.api_key = os.getenv('API_KEY')
        self.client_id = -1

    def get_client_id(self):
        client_id = read_client_id('client.cfg')
        if client_id == -1:
            client_id = self.request_client_id()
        self.client_id = client_id

    def request_client_id(self):
        endpoint = f'{self.url}/get_client_id'
        response = assure_request(requests.get, endpoint)
        client_id = int(response.json()['client_id'])
        self.write_client_id('client.cfg')
        return client_id

    def get_job(self):
        endpoint = f'{self.url}/get_job'
        params = {'client_id': self.client_id}
        # response = requests.get(endpoint, params=params)
        # response_text = loads(response.text)

        response_text = loads((requests.get(endpoint, params=params)).text)
        if 'job' not in response_text:
            raise NoJobsAvailableException()
        job = response_text['job']
        job_id = list(job.keys())[0]
        url = job[job_id]
        if 'job_type' in job:
            job_type = job['job_type']
        else:
            job_type = 'other'
        return job_id, url, job_type

    def send_job_results(self, job_id, job_result, files=None):
        endpoint = f'{self.url}/put_results'
        if 'errors' in job_result:
            data = {
                    'job_id': job_id,
                    'results': job_result
                    }
        else:
            data = {'directory': get_output_path(job_result),
                    'job_id': job_id,
                    'results': job_result}
        params = {'client_id': self.client_id}
        # print('****\n\n\n')
        # print(dumps(data))
        # print('****\n\n\n', flush=True)
        if files is not None:
            requests.put(endpoint, data=dumps(data), files=files, params=params)
        else:
            # used to be json=dumps(data), might be more consistent if we use data=dumps(data)
            requests.put(endpoint, data=dumps(data), params=params) 

    def execute_task(self):
        print('Requesting new job from server...')
        job_id, url, job_type = self.get_job()
        print('Received job!')
        print('Sending result back to server...')
        if job_type == 'attachments':
            print("this is an attachment")
            result = self.perform_attachment_job(url)
            print("this is the result", result)
        else:
            result = self.perform_job(url)
        self.send_job_results(job_id, result)
        print('Job complete!\n')

    def perform_job(self, url):
        print(f'Getting docket at {url}')
        url = url + f'?api_key={self.api_key}'
        json = assure_request(requests.get, url).json()
        print('Done with current job!')
        return json

    def write_client_id(self, filename):
        with open(filename, 'w', encoding='utf8') as file:
            file.write(str(self.client_id))


    def perform_attachment_job(self, url, **params):
        # added **params just in case needed for requests
        attachments = [] # This is a list of tuples ('file', binary file)
        print(url)
        url = url + f'?api_key={self.api_key}'
        # attachment_links = get_attachment_links(url, **params)
        response_from_related = requests.get(url, params=params)
        print(response_from_related)
        response_from_related = load(response_from_related)
        print(type(response_from_related))
        file_formats = response_from_related["data"][0]["attributes"]["fileFormats"]
        attachment_links= loads(file_formats)
        
        for link in attachment_links:
            attachments.append(('file', requests.get(link))) # must have 'file' as first element
            # check if its a pdf extract text (Maybe just check the last 3 chars?)
            # attachments.append(('text', extract_text(<attachment>))) # must have 'text' as first element

        return attachments


def read_client_id(filename):
    try:
        with open(filename, 'r', encoding='utf8') as file:
            return int(file.readline())
    except FileNotFoundError:
        return -1


def assure_request(request, url, sleep_time=60, **kwargs):
    while True:
        response = request(url, **kwargs)
        try:
            check_status_code(response)
            response.raise_for_status()
        except RequestConnectionError:
            print('Unable to connect to the server. '
                  'Trying again in a minute...')
            time.sleep(sleep_time)
        except HTTPError:
            print('An HTTP Error occured.')
        except RequestException:
            print('A Request Error occured.')
        if response is not None:
            return response


def check_status_code(response):
    status_code = response.status_code
    if status_code == 403:
        print(response.json()['error'])
    elif status_code > 400:
        print('Server error. Trying again in a minute...')


def get_key_path_string(results, key):
    if key in results.keys():
        if results[key] is None:
            return 'None/'
        return results[key] + "/"
    return ""


def get_output_path(results):
    if 'error' in results:
        return -1
    output_path = ""
    data = results["data"]["attributes"]
    # print(data + "printing data")
    output_path += get_key_path_string(data, "agencyId")
    output_path += get_key_path_string(data, "docketId")
    output_path += get_key_path_string(data, "commentOnDocumentId")
    output_path += results["data"]["id"] + "/"
    output_path += results["data"]["id"] + ".json"
    return output_path


def is_environment_variables_present():
    return (os.getenv('WORK_SERVER_HOSTNAME') is not None
            and os.getenv('WORK_SERVER_PORT') is not None
            and os.getenv('API_KEY') is not None)


if __name__ == '__main__':
    # https://api.regulations.gov/v4/attachments/0900006480cb703d
    load_dotenv()
    if not is_environment_variables_present():
        print('Need client environment variables')
        sys.exit(1)
    client = Client()
    client.get_client_id()
    print('Your ID is: ', client.client_id)
    while True:
        try:
            client.execute_task()
        except NoJobsAvailableException:
            print("No Jobs Available")
        time.sleep(3.6)
