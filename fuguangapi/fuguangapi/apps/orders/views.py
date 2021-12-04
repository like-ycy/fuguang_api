import logging

from django.db import transaction
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from coupon.services import add_coupon_to_redis
from .models import Order
from .paginations import OrderListPageNumberPagination
from .serializers import OrderModelSerializer, OrderListModelSerializer


class OrderCreateAPIView(CreateAPIView):
    """创建订单"""
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderModelSerializer


class OrderPayChoicesAPIView(APIView):
    """前端订单管理页面，支付状态的展示"""

    def get(self, request):
        return Response(Order.status_choices)


class OrderListAPIView(ListAPIView):
    """订单列表视图类"""
    permission_classes = [IsAuthenticated]
    serializer_class = OrderListModelSerializer
    pagination_class = OrderListPageNumberPagination

    def get_queryset(self):
        user = self.request.user
        query = Order.objects.filter(user=user, is_show=True, is_delete=False)
        order_status = int(self.request.query_params.get('order_status', -1))
        status_list = [item[0] for item in Order.status_choices]
        if order_status in status_list:
            query = query.filter(order_status=order_status)
        return query.order_by('-id')


class OrderViewSet(ViewSet):
    """订单管理视图集"""
    permission_classes = [IsAuthenticated]

    def pay_cancel(self, request, pk):
        """取消订单"""
        try:
            order = Order.objects.get(pk=pk, order_status=0)
        except:
            return Response({'errmsg': '订单不存在'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            save_id = transaction.savepoint()
            try:
                # 1. 查询当前订单是否使用了积分，如果有则恢复
                if order.credit > 0:
                    order.user.credit += order.credit
                    order.user.save()
                # 2. 查询当前订单是否使用了优惠券，如果有则恢复
                obj = order.to_coupon.first()
                if obj:
                    add_coupon_to_redis(obj)
                # 3. 更新订单状态
                order.order_status = 2
                order.save()

                return Response({"errmsg": "当前订单已取消！"})

            except Exception as e:
                logging.error(f"订单无法取消！发生未知错误！{e}")
                transaction.savepoint_rollback(save_id)
                return Response({"errmsg": "当前订单取消失败！"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
