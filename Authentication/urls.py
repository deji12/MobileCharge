from django.urls import path, include
from . import views

urlpatterns = [
    path('signup/', views.Register),
    path('token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', views.MyTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.Logout, name='logout_user'),
    path('password-reset/request/', views.RequestResetCode, name='request_reset_code'),
    path('verify-reset-code/', views.VerifyResetCode, name='verify_reset_code'),
    path('reset-password/', views.ResetPassword, name='reset_password'),
    path('update-profile/', views.ProfileSetting, name='profile_setting'),
    path('get-user-info/', views.GetUserInfo, name='get_user_info'),
]