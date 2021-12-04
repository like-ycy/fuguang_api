import logging
from datetime import datetime

from django.db import transaction
from django.http.response import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from alipaysdk import AliPaySDK
from coupon.models import CouponLog
from courses.serializers import CourseModelSerializer
from orders.models import Order
from users.models import UserCourse, Credit

logger = logging.getLogger("django")


class AliPayAPIViewSet(ViewSet):
    """支付宝接口"""

    def link(self, request, order_number):
        """生成支付宝支付链接信息"""
        # 订单号
        try:
            order = Order.objects.get(order_number=order_number)
            # 订单存在查看是否已支付， 0 已支付
            if order.order_status > 0:
                return Response({'errmsg': '订单已支付'})
        except Order.DoesNotExist:
            return Response({'errmsg': '订单不存在'})

        alipay = AliPaySDK()

        # 拼接完整的支付链接
        link = alipay.page_pay(order_number, order.real_price, order.name)
        return Response({
            "pay_type": 0,
            "get_pay_type_display": "支付宝",
            "link": link
        })

    def return_result(self, request):
        """支付宝支付结果的同步通知处理"""
        data = request.query_params.dict()  # QueryDict
        alipay = AliPaySDK()
        success = alipay.check_sign(data)
        if not success:
            return Response({"errmsg": "通知通知教研失败！"}, status=status.HTTP_400_BAD_REQUEST)

        order_number = data.get("out_trade_no")

        try:
            order = Order.objects.get(order_number=order_number)
            if order.order_status > 1:
                return Response({"errmsg": "订单超时或已取消！"}, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            return Response({"errmsg": "订单不存在！"}, status=status.HTTP_400_BAD_REQUEST)

        # 获取当前订单相关的课程信息，用于返回给客户端
        order_courses = order.order_courses.all()
        course_list = [item.course for item in order_courses]
        courses_list = []
        for course in course_list:
            courses_list.append(UserCourse(course=course, user=order.user))

        if order.order_status == 0:
            # 根据订单号到支付宝查询当前订单的支付状态
            result = alipay.query(order_number)
            if result.get("trade_status", None) in ["TRADE_FINISHED", "TRADE_SUCCESS"]:
                """支付成功"""
                with transaction.atomic():
                    save_id = transaction.savepoint()
                    try:
                        now_time = datetime.now()

                        # 1. 修改订单状态
                        order.order_status = 1
                        order.pay_time = now_time
                        order.save()
                        # 2. 扣除个人积分
                        if order.credit > 0:
                            Credit.objects.create(operation=1, number=order.credit, user=order.user)

                        # 3. 如果有使用了优惠券, 修改优惠券的使用记录
                        coupon_log = CouponLog.objects.filter(order=order).first()
                        if coupon_log:
                            coupon_log.use_time = now_time
                            coupon_log.use_status = 1  # 1 表示已使用
                            coupon_log.save()

                        # 4. 用户和课程的关系绑定
                        UserCourse.objects.bulk_create(courses_list)

                        # todo 4. 取消订单超时

                    except Exception as e:
                        logger.error(f"订单支付处理同步结果发生未知错误：{e}")
                        transaction.savepoint_rollback(save_id)
                        return Response({"errmsg": "当前订单支付未完成！请联系客服工作人员！"},
                                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # 返回客户端结果
        serializer = CourseModelSerializer(course_list, many=True)
        return Response({
            "pay_time": order.pay_time.strftime("%Y-%m-%d %H:%M:%S"),
            "real_price": float(order.real_price),
            "course_list": serializer.data
        })

    def query(self, request, order_number):
        """主动查询订单支付的支付结果"""
        try:
            order = Order.objects.get(order_number=order_number)
            if order.order_status > 1:
                return Response({"errmsg": "订单超时或已取消！"}, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            return Response({"errmsg": "订单不存在！"}, status=status.HTTP_400_BAD_REQUEST)

        # 获取当前订单相关的课程信息，用于返回给客户端
        order_courses = order.order_courses.all()
        course_list = [item.course for item in order_courses]
        courses_list = []
        for course in course_list:
            courses_list.append(UserCourse(course=course, user=order.user))

        if order.order_status == 0:
            alipay = AliPaySDK()
            # 根据订单号到支付宝查询当前订单的支付状态
            result = alipay.query(order_number)
            if result.get("trade_status", None) in ["TRADE_FINISHED", "TRADE_SUCCESS"]:
                """支付成功"""
                with transaction.atomic():
                    save_id = transaction.savepoint()
                    try:
                        now_time = datetime.now()

                        # 1. 修改订单状态
                        order.order_status = 1
                        order.pay_time = now_time
                        order.save()
                        # 2. 扣除个人积分
                        if order.credit > 0:
                            Credit.objects.create(operation=1, number=order.credit, user=order.user)

                        # 3. 如果有使用了优惠券, 修改优惠券的使用记录
                        coupon_log = CouponLog.objects.filter(order=order).first()
                        if coupon_log:
                            coupon_log.use_time = now_time
                            coupon_log.use_status = 1  # 1 表示已使用
                            coupon_log.save()

                        # 4. 用户和课程的关系绑定
                        UserCourse.objects.bulk_create(courses_list)

                        # todo 4. 取消订单超时

                    except Exception as e:
                        logger.error(f"订单支付处理同步结果发生未知错误：{e}")
                        transaction.savepoint_rollback(save_id)
                        return Response({"errmsg": "当前订单支付未完成！请联系客服工作人员！"},
                                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                """当前订单未支付"""
                return Response({"errmsg": "当前订单未支付！"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"errmsg": "当前订单已支付！"})

    def notify_result(self, request):
        """支付宝支付结果的异步通知处理"""
        data = request.data  # 接受来自支付宝平台的异步通知结果
        alipay = AliPaySDK()
        success = alipay.check_sign(data)
        if not success:
            # 因为是属于异步处理，这个过程无法通过终端调试，因此，需要把支付发送过来的结果，记录到日志中。
            logger.error(f"[支付宝]>> 异步通知结果验证失败：{data}")
            return HttpResponse("fail")

        if data["trade_status"] not in ["TRADE_FINISHED", "TRADE_SUCCESS"]:
            return HttpResponse("fail")

        order_number = data.get("out_trade_no")
        try:
            order = Order.objects.get(order_number=order_number)
            if order.order_status > 1:
                return HttpResponse("fail")
        except Order.DoesNotExist:
            return HttpResponse("fail")

        # 如果已经支付完成，则不需要继续往下处理
        if order.order_status == 1:
            return HttpResponse("success")

        # 获取当前订单相关的课程信息
        order_courses = order.order_courses.all()
        course_list = [item.course for item in order_courses]
        courses_list = []
        for course in course_list:
            courses_list.append(UserCourse(course=course, user=order.user))

        """支付成功"""
        with transaction.atomic():
            save_id = transaction.savepoint()
            try:
                now_time = datetime.now()

                # 1. 修改订单状态
                order.order_status = 1
                order.pay_time = now_time
                order.save()
                # 2. 扣除个人积分
                if order.credit > 0:
                    Credit.objects.create(operation=1, number=order.credit, user=order.user)

                # 3. 如果有使用了优惠券, 修改优惠券的使用记录
                coupon_log = CouponLog.objects.filter(order=order).first()
                if coupon_log:
                    coupon_log.use_time = now_time
                    coupon_log.use_status = 1  # 1 表示已使用
                    coupon_log.save()

                # 4. 用户和课程的关系绑定
                UserCourse.objects.bulk_create(courses_list)

                # todo 4. 取消订单超时

                return HttpResponse("success")

            except Exception as e:
                logger.error(f"订单支付处理同步结果发生未知错误：{e}")
                transaction.savepoint_rollback(save_id)
                return HttpResponse("fail")
