from django.utils.safestring import mark_safe

from models import BaseModel, models


class Nav(BaseModel):
    """
    导航菜单
    """
    POSITION_CHOICES = (
        (0, "顶部导航"),
        (1, "脚部导航")
    )
    link = models.CharField(max_length=255, verbose_name="导航链接")
    is_http = models.BooleanField(default=False, verbose_name="是否为外部链接")
    position = models.SmallIntegerField(choices=POSITION_CHOICES, default=0, verbose_name="导航位置")

    class Meta:
        db_table = "fg_nav"
        verbose_name = "导航菜单"
        verbose_name_plural = verbose_name


class Banner(BaseModel):
    """
    轮播图模型
    models.ImageField 表示该字段的内容，按图片格式进行处理，通过upload_to进行指定保存的目录
    图片的保存目录为 settings.MEDIA_ROOT/upload_to/图片名称
    upload_to 支持格式化字符串，可以指定保存的目录 %Y 表示年份 %m 表示月份 %d 表示日期 %H 表示小时 %M 表示分钟 %S 表示秒
    """
    image = models.ImageField(upload_to="banner/%Y/", verbose_name="图片地址")
    link = models.CharField(max_length=255, verbose_name="轮播图链接")
    is_http = models.BooleanField(default=False, verbose_name="是否为外部链接",
                                  help_text="站内地址：/book/  站外地址: https://baidu.com/book")
    note = models.CharField(max_length=255, verbose_name="备注信息")

    class Meta:
        db_table = "fg_banner"
        verbose_name = "轮播图"
        verbose_name_plural = verbose_name

    def image_html(self):
        if self.image:
            return mark_safe(
                f'<img style="border-radius: 0%;max-height: 100px; max-width: 400px;" src="{self.image.url}">')

    image_html.short_description = "轮播图片"
    image_html.allow_tags = True
    image_html.admin_order_field = "image"
