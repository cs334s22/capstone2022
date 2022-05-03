import os
import sys
import time
import dotenv
import redis
from mirrgen.search_iterator import SearchIterator
from mirrcore.redis_check import is_redis_available
from mirrcore.regulations_api import RegulationsAPI
from mirrcore.data_storage import DataStorage
from mirrcore.job_queue import JobQueue


class Validator:

    def __init__(self, api, datastorage, job_queue):
        self.api = api
        self.datastorage = datastorage
        self.job_queue = job_queue

    def download(self, endpoint):
        beginning_timestamp = '1972-01-01 00:00:00'
        collection_size = self.datastorage.get_collection_size(endpoint)
        counter = 0
        for result in SearchIterator(self.api, endpoint, beginning_timestamp):
            if result == {}:
                continue
            for res in result['data']:
                if not self.datastorage.exists(res):
                    print(res['id'])
                    self.job_queue.add_job(res['links']['self'], res['type'])
                counter += 1
            percentage = (counter / collection_size) * 100
            print(f'{percentage:.2f}%')


def generate_work(collection=None):
    dotenv.load_dotenv()

    database = redis.Redis('redis')
    # Sleep for 30 seconds to give time to load
    while not is_redis_available(database):
        print("Redis database is busy loading")
        time.sleep(30)

    api_prefix = collection.upper() if collection else 'DOCKETS'
    api_key = os.getenv(api_prefix + '_API_KEY')
    api = RegulationsAPI(api_key)
    storage = DataStorage()
    job_queue = JobQueue(database)
    generator = Validator(api, storage, job_queue)

    if not collection:
        generator.download('dockets')
        generator.download('documents')
        generator.download('comments')
    else:
        generator.download(collection)


if __name__ == '__main__':
    job_types = ('dockets', 'documents', 'comments')
    while True:
        if len(sys.argv) > 1 and sys.argv[1] in job_types:
            generate_work(sys.argv[1])
        else:
            generate_work()
        time.sleep(60*60*24*30)
