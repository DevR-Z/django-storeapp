from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.
class Category(models.Model):
	category_name = models.CharField(max_length=100)

	def __str__(self):
		return self.category_name

class Product(models.Model):
	p_id = models.CharField(max_length=100,primary_key=True) 
	product_name = models.TextField()
	category  = models.ForeignKey(Category,on_delete=models.CASCADE)
	price = models.DecimalField(max_digits=10,decimal_places=2)
	image_url = models.CharField(max_length=255)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.product_name}: s/{self.price}"

class Order(models.Model):
	STATUS_CHOICES = [
		('Pending','Pending'),
		('In Stand','In Stand'),
		('Delivered','Delivered'),
		('Cancelled','Cancelled')]

	user = models.ForeignKey(User,on_delete=models.CASCADE)
	total_amount = models.DecimalField(max_digits=10, decimal_places=2)
	status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='Pending')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Order {self.id} by {self.user.username}"

class OrderDetail(models.Model):
	order = models.ForeignKey(Order,on_delete=models.CASCADE)
	product = models.ForeignKey(Product,on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField()
	price = models.DecimalField(max_digits=10, decimal_places=2)
	created_at = models.DateTimeField() #tomara la fecha cuando se añadio al carrito

	def __str__(self):
		return f"Order {self.order.id} by {self.order.user.username}: {self.quantity} {self.product.product_name}"

class Wishlist(models.Model):
	user = models.ForeignKey(User,on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Wishlist {self.id} by {self.user.username}"

class WishlistItems(models.Model):
	wishlist = models.ForeignKey(Wishlist,on_delete=models.CASCADE)
	product = models.ForeignKey(Product,on_delete=models.CASCADE)
	created_at = models.DateTimeField(default=timezone.now)

	def __str__(self):
		return f"Wishlist {self.wishlist.id} by {self.wishlist.user.username}: {self.product.product_name}"

class Cart(models.Model):
	user = models.ForeignKey(User,on_delete=models.CASCADE)
	total_amount = models.DecimalField(max_digits=10, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Cart {self.id} by {self.user.username}"

class CartItem(models.Model):
	cart = models.ForeignKey(Cart,on_delete=models.CASCADE)
	product = models.ForeignKey(Product,on_delete=models.CASCADE)
	quantity = models.IntegerField()
	price = models.DecimalField(max_digits=10, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Cart {self.cart.id} by {self.cart.user.username}: {self.quantity} {self.product.product_name}"


