# oss/utils.py
import oss2
from django.conf import settings
import uuid
from datetime import datetime
import os

class OSSManager:
    def __init__(self):
        self.auth = oss2.Auth(
            settings.ALIYUN_OSS_CONFIG['ACCESS_KEY_ID'],
            settings.ALIYUN_OSS_CONFIG['ACCESS_KEY_SECRET']
        )
        self.bucket = oss2.Bucket(
            self.auth,
            settings.ALIYUN_OSS_CONFIG['ENDPOINT'],
            settings.ALIYUN_OSS_CONFIG['BUCKET_NAME']
        )
        self.cdn_domain = settings.ALIYUN_OSS_CONFIG.get('CDN_DOMAIN', '')

    def generate_object_name(self, original_filename, prefix='uploads'):
        """生成唯一的对象名称"""
        ext = os.path.splitext(original_filename)[1]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}{ext}"
        return f"{prefix}/{filename}"

    def upload_file(self, file_obj, original_filename, prefix='uploads'):
        """上传文件到OSS"""
        try:
            # 生成对象名称
            object_name = self.generate_object_name(original_filename, prefix)
            
            # 上传文件
            result = self.bucket.put_object(object_name, file_obj)
            
            if result.status == 200:
                # 返回文件URL
                if self.cdn_domain:
                    file_url = f"https://{self.cdn_domain}/{object_name}"
                else:
                    file_url = f"https://{self.bucket.bucket_name}.{settings.ALIYUN_OSS_CONFIG['ENDPOINT']}/{object_name}"
                
                return {
                    'success': True,
                    'url': file_url,
                    'object_name': object_name,
                    'filename': original_filename
                }
            else:
                return {'success': False, 'error': '上传失败'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_file(self, object_name):
        """删除OSS上的文件"""
        try:
            result = self.bucket.delete_object(object_name)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def list_files(self, prefix='', max_keys=100):
        """列出OSS中的文件"""
        try:
            files = []
            for obj in oss2.ObjectIterator(self.bucket, prefix=prefix, max_keys=max_keys):
                files.append({
                    'key': obj.key,
                    'size': obj.size,
                    'last_modified': obj.last_modified
                })
            return {'success': True, 'files': files}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def test_connection(self):
        """测试OSS连接"""
        try:
            # 尝试列出Bucket信息
            bucket_info = self.bucket.get_bucket_info()
            return {
                'success': True,
                'bucket_name': bucket_info.name,
                'location': bucket_info.location,
                'creation_date': bucket_info.creation_date
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

# 创建全局实例
oss_manager = OSSManager()
