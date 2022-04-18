class Job():
    # This should probably be extracted into another class
    # def get_job(self):
    #     endpoint = f'{self.url}/get_job'
    #     params = {'client_id': self.client_id}g
    #     # response = requests.get(endpoint, params=params)
    #     # response_text = loads(response.text)

    #     response_text = loads((requests.get(endpoint, params=params)).text)
    #     if 'job' not in response_text:
    #         raise NoJobsAvailableException()
        
    #     return Job(response_text['job'])

    def __init__(self, job_json):
        self.job_json = job_json
        self.assign_job_id()
        self.assign_job_url()
        self.assign_job_type()

    def assign_job_id(self):
        self.job_id = list(self.job_json.keys())[0]

    def assign_job_url(self):
        self.job_url = self.job_json[self.job_id]

    def assign_job_type(self):
        if 'job_type' in self.job_json:
            self.job_type = self.job_json['job_type']
        else:
            self.job_type = 'other'