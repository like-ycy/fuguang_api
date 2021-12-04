import json

from ckeditor_uploader.fields import RichTextUploadingField  # 支持文件上传
from django.utils import timezone as datetime
from django.utils.safestring import mark_safe
from stdimage import StdImageField

from fuguangapi.utils.models import BaseModel, models


class CourseDirection(BaseModel):
    """
    课程方向，例如：前端、后端、移动端
    """
    name = models.CharField(max_length=255, unique=True, verbose_name='课程方向')
    remark = RichTextUploadingField(default='', blank=True, null=True, verbose_name='课程方向描述')
    recomment_home_hot = models.BooleanField(default=False, verbose_name="是否推荐到首页新课栏目")
    recomment_home_top = models.BooleanField(default=False, verbose_name="是否推荐到首页必学栏目")

    class Meta:
        db_table = 'fg_course_direction'
        verbose_name = '课程方向'
        verbose_name_plural = verbose_name


class CourseCategory(BaseModel):
    """
    课程分类，例如：前端方向下有vue、js，后端方向下有python、javva
    """
    name = models.CharField(max_length=255, unique=True, verbose_name='分类名称')
    remark = RichTextUploadingField(default='', blank=True, null=True, verbose_name='分类描述')
    direction = models.ForeignKey('CourseDirection', on_delete=models.DO_NOTHING,
                                  related_name='category_list', db_constraint=False, verbose_name='学习方向')

    class Meta:
        db_table = 'fg_course_category'
        verbose_name = '课程分类'
        verbose_name_plural = verbose_name


class Course(BaseModel):
    """
    课程信息，例如：Vue分类下 vue基础语法，Python分类下 python基础语法
    """
    COURSE_TYPE = (
        (0, '实战课程'),
        (1, '会员专享'),
        (2, '学位课程'),
    )
    level_choices = (
        (0, '初级'),
        (1, '中级'),
        (2, '高级')
    )
    status_choices = (
        (0, '上线'),
        (1, '下线'),
        (2, '预上线')
    )
    # course_cover = models.ImageField(upload_to='course/cover', max_length=255, verbose_name='课程封面', null=True,
    #                                  blank=True)
    course_cover = StdImageField(variations={
        'thumb_1080x608': (1080, 608),
        'thumb_540x304': (540, 304),
        'thumb_108x61': (108, 61),
    }, max_length=255, upload_to='course/cover', verbose_name='课程封面', null=True, blank=True)
    course_video = models.FileField(upload_to='course/video', max_length=255, verbose_name='课程视频', null=True,
                                    blank=True)
    course_type = models.SmallIntegerField(choices=COURSE_TYPE, default=0, verbose_name='付费类型')
    level = models.SmallIntegerField(choices=level_choices, default=0, verbose_name='课程难度')
    description = RichTextUploadingField(null=True, blank=True, verbose_name='课程描述')
    pub_date = models.DateField(auto_now_add=True, verbose_name='发布日期')
    period = models.IntegerField(default=7, verbose_name='建议学习周期(day)')
    attachment_path = models.FileField(max_length=1000, verbose_name='课件路径', null=True, blank=True)
    attachment_link = models.FileField(max_length=1000, verbose_name='课件链接', null=True, blank=True)
    status = models.SmallIntegerField(choices=status_choices, default=0, verbose_name='课程状态')
    students = models.IntegerField(default=0, verbose_name='学习人数')
    recomment_home_hot = models.BooleanField(default=False, verbose_name='推荐到首页热门')
    recomment_home_top = models.BooleanField(default=False, verbose_name='推荐到首页必学栏目')
    lessons = models.IntegerField(default=0, verbose_name='总课时/小时')
    pub_lessons = models.IntegerField(default=0, verbose_name='已更新课时/小时')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='课程原价')
    credit = models.IntegerField(default=0, blank=True, null=True, verbose_name='积分')
    direction = models.ForeignKey('CourseDirection', on_delete=models.DO_NOTHING, related_name='course_list',
                                  null=True, blank=True, db_constraint=False, verbose_name='学习方向')
    category = models.ForeignKey('CourseCategory', on_delete=models.DO_NOTHING, related_name='course_list',
                                 null=True, blank=True, db_constraint=False, verbose_name='课程分类')
    teacher = models.ForeignKey('Teacher', related_name="course_list", null=True, blank=True,
                                on_delete=models.DO_NOTHING, db_constraint=False, verbose_name='授课老师')

    class Meta:
        db_table = 'fg_course_info'
        verbose_name = '课程信息'
        verbose_name_plural = verbose_name

    def course_cover_small(self):
        if self.course_cover:
            return mark_safe(f'<img style="border-radius: 0%;" src="{self.course_cover.thumb_108x61.url}">')
        return ""

    course_cover_small.short_description = "封面图片(108x61)"
    course_cover_small.allow_tags = True
    course_cover_small.admin_order_field = "course_cover"

    def course_cover_medium(self):
        if self.course_cover:
            return mark_safe(f'<img style="border-radius: 0%;" src="{self.course_cover.thumb_540x304.url}">')
        return ""

    course_cover_medium.short_description = "封面图片(540x304)"
    course_cover_medium.allow_tags = True
    course_cover_medium.admin_order_field = "course_cover"

    def course_cover_large(self):
        if self.course_cover:
            return mark_safe(f'<img style="border-radius: 0%;" src="{self.course_cover.thumb_1080x608.url}">')
        return ""

    course_cover_large.short_description = "封面图片(1080x608)"
    course_cover_large.allow_tags = True
    course_cover_large.admin_order_field = "course_cover"

    @property
    def discount(self):
        # 通过计算获取当前课程的折扣优惠相关的信息
        now_time = datetime.now()

        # 获取当前课程参与的最新活动记录
        last_activity_log = self.price_list.filter(
            activity__end_time__gt=now_time,
            activity__start_time__lt=now_time).order_by('-id').first()

        type_text = ""  # 优惠类型的默认值
        price = -1  # 优惠价格
        expire = 0  # 优惠剩余时间

        if last_activity_log:
            # 如果有活动记录，则获取相关信息
            type_text = last_activity_log.discount.discount_type.name
            # 获取限时活动剩余时间戳[单位：s]
            expire = last_activity_log.activity.end_time.timestamp() - now_time.timestamp()

            # 判断课程价格是否满足优惠条件
            course_price = float(self.price)  # 课程原价
            condition_price = float(last_activity_log.discount.condition)  # 优惠条件价格
            if course_price >= condition_price:
                # 如果课程价格满足优惠条件，则计算优惠价格
                sale = last_activity_log.discount.sale  # 计算公式 *0.8，-200
                if sale[0] == '0':
                    price = 0
                elif sale[0] == '*':
                    price = course_price * float(sale[1:])
                elif sale[0] == '-':
                    price = course_price - float(sale[1:])

                price = float(f'{price:.2f}')

        data = {}
        if type_text:
            data['type'] = type_text
        if price != -1:
            data['price'] = price
        if expire > 0:
            data['expire'] = expire

        return data

    def discount_json(self):
        # 必须转成字符串才能保存到es中。所以该方法提供给es使用的。
        return json.dumps(self.discount)

    @property
    def can_free_study(self):
        # 判断当前课程是否可以免费学习
        lesson_list = self.lesson_list.filter(is_show=True, is_delete=False, free_trail=True
                                              ).order_by("orders").all()
        return len(lesson_list) > 0


class Teacher(BaseModel):
    """
    老师信息
    """
    role_choices = (
        (0, '讲师'),
        (1, '导师'),
        (2, '班主任')
    )
    role = models.SmallIntegerField(choices=role_choices, default=0, verbose_name='讲师身份')
    title = models.CharField(max_length=255, verbose_name='职称、职位')
    signature = models.CharField(max_length=255, blank=True, null=True, verbose_name='讲师签名')
    # avatar = models.ImageField(upload_to='teacher', null=True, verbose_name='讲师头像')
    avatar = StdImageField(variations={
        'thumb_800x800': (800, 800),  # 'large': (800, 800),
        'thumb_400x400': (400, 400),  # 'medium': (400, 400),
        'thumb_50x50': (50, 50, True),  # 'small': (50, 50, True),
    }, delete_orphans=True, upload_to='teacher', null=True, verbose_name='讲师头像')
    brief = RichTextUploadingField(max_length=1024, verbose_name='讲师描述')

    class Meta:
        db_table = 'fg_teacher'
        verbose_name = '讲师信息'
        verbose_name_plural = verbose_name

    def avatar_small(self):
        if self.avatar:
            return mark_safe(f'<img style="border-radius: 100%;" src="{self.avatar.thumb_50x50.url}">')
        return ""

    avatar_small.short_description = "头像信息(50x50)"
    avatar_small.allow_tags = True
    avatar_small.admin_order_field = "avatar"

    def avatar_medium(self):
        if self.avatar:
            return mark_safe(f'<img style="border-radius: 100%;" src="{self.avatar.thumb_400x400.url}">')
        return ""

    avatar_medium.short_description = "头像信息(400x400)"
    avatar_medium.allow_tags = True
    avatar_medium.admin_order_field = "avatar"

    def avatar_large(self):
        if self.avatar:
            return mark_safe(f'<img style="border-radius: 100%;" src="{self.avatar.thumb_800x800.url}">')
        return ""

    avatar_large.short_description = "头像信息(800x800)"
    avatar_large.allow_tags = True
    avatar_large.admin_order_field = "avatar"


class CourseChapter(BaseModel):
    """
    课程章节
    """
    orders = models.SmallIntegerField(default=1, verbose_name='第几章节')
    summary = RichTextUploadingField(blank=True, null=True, verbose_name='章节介绍')
    pub_date = models.DateField(auto_now_add=True, verbose_name='发布时间')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='chapter_list', db_constraint=False,
                               verbose_name='课程名称')

    class Meta:
        db_table = 'fg_course_chapter'
        verbose_name = '课程章节'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s-%s章节-%s' % (self.course.name, self.orders, self.name)

    def text(self):
        return self.__str__()

    text.short_description = "章节名称"
    text.allow_tags = True
    text.admin_order_field = "orders"


class CourseLesson(BaseModel):
    """
    课程课时
    """
    lesson_type_choices = (
        (0, '文档'),
        (1, '练习'),
        (2, '视频')
    )
    orders = models.SmallIntegerField(default=1, verbose_name='第几课时')
    lesson_type = models.SmallIntegerField(default=2, verbose_name='课时类型', choices=lesson_type_choices)
    lesson_link = models.CharField(max_length=255, blank=True, null=True, verbose_name='课时链接')
    duration = models.CharField(max_length=32, blank=True, null=True, verbose_name='课时时长')
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name='发布时间')
    free_trail = models.BooleanField(default=False, verbose_name='是否试看')
    recomment = models.BooleanField(default=False, verbose_name='是否推荐到课程列表')
    chapter = models.ForeignKey('CourseChapter', on_delete=models.CASCADE, related_name='lesson_list',
                                db_constraint=False,
                                verbose_name='课程章节')
    course = models.ForeignKey('Course', on_delete=models.DO_NOTHING, related_name='lesson_list', db_constraint=False,
                               verbose_name='课程名称')

    class Meta:
        db_table = 'fg_course_lesson'
        verbose_name = '课时信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return "%s-%s" % (self.chapter, self.name)

    def text2(self):
        return self.__str__()

    text2.short_description = "课时名称"
    text2.allow_tags = True
    text2.admin_order_field = "orders"


class Activity(BaseModel):
    """
    活动时间
    """
    start_time = models.DateTimeField(verbose_name='开始时间', default=datetime.now)
    end_time = models.DateTimeField(verbose_name='结束时间', default=datetime.now)
    description = RichTextUploadingField(verbose_name='活动描述', null=True, blank=True)
    remark = models.TextField(verbose_name='备注', null=True, blank=True)

    class Meta:
        db_table = 'fg_activity'
        verbose_name = '优惠活动'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class DiscountType(BaseModel):
    """
    优惠类型
        限时免费
        限时减免
        限时折扣
    """
    remark = models.CharField(max_length=255, verbose_name='备注', null=True, blank=True)

    class Meta:
        db_table = 'fg_discount_type'
        verbose_name = '优惠类型'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Discount(BaseModel):
    """
    优惠计算公式
    """
    discount_type = models.ForeignKey('DiscountType', on_delete=models.CASCADE, related_name='discount_list',
                                      db_constraint=False, verbose_name='优惠类型')
    condition = models.IntegerField(verbose_name='优惠条件', default=0,
                                    blank=True, help_text='设置享受优惠的价格条件，不填或0为没有优惠')
    sale = models.TextField(verbose_name="优惠计算公式", help_text="""
    0表示免费；<br>
    *号开头表示折扣价，例如填写*0.82,则表示八二折；<br>
    -号开头表示减免价, 例如填写-100,则表示减免100；<br>
    """)

    class Meta:
        db_table = 'fg_discount'
        verbose_name = '优惠计算公式'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'价格优惠:{self.discount_type.name}, 优惠条件:{self.condition}, 优惠公式: {self.sale}'


class CourseActivityPrice(BaseModel):
    """
    课程优惠价格表
    """
    activity = models.ForeignKey('Activity', on_delete=models.CASCADE, related_name='price_list',
                                 db_constraint=False, verbose_name='活动')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='price_list',
                               db_constraint=False, verbose_name='课程')
    discount = models.ForeignKey('Discount', on_delete=models.CASCADE, related_name='price_list',
                                 db_constraint=False, verbose_name='优惠')

    class Meta:
        db_table = 'fg_course_activity_price'
        verbose_name = '课程参与活动的价格表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"活动:{self.activity.name}-课程:{self.course.name}-优惠公式:{self.discount.sale}"
