import uuid

import oss2

if __name__ == '__main__':
    OSS_ACCESS_KEY_ID = 'LTAI5t6a87q8Z8rZnb6juW6c'
    OSS_ACCESS_KEY_SECRET = 'xXxhro5jJ8snG10LW0TzrFy4dxw6CD'
    OSS_ENDPOINT = 'oss-cn-beijing.aliyuncs.com'
    OSS_BUCKET_NAME = 'fuguang-online'
    OSS_SERVER_URL = f'https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}'

    # 创建命名空间操作实例对象
    auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)

    # 上传文件
    # 在oss中的文件路径
    image = f"{str(uuid.uuid4())}.jpg"
    # 本地的文件路径
    with open('/home/wang/fuguang/fuguangapi/fuguangapi/uploads/avatar/2021/avatar.jpg', 'rb') as f:
        result = bucket.put_object(image, f.read())
