from django.urls import path
from . import views



urlpatterns = [
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_page, name='register'),    
    path('', views.index, name='index'),
    
    path("dashboard/", views.dashboard, name="dashboard"),  # admin dashboard
    path("user/dashboard/", views.user_dashboard, name="user_dashboard"),  # user dashboard

    path("category/create/", views.category_create, name="category_create"),
    path("categories/", views.category_list, name="category_list"),
    path('category/update/<int:id>/', views.category_update, name='category_update'),
    path("categories/delete/<int:id>/", views.category_delete, name="category_delete"),


    path("subcategory/create/", views.subcategory_create, name="subcategory_create"),
    path("subcategory/", views.subcategory_list, name="subcategory_list"),
    path("subcategory/update/<int:id>/", views.subcategory_update, name="subcategory_update"),
    path("subcategory/delete/<int:id>/", views.subcategory_delete, name="subcategory_delete"),

    path("brand/create/", views.brand_create, name="brand_create"),
    path("brand/", views.brand_list, name="brand_list"),
    path("brand/update/<int:id>/", views.brand_update, name="brand_update"),
    path("brand/delete/<int:id>/", views.brand_delete, name="brand_delete"),

    path("product/create/", views.product_create, name="product_create"),
    path("product/", views.product_list, name="product_list"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail_admin"),
    path("product/update/<int:id>/", views.product_update, name="product_update"),
    path("product/delete/<int:id>/", views.product_delete, name="product_delete"),


    path("product/<int:product_id>/images/", views.product_image_list, name="product_image_list"),
    path("product/image/<int:id>/primary/", views.product_image_make_primary, name="product_image_make_primary"),
    path("product/image/<int:id>/delete/", views.product_image_delete, name="product_image_delete"),

    path("product/<int:product_id>/attributes/", views.attribute_list, name="attribute_list"),
    path("product/<int:product_id>/attributes/add/", views.attribute_add, name="attribute_add"),
    path("product/attribute/<int:id>/update/", views.attribute_update, name="attribute_update"),
    path("product/attribute/<int:id>/delete/", views.attribute_delete, name="attribute_delete"),

    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),

    path("users/", views.user_list, name="user_list"),
    path("users/<int:pk>/", views.user_detail, name="user_detail"),
    path("users/<int:pk>/delete/", views.user_delete, name="user_delete"),


    path('homepage/sections/', views.homepage_sections_manage, name='homepage_sections_manage'),
    path('homepage/section/<int:section_id>/add-product/', views.homepage_section_add_product, name='homepage_section_add_product'),
    path('homepage/product/<int:hp_id>/remove/', views.homepage_product_remove, name='homepage_product_remove'),
    path('homepage/section/<int:section_id>/toggle/', views.homepage_section_toggle, name='homepage_section_toggle'),
    path('homepage/section/<int:section_id>/categories/',views.homepage_section_update_categories,name='homepage_section_update_categories'),


    path("coupons/", views.coupon_list, name="coupon_list"),
    path("coupons/create/", views.coupon_create, name="coupon_create"),
    path("coupons/update/<int:id>/", views.coupon_update, name="coupon_update"),
    path("coupons/delete/<int:id>/", views.coupon_delete, name="coupon_delete"),


    

]
