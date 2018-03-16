import pymongo


class MongoDB(object):

    MONGO_URI = ""
    MONGO_DATABASE = ""

    client = pymongo.MongoClient(MONGO_URI)
    db = client.MONGO_DATABASE
    collection = None

    def __init__(self, collection):
        self.collection = self.client[self.MONGO_DATABASE][collection]
        super(MongoDB, self).__init__()