import pymongo


class DataStorage:
    def __init__(self):
        database = pymongo.MongoClient('mongo', 27017)['mirrulations']
        self.dockets = database['dockets']
        self.documents = database['documents']
        self.comments = database['comments']
        self.attachments = database['attachments']

    def exists(self, search_element):
        result_id = search_element['id']

        return self.dockets.count_documents({'id': result_id}) > 0 or \
            self.documents.count_documents({'id': result_id}) > 0 or \
            self.comments.count_documents({'id': result_id}) > 0 or \
            self.attachments.count_documents({'id': result_id}) > 0

    def add(self, data):
        if 'type' in data['data'].keys():
            if data['data']['type'] == 'dockets':
                self.dockets.insert_one(data)
            elif data['data']['type'] == 'documents':
                self.documents.insert_one(data)
            elif data['data']['type'] == 'comments':
                self.comments.insert_one(data)

    def add_attachment(self, data):
        # if 'attachments_text' in data.keys():
        #     for attachment_text in data['data']['attachments_text']:
        #             data = {'id':data['data']['id'], 'text':attachment_text}
        #             self.attachments.insert_one(data)
        agency = data['agency']
        reg_id = data['reg_id']
        path = agency + '/' + reg_id
        for file in data['results']:
            entry = {'path': path, 'file': file}
            self.attachments.insert_one(entry)


    def get_collection_size(self, collection):
        return self.__getattribute__(collection).count_documents({})

