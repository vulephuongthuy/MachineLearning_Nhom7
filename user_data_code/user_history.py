def check_user_id_types():
    from pymongo import MongoClient
    client = MongoClient('mongodb://localhost:27017/')
    db = client['moo_d']

    collections_to_check = ['purchase', 'user_favorite']

    for collection in collections_to_check:
        print(f"\n🔍 Checking {collection}:")

        # Lấy 2 document mẫu
        sample_docs = list(db[collection].find().limit(2))

        for i, doc in enumerate(sample_docs):
            user_id = doc.get('userId')
            print(
                f"  Document {i + 1}: userId = {user_id} (type: {type(user_id)})")


check_user_id_types()