import random

from django.core.management.base import BaseCommand
from faker import Faker

from courses.models import Teacher

# 实例化faker对象并设置简体中文
faker = Faker(['zh_CN'])


# 类名必须是Command而且一个文件就是一个命令类，这个命令类必须直接或间接继承BaseCommand
class Command(BaseCommand):
    help = "生成测试数据"

    def add_arguments(self, parser):
        parser.add_argument('--type', type=str, default='teacher',
                            dest='type', help='测试数据类型')
        parser.add_argument('--number', type=int, default=10,
                            dest='number', help='生成数据的数量')

    def handle(self, *args, **options):
        """添加测试数据"""
        if options['type'] == 'teacher':
            self.add_teacher(options)
        elif options['type'] == 'course':
            self.add_course(options)

    def add_teacher(self, options):
        """添加老师的测试数据"""
        for i in range(options['number']):
            Teacher.objects.create(
                name=faker.unique.name(),
                avatar='teacher/avatar.jpg',
                role=random.randint(0, 2),
                title="老师",
                signature="没有教不会的学生，有就是你不行！",
                brief=f"从业3年，管理班级无数，联系电话：{faker.unique.phone_number()}，邮箱地址：{faker.unique.company_email()}",
            )
        print('添加老师完成')

    def add_course(self, options):
        """添加课程信息"""
        pass
        # Course.objects.create(
        #     name='python变量',
        #     course_cover='course/course_5.png',
        #     course_type=random.randint(0, 2),
        #     level=random.randint(0, 2),
        #     status=random.randint(0, 2),
        #     students=random.randint(1, 100),
        #     lessons=random.randint(100, 1000),
        #     pub_lessons=random.randint(10, 300),
        #     price=random.randint(300, 9999),
        #     direction_id=2,
        #     category_id=20,
        # )
