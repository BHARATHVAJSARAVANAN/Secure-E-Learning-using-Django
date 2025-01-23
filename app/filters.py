import django_filters
from django_filters.filters import CharFilter
from app.models import LearningResource
class LearningResourceFilter(django_filters.FilterSet):
    course_title = CharFilter(lookup_expr='icontains')
    class Meta:
        model = LearningResource
        fields = ["course_title"]
        # fields = ['course_title', 'other_field']
        