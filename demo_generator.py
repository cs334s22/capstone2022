import redis
import time
from mirrcore.job_queue import JobQueue
from mirrcore.redis_check import is_redis_available
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
            job = {'job_id': job_id,
                    'url': url,
                    'job_type': job_type,
                    'agency': 'EPA',
                    'reg_id': '12345'
                }
            return job
    
    
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
    attachments_lst = ["https://api.regulations.gov/v4/comments/EPA-HQ-OPP-2003-0101-0035/attachments",
                        "https://api.regulations.gov/v4/comments/EPA-HQ-OPP-2003-0360-0022/attachments",
                        "https://api.regulations.gov/v4/comments/EPA-HQ-OECA-2004-0024-0052/attachments",
                        "https://api.regulations.gov/v4/comments/EPA-HQ-OAR-2002-0024-0264/attachments"]

    document_index = 0
    comment_index = 0
    attachment_index = 0
    for x in range(11):
        if x == 0 or x == 1 or x == 2:
            job_queue.add_job(comments_lst[comment_index], job_type='comments', agency='EPA', reg_id='12345')
            comment_index += 1

        elif x == 3 or x == 4 or x == 5:
            job_queue.add_job(documents_lst[document_index], job_type='documents', agency='EPA', reg_id='12345')
            document_index += 1

        elif x == 6:
            job_queue.add_job('https://api.regulations.gov/v4/dockets/NCUA-2021-0112', job_type='dockets', agency='EPA', reg_id='12345')

        elif x == 7 or x == 8 or x == 9 or x == 10:
            job_queue.add_job(attachments_lst[attachment_index], job_type='attachments', agency='EPA', reg_id='12345')
            attachment_index += 1

