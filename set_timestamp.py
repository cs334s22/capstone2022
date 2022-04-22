import redis
# import time

class JobQueueTest:

        def __init__(self, database):
            self.database = database

        def get_dockets_timestamp(self):
            # dockets_timestamp = self.database.get('dockets_last_timestamp')
            new_timestamp = "2022-04-22 12:30:50"
            return new_timestamp

        def set_dockets_timestamp(self, new_timestamp):
            self.database.sadd(new_timestamp, 'dockets_last_timestamp')
