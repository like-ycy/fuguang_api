import json

from django.utils import timezone as datetime
from django_redis import get_redis_connection

from courses.models import Course


def get_user_coupon_list(user_id):
    """获取指定用户拥有的所有优惠券列表"""
    # 获取redis连接
    redis = get_redis_connection('coupon')
    # 从redis中获取用户的优惠券信息
    coupon_list = redis.keys(f'{user_id}:*')  # bytes类型，[b'1:11', b'1:12']
    try:
        # 将bytes类型转换为list类型
        coupon_id_list = [item.decode() for item in coupon_list]  # [b'1:11', b'1:12'] <用户id>:<优惠券发放记录id>
    except:
        coupon_id_list = []

    coupon_data = []
    # 遍历coupon_id_list获取优惠券详细信息
    for coupon_key in coupon_id_list:  # coupon_key  1:11，1:12
        coupon_item = {"user_coupon_id": int(coupon_key.split(":")[-1])}
        coupon_hash = redis.hgetall(
            coupon_key)  # coupon_hash {b'to_category': b'[]', b'condition': b'0', b'discount': b'1', .....}
        # 将coupon_hash的bytes类型转换为dict类型
        for key, value in coupon_hash.items():
            key = key.decode()
            value = value.decode()
            if key in ['to_course', 'to_category', 'to_direction']:
                value = json.loads(value)
            coupon_item[key] = value  # {'to_direction': '[]'} {'to_course': '[]'}
        coupon_data.append(coupon_item)  # 将字典添加到列表中
    return coupon_data


def get_user_enable_coupon_list(user_id):
    """获取指定用户本次下单的可用优惠券列表"""

    # 先获取所有的优惠券列表
    coupon_data = get_user_coupon_list(user_id)

    # 获取指定用户的购物车中的勾选商品[与优惠券的适用范围进行比对，找出能用的优惠券]
    redis = get_redis_connection("cart")
    cart_hash = redis.hgetall(f"cart_{user_id}")
    # 获取被勾选的商品课程的ID列表
    course_id_list = {int(key.decode()) for key, value in cart_hash.items() if value == b'1'}
    # 获取被勾选的商品课程的模型对象列表
    course_list = Course.objects.filter(pk__in=course_id_list, is_delete=False, is_show=True).all()
    category_id_list = set()
    direction_id_list = set()
    for course in course_list:
        category_id_list.add(int(course.category.id))
        direction_id_list.add(int(course.direction.id))

    # 遍历优惠券列表，找出能用的优惠券
    enable_coupon_list = []
    for item in coupon_data:
        coupon_type = int(item.get("coupon_type"))

        if coupon_type == 0:
            # 通用优惠券
            item["enable_course"] = "__all__"
            enable_coupon_list.append(item)

        elif coupon_type == 3:
            # 指定课程优惠券
            coupon_course = {int(course_item["course__id"]) for course_item in item.get("to_course")}
            ret = course_id_list & coupon_course
            if len(ret) > 0:
                item["enable_course"] = {int(course.id) for course in course_list if course.id in ret}
                enable_coupon_list.append(item)

        elif coupon_type == 2:
            # 指定学习分类优惠券
            coupon_category = {int(category_item["category__id"]) for category_item in item.get("to_category")}
            ret = category_id_list & coupon_category
            if len(ret) > 0:
                item["enable_course"] = {int(course.id) for course in course_list if course.category.id in ret}
                enable_coupon_list.append(item)

        elif coupon_type == 1:
            # 指定学习方向优惠券
            coupon_direction = {int(direction_item["direction__id"]) for direction_item in item.get("to_direction")}
            # 取交集
            ret = direction_id_list & coupon_direction
            if len(ret) > 0:
                item["enable_course"] = {int(course.id) for course in course_list if course.direction.id in ret}
                enable_coupon_list.append(item)

    return enable_coupon_list


def add_coupon_to_redis(obj):
    """添加优惠券使用记录到redis"""
    redis = get_redis_connection('coupon')
    # 记录优惠券信息到redis中
    pipe = redis.pipeline()
    pipe.multi()
    pipe.hset(f"{obj.user.id}:{obj.id}", "coupon_id", obj.coupon.id)
    pipe.hset(f"{obj.user.id}:{obj.id}", "name", obj.coupon.name)
    pipe.hset(f"{obj.user.id}:{obj.id}", "discount", obj.coupon.discount)
    pipe.hset(f"{obj.user.id}:{obj.id}", "get_discount_display", obj.coupon.get_discount_display())
    pipe.hset(f"{obj.user.id}:{obj.id}", "coupon_type", obj.coupon.coupon_type)
    pipe.hset(f"{obj.user.id}:{obj.id}", "get_coupon_type_display",
              obj.coupon.get_coupon_type_display())
    pipe.hset(f"{obj.user.id}:{obj.id}", "start_time",
              obj.coupon.start_time.strftime("%Y-%m-%d %H:%M:%S"))
    pipe.hset(f"{obj.user.id}:{obj.id}", "end_time", obj.coupon.end_time.strftime("%Y-%m-%d %H:%M:%S"))
    pipe.hset(f"{obj.user.id}:{obj.id}", "get_type", obj.coupon.get_type)
    pipe.hset(f"{obj.user.id}:{obj.id}", "get_get_type_display", obj.coupon.get_get_type_display())
    pipe.hset(f"{obj.user.id}:{obj.id}", "condition", obj.coupon.condition)
    pipe.hset(f"{obj.user.id}:{obj.id}", "sale", obj.coupon.sale)
    pipe.hset(f"{obj.user.id}:{obj.id}", "to_direction",
              json.dumps(list(obj.coupon.to_direction.values("direction__id", "direction__name"))))
    pipe.hset(f"{obj.user.id}:{obj.id}", "to_category",
              json.dumps(list(obj.coupon.to_category.values("category__id", "category__name"))))
    pipe.hset(f"{obj.user.id}:{obj.id}", "to_course",
              json.dumps(list(obj.coupon.to_course.values("course__id", "course__name"))))
    pipe.expire(f"{obj.user.id}:{obj.id}",
                int(obj.coupon.end_time.timestamp() - datetime.now().timestamp()))
    pipe.execute()
