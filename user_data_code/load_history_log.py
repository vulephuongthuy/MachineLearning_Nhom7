# ---------------- Upload each JSON file in a folder as its own MongoDB collection ----------------
import os
import json
from pymongo import MongoClient


def upload_each_file_as_collection(folder_path, db_name, mongo_uri="mongodb://localhost:27017/"):
    """
    Mỗi file JSON trong folder sẽ được upload vào một collection riêng biệt trong MongoDB.
    - folder_path: đường dẫn đến folder chứa file JSON
    - db_name: tên database trên MongoDB
    - mongo_uri: link kết nối MongoDB (mặc định localhost)
    """
    # Kết nối MongoDB
    client = MongoClient(mongo_uri)
    db = client[db_name]

    total_files = 0

    # Duyệt tất cả file JSON trong folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            collection_name = os.path.splitext(filename)[0]  # bỏ .json → tên collection

            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):  # nếu là danh sách nhiều document
                        db[collection_name].insert_many(data)
                    else:  # nếu là 1 document duy nhất
                        db[collection_name].insert_one(data)
                    print(f"Uploaded {filename} → collection '{collection_name}'")
                    total_files += 1
                except Exception as e:
                    print(f"Lỗi khi upload {filename}: {e}")

    client.close()


# ---------------- Example ----------------
if __name__ == "__main__":
    # Đường dẫn folder chứa các file JSON
    folder_path = r"D:\MachineLearning\FinalProject\data\history_log"

    # Tên database trên MongoDB
    db_name = "moo_d"

    #  Link MongoDB (localhost hoặc Atlas)
    mongo_uri = "mongodb://localhost:27017/"

    # Gọi hàm
    upload_each_file_as_collection(folder_path, db_name, mongo_uri)
