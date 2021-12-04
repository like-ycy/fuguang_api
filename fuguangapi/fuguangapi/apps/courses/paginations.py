from rest_framework.pagination import PageNumberPagination


class CourseListPageNumberPagination(PageNumberPagination):
    """课程信息列表分页器"""
    page_size = 5
    page_size_query_param = 'size'
    page_query_param = 'page'
    max_page_size = 20
