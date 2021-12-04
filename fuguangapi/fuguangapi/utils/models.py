from django.db import models


class BaseModel(models.Model):
    """
    公共模型基类
    保存项目中的所有模型的公共属性和公共方法的声明
    """
    name = models.CharField(max_length=255, verbose_name='名称/标题')
    orders = models.IntegerField(default=0, verbose_name='显示顺序')
    is_show = models.BooleanField(default=True, verbose_name='是否显示')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_delete = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
