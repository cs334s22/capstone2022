import redis
import time

if __name__ == '__main__':
    database = redis.Redis()

    # Gets dockets_last_timestamp, documents_last_timestamp, and comments_last_timestamp timestamps
    dockets_timestamp = database.get('dockets_last_timestamp')
    documents_timestamp = database.get('documents_last_timestamp')
    comments_timestamp = database.get('comments_last_timestamp')

    # Sets dockets_last_timestamp, documents_last_timestamp, and comments_last_timestamp to an hour before
    # the current time
    new_dockets_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 3600))
    new_documents_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 3600))
    new_comments_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 3600))
    database.set('dockets_last_timestamp', new_dockets_timestamp)
    database.set('documents_last_timestamp', new_documents_timestamp)
    database.set('comments_last_timestamp', new_comments_timestamp)

    # Print for debugging
    print('Dockets Datetime: {}'.format(database.get('dockets_last_timestamp')))
    print('Documents Datetime: {}'.format(database.get('documents_last_timestamp')))
    print('Comments Datetime: {}'.format(database.get('comments_last_timestamp')))