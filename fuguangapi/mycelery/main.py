from celery import Celery
import os
import django

# 初始化django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuguangapi.settings.dev')
django.setup()

# 实例化Celery对象
app = Celery("fuguang")

# 导入配置文件
app.config_from_object("mycelery.settings")

# 注册任务
app.autodiscover_tasks(["mycelery.sms", "mycelery.email"])
