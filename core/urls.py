from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('buy/', views.buy, name='buy'),
    path('rent/', views.rent, name='rent'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/<str:type>/<int:id>/', views.order_success, name='order_success'),
    path('service-request/', views.service_request, name='service_request'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('api/admin/delete/<str:type>/<int:id>/', views.api_delete_record, name='api_delete_record'),
    path('api/admin/laptop/', views.api_manage_laptop, name='api_manage_laptop'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('invoice/<str:type>/<int:id>/', views.invoice, name='invoice'),
    path('download-invoice/<str:type>/<int:id>/', views.download_invoice, name='download_invoice'),
    path('management/user-activity/<int:user_id>/', views.user_activity, name='user_activity'),
    path('management/admin-login/', views.admin_login_view, name='admin_login'),
    path('track/<str:type>/<int:id>/', views.track_order, name='track_order'),
    path('api/admin/track/update/', views.api_update_tracking, name='api_update_tracking'),
    path('logout/', views.logout_view, name='logout'),
    # Cart System
    path('cart/add/<int:laptop_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_qty, name='update_cart_qty'),
    # Order Cancellation
    path('order/cancel/<str:type>/<int:id>/', views.cancel_order, name='cancel_order'),
]
