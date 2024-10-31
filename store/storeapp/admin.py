from django.contrib import admin
from .models import Product,Category,Cart,CartItem,Wishlist,WishlistItems,Order,OrderDetail
# Register your models here.

class ProductAdmin(admin.ModelAdmin):
	readonly_fields=('created_at','updated_at')

class CartItemAdmin(admin.ModelAdmin):
	readonly_fields=('created_at',)

admin.site.register(Product,ProductAdmin)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(CartItem,CartItemAdmin)
admin.site.register(Wishlist)
admin.site.register(WishlistItems)
admin.site.register(Order)
admin.site.register(OrderDetail)