"""
Celery configuartion
"""

# 任务队列的redis地址
broker_url = "redis://dba:123.com@127.0.0.1:6379/14"

# 结果存储的redis地址
result_backend = "redis://dba:123.com@127.0.0.1:6379/15"
