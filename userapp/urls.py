# userapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="user_home"),
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.about_view, name='about'),
    path('services/', views.service_view, name='services'),



    path("profile/", views.my_profile, name="profile"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path('search-results/', views.product_search, name='product_search_user'),
    path('category/<slug:slug>/', views.category_products_no_login, name='category_products_no_login'),
    path('category/<slug:slug>/products', views.category_products, name='category_products'),
    path("cart/add/<int:id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/", views.view_cart, name="view_cart"),
    path('cart/data/', views.view_cart, name='cart_data'),
    path("checkout/", views.checkout, name="checkout"),
    path("order/success/", views.payment_success, name="order_success"),
    path("orders/", views.order_history, name="order_history"),  # ✅ Correct function linked
    # userapp/urls.py
    path("orders/<int:pk>/", views.user_order_detail, name="user_order_detail"),

    path('user/cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('products/', views.all_products, name='all_products'),

    
    path("address/create/", views.address_create, name="address_create"),
    path("address/update/<int:id>/", views.address_update, name="address_update"),
    path("address/delete/<int:id>/", views.address_delete, name="address_delete"),

    path('search/', views.product_search_no_login, name='product_search_no_login'),
    path('review/delete/<int:review_id>/', views.delete_review, name='delete_review'),


    path('product/<slug:slug>/detail', views.product_detail_no_login, name='product_detail_no_login'),
    path("cart/apply-coupon/", views.apply_coupon, name="apply_coupon"),
    path("cart/remove-coupon/", views.remove_coupon, name="remove_coupon"),  # ✅ ADD THIS

    

]
