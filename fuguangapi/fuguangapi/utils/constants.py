"""
常量配置文件
"""

# 导航位置->头部
NAV_HEADER = 0

# 导航位置->脚部
NAV_FOOTER = 1

# 头部导航的显示数量
NAV_HEADER_SIZE = 7

# 脚部导航的显示数量
NAV_FOOTER_SIZE = 7

# 轮播广告的显示数量
BANNER_SIZE = 10

# 通用列表的缓存时间，单位：秒
LIST_PAGE_CACHE_TIME = 60 * 60 * 24

# 默认头像
DEFAULT_USER_AVATAR = "avatar/2021/avatar.jpg"

# 设置热门搜索关键字在redis中的key前缀名称
DEFAULT_HOT_WORD = "hot_word"

# 设置返回的热门搜索关键字的数量
HOT_WORD_LENGTH = 5

# 设置热门搜索关键字的有效期时间[单位：天]
HOT_WORD_EXPIRE = 7

# 积分抵扣现金的比例，n积分:1元
CREDIT_TO_MONEY = 10

# 设置订单超时超时的时间[单位: 秒]
ORDER_TIMEOUT = 15 * 60
