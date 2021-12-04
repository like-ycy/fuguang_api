from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from courses.models import Course
from users.models import UserCourse


class CartViewSet(ViewSet):
    """购物车"""

    # 登录状态才可以调用当前视图，即添加购物车
    permission_classes = [IsAuthenticated]

    def add_cart(self, request):
        """添加购物车"""
        # 接受客户端发送的数据 <用户id> <课程id> <勾选状态>
        user_id = request.user.id
        course_id = request.data.get('course_id')
        selected = 1  # 在购物车中是否被选中，默认勾选

        # 验证数据
        try:
            # 判断课程是否存在
            Course.objects.get(is_delete=False, is_show=True, pk=course_id)
        except Course.DoesNotExist:
            return Response({'errmsg': '课程不存在'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 判断用户是否已经购买了
            UserCourse.objects.get(user_id=user_id, course_id=course_id)
            return Response({"errmsg": "对不起，您已经购买过当前课程！不需要重新购买了."}, status=status.HTTP_400_BAD_REQUEST)
        except:
            pass

        redis = get_redis_connection("cart")  # redis连接对象
        ret = redis.hexists(f'cart_{user_id}', course_id)  # 判断购物车是否已经添加当前课程
        cart_total = redis.hlen(f'cart_{user_id}')  # 购物车总数，即用户加入进去几个课程
        # 添加该课程了
        if ret:
            return Response({
                'errmsg': '当前商品课程已经被添加到购物车，请不要重复添加！',
                'cart_total': cart_total})

        # 没买过的课程保存到购物车
        redis.hset(f'cart_{user_id}', course_id, selected)
        cart_total = redis.hlen(f'cart_{user_id}')  # 购物车总数，即用户加入进去几个课程
        return Response({
            'errmsg': '成功添加商品到购物车！',
            'cart_total': cart_total}, status=status.HTTP_201_CREATED)

    def list(self, request):
        """购物车商品列表页"""
        # 查询购物车中的商品课程ID列表
        user_id = request.user.id
        redis = get_redis_connection("cart")
        cart_hash = redis.hgetall(f"cart_{user_id}")
        if len(cart_hash) < 1:
            return Response({"errmsg": "购物车没有任何商品。"}, status=status.HTTP_204_NO_CONTENT)

        # 把redis中的购物车信息转换成普通字典
        cart_dict = {int(course_id.decode()): bool(int(selected.decode())) for course_id, selected in cart_hash.items()}

        # 从mysql中提取购物车商品对应的商品其他信息
        course_list = Course.objects.filter(pk__in=cart_dict.keys(), is_delete=False, is_show=True).all()

        # 把course_list进行遍历，提取课程中的信息组成列表
        data = []
        for course in course_list:
            data.append({
                "id": course.id,
                "name": course.name,
                "course_cover": course.course_cover.url,
                "price": float(course.price),
                "discount": course.discount,
                "credit": course.credit,
                "course_type": course.get_course_type_display(),
                "selected": cart_dict[course.id],
            })
        # 返回客户端
        return Response({"errmsg": "ok！", "cart": data})

    def change_select(self, request):
        """改变购物车中商品的勾选状态"""
        user_id = request.user.id
        course_id = int(request.data.get('course_id', 0))
        selected = int(bool(request.data.get('selected', True)))
        redis = get_redis_connection("cart")
        try:
            # 判断课程是否存在
            Course.objects.get(is_delete=False, is_show=True, pk=course_id)
        except Course.DoesNotExist:
            redis.hdel(f"cart_{user_id}", course_id)
            return Response({'errmsg': '当前商品不存在或已经被下架!'})
        redis.hset(f'cart_{user_id}', course_id, selected)
        return Response({'errmsg': 'ok!'})

    def together_select(self, request):
        """全选/全不选"""
        user_id = request.user.id
        selected = int(bool(request.data.get('selected', True)))
        redis = get_redis_connection('cart')
        # 购物车所有课程
        cart_hash = redis.hgetall(f'cart_{user_id}')
        if len(cart_hash) < 1:
            return Response({"errmsg": "购物车没有任何商品。"}, status=status.HTTP_204_NO_CONTENT)

        cart_list = [int(course_id.decode()) for course_id in cart_hash]

        # 批量修改购物车中素有商品课程的勾选状态
        pipe = redis.pipeline()
        pipe.multi()
        for course_id in cart_list:
            pipe.hset(f"cart_{user_id}", course_id, selected)
        pipe.execute()

        return Response({"errmsg": "ok"})

    def delete_course(self, request):
        """购车车中删除课程"""
        user_id = request.user.id
        course_id = request.query_params.get('course_id', 0)
        redis = get_redis_connection('cart')
        redis.hdel(f'cart_{user_id}', course_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def cart_select_list(self, request):
        """获取商品勾选列表"""
        user_id = request.user.id
        redis = get_redis_connection('cart')
        cart_hash = redis.hgetall(f'cart_{user_id}')
        if len(cart_hash) < 1:
            return Response({'errmsg': '购物车没有任何商品'}, status=status.HTTP_400_BAD_REQUEST)

        # 把redis中的购物车勾选课程ID信息转换成普通列表, 即value=1
        cart_list = [int(course_id.decode()) for course_id, selected in cart_hash.items() if selected == b'1']
        course_list = Course.objects.filter(is_delete=False, is_show=True, pk__in=cart_list)

        # 把course_list进行遍历，提取课程中的信息组成列表
        data = []
        for course in course_list:
            data.append({
                "id": course.id,
                "name": course.name,
                "course_cover": course.course_cover.url,
                "price": float(course.price),
                "discount": course.discount,
                "credit": course.credit,
                "course_type": course.get_course_type_display(),
            })

        # 返回客户端
        return Response({"errmsg": "ok！", "cart": data})
