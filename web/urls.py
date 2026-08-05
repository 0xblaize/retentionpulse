from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/analyze/", views.analyze, name="analyze"),
    path("api/auth/session/", views.auth_session, name="auth-session"),
    path("api/auth/logout/", views.auth_logout, name="auth-logout"),
    path("api/auth/passkey/register/options/", views.passkey_register_options, name="passkey-register-options"),
    path("api/auth/passkey/register/verify/", views.passkey_register_verify, name="passkey-register-verify"),
    path("api/auth/passkey/authenticate/options/", views.passkey_auth_options, name="passkey-auth-options"),
    path("api/auth/passkey/authenticate/verify/", views.passkey_auth_verify, name="passkey-auth-verify"),
    path("api/analyze/", views.analyze_api, name="analyze-api"),
]
