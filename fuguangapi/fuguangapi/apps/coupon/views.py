from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import constants
from .services import get_user_enable_coupon_list


class CouponListAPIView(APIView):
    """
    获取优惠券列表
    """
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        """
        获取优惠券列表
        :param request:
        :return:
        """
        user_id = request.user.id
        # 获取用户拥有的所有优惠券
        # coupon_data = get_user_coupon_list(user_id)
        # 获取用户拥有的所有可用优惠券
        coupon_data = get_user_enable_coupon_list(user_id)
        # 获取购物车中的勾选商品[与优惠券的适用范围进行比对，找出本次下单能用的优惠券]
        return Response({
            "errmsg": "ok",
            'has_credit': request.user.credit,
            'credit_to_money': constants.CREDIT_TO_MONEY,
            "coupon_list": coupon_data
        })
