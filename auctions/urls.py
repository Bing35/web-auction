from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('index/<str:setting>', views.index, name='index'),
    path('index/<str:setting>/<str:category>', views.index, name='index'),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path('create', views.create, name='create'),
    path('listing/<int:id>', views.listing, name='listing'),
    path('listing/<int:id>/<str:message>', views.listing, name='listing'),
    path('watchList', views.watchList, name='watchList'),
    path('comments', views.comments, name='comments'),
    path('close', views.close, name='close'),
    path('categories', views.categories, name='categories')
]
