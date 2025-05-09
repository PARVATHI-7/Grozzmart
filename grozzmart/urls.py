"""
URL configuration for FreshMart project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from store import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_redirect),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('verify/email/', views.VerifyEmailView.as_view(), name='verify-email'),
    path("signin/",views.SignInView.as_view(),name="signin"),
    path('signout/', views.SignOutView.as_view(), name='signout'),
    path('index/',views.ProductListView.as_view(),name="product-list"),
    path('product/<int:pk>/',views.ProductDetailView.as_view(),name="product-detail"),
    path('submit_review/<int:product_id>/', views.SubmitReviewView.as_view(), name='submit_review'),
    path('products/<int:pk>/cart/add/',views.AddToCartView.as_view(),name="addtocart"),
    path('cart/sumary/',views.CartSummaryView.as_view(),name="cart-summary"),
    path('cart/<int:pk>/summary/remove/',views.ItemDeleteView.as_view(),name="item-remove"),
    path('order',views.PlaceOrderView.as_view(),name="placeorder"),
    path('payment/verify/',views.PaymentVerificationView.as_view(),name="payment-verify"),
    path('order-status/<int:order_id>/',views.OrderStatusView.as_view(), name='order-status'),
    path('download-invoice/<int:order_id>/',views.InvoiceDownloadView.as_view(), name='download-invoice'),
    path('submit-review/<int:pk>/',views.SubmitReviewView.as_view(),name='submit_review'),
    path('order/summary/',views.OrderSummaryView.as_view(),name="order-summary"),
    path('update-quantity/<int:item_id>/',views.UpdateQuantityView.as_view(), name='update-quantity'),
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.AddToWishlistView.as_view(), name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.RemoveFromWishlistView.as_view(), name='remove_from_wishlist'),
    
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)