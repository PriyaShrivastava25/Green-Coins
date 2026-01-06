
from django.urls import path,include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_page, name='login'),
    path('signup/', views.signup_page, name='signup'),
    path('signup/success/', views.signup_success, name='signup_success'),
    path('check-email/', views.check_email, name='check-email'),
    path('submit-proof/', views.submit_proof, name='submit_proof'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),  
    path('resubmit/<int:submission_id>/', views.resubmit_proof, name='resubmit_proof'),
    path('reward/', views.reward, name='reward'),
    path('redeem/', views.redeem_reward, name='redeem_reward'),
    path('awareness/', views.awareness_page, name='awareness'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('tree/', include('tree_recommend.urls')),
]