import pymongo
from pymongo import MongoClient
from typing import Dict, List, Any, Optional
import os
from datetime import datetime


class Connector:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Connector, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.connection_string = "mongodb://localhost:27017/"
            self.database_name = "moo_d"
            self.client = None
            self.db = None
            self._connect()
            self._initialized = True

    def _connect(self):
        """Kết nối tới MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            print(f"Đã kết nối thành công tới database: {self.database_name}")
        except Exception as e:
            print(f"Lỗi kết nối MongoDB: {e}")
            raise

    def close_connection(self):
        """Đóng kết nối"""
        if self.client:
            self.client.close()
            print("✅ Đã đóng kết nối MongoDB")

    def insert_one(self, collection_name: str, document: Dict) -> str:
        """
        Thêm một document vào collection

        Args:
            collection_name: Tên collection
            document: Document cần thêm

        Returns:
            ID của document vừa thêm
        """
        try:
            collection = self.db[collection_name]
            result = collection.insert_one(document)
            print(f"✅ Đã thêm document với ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"❌ Lỗi khi thêm document: {e}")
            raise

    def insert_many(self, collection_name: str, documents: List[Dict]) -> List[str]:
        """
        Thêm nhiều documents vào collection

        Args:
            collection_name: Tên collection
            documents: Danh sách documents

        Returns:
            Danh sách IDs của documents vừa thêm
        """
        try:
            collection = self.db[collection_name]
            result = collection.insert_many(documents)
            inserted_ids = [str(id) for id in result.inserted_ids]
            print(f"✅ Đã thêm {len(inserted_ids)} documents")
            return inserted_ids
        except Exception as e:
            print(f"❌ Lỗi khi thêm nhiều documents: {e}")
            raise

    def find_one(self, collection_name: str, query: Dict = None) -> Optional[Dict]:
        """
        Tìm một document

        Args:
            collection_name: Tên collection
            query: Điều kiện tìm kiếm

        Returns:
            Document tìm thấy hoặc None
        """
        try:
            collection = self.db[collection_name]
            document = collection.find_one(query or {})
            return document
        except Exception as e:
            print(f"❌ Lỗi khi tìm document: {e}")
            raise

    def find_all(self, collection_name: str, query: Dict = None, limit: int = 0) -> List[Dict]:
        """
        Tìm tất cả documents thỏa điều kiện

        Args:
            collection_name: Tên collection
            query: Điều kiện tìm kiếm
            limit: Giới hạn số lượng kết quả

        Returns:
            Danh sách documents
        """
        try:
            collection = self.db[collection_name]
            cursor = collection.find(query or {})
            if limit > 0:
                cursor = cursor.limit(limit)
            return list(cursor)
        except Exception as e:
            print(f"❌ Lỗi khi tìm documents: {e}")
            raise

    def update_one(self, collection_name: str, query: Dict, update_data: Dict) -> bool:
        """
        Cập nhật một document

        Args:
            collection_name: Tên collection
            query: Điều kiện tìm document cần update
            update_data: Dữ liệu cập nhật

        Returns:
            True nếu thành công
        """
        try:
            collection = self.db[collection_name]
            result = collection.update_one(query, {"$set": update_data})
            print(f"✅ Đã cập nhật {result.modified_count} document")
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Lỗi khi cập nhật document: {e}")
            raise

    def delete_one(self, collection_name: str, query: Dict) -> bool:
        """
        Xóa một document

        Args:
            collection_name: Tên collection
            query: Điều kiện tìm document cần xóa

        Returns:
            True nếu thành công
        """
        try:
            collection = self.db[collection_name]
            result = collection.delete_one(query)
            print(f"✅ Đã xóa {result.deleted_count} document")
            return result.deleted_count > 0
        except Exception as e:
            print(f"❌ Lỗi khi xóa document: {e}")
            raise

    def count_documents(self, collection_name: str, query: Dict = None) -> int:
        """
        Đếm số documents thỏa điều kiện

        Args:
            collection_name: Tên collection
            query: Điều kiện đếm

        Returns:
            Số lượng documents
        """
        try:
            collection = self.db[collection_name]
            return collection.count_documents(query or {})
        except Exception as e:
            print(f"❌ Lỗi khi đếm documents: {e}")
            raise

    def create_index(self, collection_name: str, field: str, unique: bool = False):
        """
        Tạo index cho collection

        Args:
            collection_name: Tên collection
            field: Tên field cần index
            unique: Có phải unique index không
        """
        try:
            collection = self.db[collection_name]
            collection.create_index([(field, pymongo.ASCENDING)], unique=unique)
            print(f"✅ Đã tạo index cho field: {field}")
        except Exception as e:
            print(f"❌ Lỗi khi tạo index: {e}")
            raise

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_connection()

# Global instance - dùng chung cho cả app
db = Connector()
