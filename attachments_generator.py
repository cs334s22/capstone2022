import redis
import time
from mirrcore.job_queue import JobQueue
from mirrcore.redis_check import is_redis_available
import random
import json


class AttachmentsGenerator:

        def __init__(self, job_queue, database):
            self.job_queue = job_queue
            self.database = database

        def get_job_id(self):
            job_id = self.database.incr('last_job_id')
            return job_id

        def add_job(self, job_type, url):
            job_id = self.get_job_id()
            if job_type == 'attachments':
                job = {'job_id': job_id,
                        'url': random.randint(0, 6),
                        'job_type': job_type
                    }
            else:
                job = {'job_id': job_id,
                        'url': url,
                        'job_type': job_type
                    }
            return job

        def add_job_type_counter(job, database):
            job_count = {'num_jobs' : 0}
            if job['job_type'] == 'attachments':
                job_count['num_jobs'] += 1
                database.lpush('num_jobs_attach_queue', json.dumps(job_count))
            if job['job_type'] == 'comments':
                job_count['num_jobs'] += 1
                database.lpush('num_jobs_comments_queue', json.dumps(job_count))
            if job['job_type'] == 'dockets':
                job_count['num_jobs'] += 1
                database.lpush('num_jobs_dockets_queue', json.dumps(job_count))
            if job['job_type'] == 'documents':
                job_count['num_jobs'] += 1
                database.lpush('num_jobs_documents_queue', json.dumps(job_count))
    
    
if __name__ == '__main__':
    database = redis.Redis()
    while not is_redis_available(database):
        print("Redis database is busy loading")
        time.sleep(30)

    job_queue = JobQueue(database)
    generator = AttachmentsGenerator(job_queue, database)

    documents_lst = ["https://api.regulations.gov/v4/documents/EPA-HQ-OA-2003-0003-0003",
                        "https://api.regulations.gov/v4/documents/APHIS-2005-0003-0008",
                        "https://api.regulations.gov/v4/documents/EPA-HQ-OAR-2001-0006-0123"]
    comments_lst = ["https://api.regulations.gov/v4/comments/EPA-HQ-OPP-2003-0132-0596",
                        "https://api.regulations.gov/v4/comments/EPA-HQ-OPP-2003-0132-0274",
                        "https://api.regulations.gov/v4/comments/EPA-HQ-OAR-2002-0056-0366"]

    document_index = 0
    comments_index = 0
    print(database.llen('jobs_waiting_queue'))
    for x in range(10):
        if x == 0 or x == 1 or x == 2:
            job = generator.add_job('comments', comments_lst[comments_index])
            #generator.add_job_type_counter(job, database)
            comments_index += 1

        elif x == 3 or x == 4 or x == 5:
            job = generator.add_job('documents', documents_lst[document_index])
            #generator.add_job_type_counter(job, database)
            document_index += 1

        elif x == 6:
            job = generator.add_job('dockets', 'https://api.regulations.gov/v4/dockets/NCUA-2021-0112')
            #generator.add_job_type_counter(job, database)

        elif x == 7 or x == 8 or x == 9:
            job = generator.add_job('attachments', 'none')
            #generator.add_job_type_counter(job, database)
        database.lpush('jobs_waiting_queue', json.dumps(job))


    print(database.llen('jobs_waiting_queue'))


