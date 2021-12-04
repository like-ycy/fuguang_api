from celery import Celery
import os

# 初始化django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuguangapi.settings.dev')

# 实例化Celery对象
app = Celery("fuguangapi")

# 指定任务的队列名称
app.conf.task_default_queue = 'Celery'

# 导入配置文件
app.config_from_object("django.conf:settings", namespace="CELERY")

# 注册任务
app.autodiscover_tasks()
