import redis
# from mirrcore.redis_check import is_redis_available
import time

# class JobQueueTest:

#         def __init__(self, database):
#             self.database = database

#         def get_dockets_timestamp(self):
#             # dockets_timestamp = self.database.get('dockets_last_timestamp')
#             new_timestamp = "2022-04-22 12:30:50"
#             return new_timestamp

#         def set_dockets_timestamp(self, new_timestamp):
#             self.database.sadd(new_timestamp, 'dockets_last_timestamp')

if __name__ == '__main__':
    database = redis.Redis()
    # while not is_redis_available(database):
    #     print("Redis database is busy loading")
    #     time.sleep(30)
    
    # new_timestamp = "2022-04-22 12:30:50"
    dockets_timestamp = database.get('dockets_last_timestamp')
    documents_timestamp = database.get('documents_last_timestamp')
    comments_timestamp = database.get('comments_last_timestamp')
    # subtract 1 hour from dockets_timestamp using time module
    new_dockets_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 3600))
    new_documents_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 3600))
    new_comments_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 3600))
    database.set('dockets_last_timestamp', new_dockets_timestamp)
    database.set('documents_last_timestamp', new_documents_timestamp)
    database.set('comments_last_timestamp', new_comments_timestamp)
    print('Dockets Datetime: {}'.format(database.get('dockets_last_timestamp')))
    print('Documents Datetime: {}'.format(database.get('documents_last_timestamp')))
    print('Comments Datetime: {}'.format(database.get('comments_last_timestamp')))

    # queue_test = JobQueueTest(database)
    # job_queue = JobQueueTest(database)
    # new_timestamp = job_queue.get_dockets_timestamp()
    # set_new_timestamp = job_queue.set_dockets_timestamp(new_timestamp)
    # print(database.llen('dockets_last_timestamp'))
        

