from django.contrib import admin

from store.models import Brand,Size,Category,Product,User,Coupon

# Register your models here.

admin.site.register(Brand)
admin.site.register(Size)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(User)
admin.site.register(Coupon)
