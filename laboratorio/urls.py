from django.urls import path
from . import views

# for use in 'app_name:route_name'
app_name = "lab"

# the <int> secures that if the value is found is parse to int
# you have to parse url queries manually
urlpatterns = [
    path("", views.IndexView.as_view(), name="inicio"),
    path("lista/", views.LabList.as_view(), name="labs"),
    path("change-list/", views.change_table, name="other-list"),
    path("login/", views.log_user_in, name="login"),
    path("logout/", views.LogOutView.as_view(), name="logout"),
    path("register/", views.new_user, name="register"),
    path("add/<int:tabla>/", views.create_entry, name="add"),
    path("delete/<int:tabla>/<int:pk>/", views.delete_entry, name="delete"),
    path("update/<int:tabla>/<int:pk>/", views.update_entry, name="update"),
    path("csv/<int:tabla>/", views.get_csv, name="get-csv"),
    path("details/<int:pk>/", views.ProductView.as_view(), name="detail"),
    path("cart/<str:username>/", views.UserCartView.as_view(), name="cart"),
    path("add-to-cart/<int:pk>/", views.add_to_cart, name="add-cart"),
    path("delist-cart-item/<int:pk>/", views.delete_cart_item, name="delist"),
    path("perfil/<str:username>/", views.user_profile, name="profile"),
    path("delete-profile/<str:username>/", views.delete_profile, name="del-user"),
]

# TODO add the extra routes for adding product to the current user whe he bougths
# only disscount the prodcut from the stock when the user has it on its cart
# 
