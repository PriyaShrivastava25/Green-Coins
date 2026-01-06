from django.urls import path
from . import views

urlpatterns = [
    path('recommend/', views.recommend_trees, name='recommend_trees'),
]
