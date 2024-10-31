from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from .models import Category,Product,Cart,CartItem,Order,OrderDetail,Wishlist,WishlistItems

from decimal import Decimal
from urllib.parse import unquote
import datetime

# Create your views here.
def home(request):
	return redirect('signin')

def signin(request):
	if request.user.is_authenticated:
		return redirect('store_app')
	if request.method=='GET':
		return render(request,'signin.html',{
		    'form': AuthenticationForm
		})
	else:
	    user = authenticate(request,username=request.POST['username'],password=request.POST['password'])
	    if user is None:
	        return render(request,'signin.html',{
	            'form': AuthenticationForm,
	            'error': 'Username or password is incorrect!'
	        })
	    else:
	        login(request,user)
	        return redirect('store_app')

def signup(request):
    if request.method=='GET':
        return render(request,'signup.html',{
            'form': UserCreationForm
        })
    else:
        if request.POST['password1']==request.POST['password2']:
            try:
                user = User.objects.create_user(username=request.POST['username'],password=request.POST['password1'])
                user.save()
                login(request,user)
                return redirect('store_app')
            except IntegrityError:
                return render(request,'signup.html',{
                    'form': UserCreationForm,
                    'error': 'Username already exists'
                })
        return render(request,'signup.html',{
            'form': UserCreationForm,
            'error': 'Passwords do not match'
        })

@login_required
def signout(request):
    logout(request)
    return redirect('home')

@login_required
def getProducts(request):
	if request.method=='GET':
		categories = Category.objects.all().order_by('category_name')
		list_categories = []
		for category in categories:
			list_categories.append(category.category_name)
		selected_category = request.GET.get('category') #al seleccionar una categoria, cambiar de pagina, deseleccionar la categoria, dar al logo StoreApp y cambiar de pagina, por alguna razon el None se castea a string
		search_by_product = request.GET.get('search')
		if selected_category=='None':
			selected_category=None
		if search_by_product and selected_category:
			products=Product.objects.filter(category=Category.objects.get(category_name=selected_category),product_name__icontains=search_by_product).values().order_by('product_name')
		elif selected_category: products=Product.objects.filter(category=Category.objects.get(category_name=selected_category)).values().order_by('product_name')
		elif search_by_product: products=Product.objects.filter(product_name__icontains=search_by_product).values().order_by('product_name')
		else: products=Product.objects.all().values()
		paginator = Paginator(products,15)
		page_number = request.GET.get('page')
		page_obj = paginator.get_page(page_number)
		cart_exists= Cart.objects.filter(user=request.user).exists()
		current_time = datetime.datetime.now() #el valor asignado al crear una instancia es ignorado si el atributo en la clase modelo tiene el parametro auto_now_add
		if cart_exists:
			for product in page_obj: #verifica que cada producto en pantalla esté o no en el carrito
				cart_instance = Cart.objects.get(user=request.user)
				wishlist_instance, created = Wishlist.objects.get_or_create(user=request.user,defaults={'created_at':current_time,'updated_at':current_time})
				product_instance = Product.objects.get(p_id=product.get('p_id'))
				product_in_cart = CartItem.objects.filter(cart=cart_instance,product=product_instance).exists()
				product['is_in_cart']=True if product_in_cart else False
				product_in_wishlist = WishlistItems.objects.filter(wishlist=wishlist_instance,product=product_instance).exists()
				product['is_in_wishlist']=True if product_in_wishlist else False
			products_in_cart,total_amount=getCart(request)
		else:
			for product in page_obj:
				product['is_in_cart']=False
			products_in_cart,total_amount=[],0
		return render(request,'store_products.html',{
			'page_obj':page_obj,
			'products_in_cart':products_in_cart,
			'list_categories':list_categories,
			'selected_category':selected_category,
			'total_amount':total_amount,
			'search_by_product':search_by_product})
	if request.method=='POST':
		if request.POST.get('make_order',None):
			products_in_cart,total_amount = getCart(request)
			if products_in_cart:
				makeOrder(request,products_in_cart,total_amount)
		if request.POST.get('product_quantity',None):
			updateQuantity(request,request.POST.get('product_id'))
		if request.POST.get('remove_cart',None):
			removeToCart(request,request.POST.get('product_id'))
		if request.POST.get('remove_wishlist',None):
			removeToWishlist(request,request.POST.get('product_id'))	
		if request.POST.get('add_cart',None):
			addToCart(request,request.POST.get('product_id'))
		if request.POST.get('add_wishlist',None):
			addToWishlist(request,request.POST.get('product_id'))
		categories = Category.objects.all().order_by('category_name')
		list_categories = []
		for category in categories:
			list_categories.append(category.category_name)
		selected_category = request.GET.get('category')
		search_by_product = request.GET.get('search')
		if selected_category=='None':
			selected_category=None
		if search_by_product and selected_category:
			products=Product.objects.filter(category=Category.objects.get(category_name=selected_category),product_name__icontains=search_by_product).values().order_by('product_name')
		elif selected_category: products=Product.objects.filter(category=Category.objects.get(category_name=selected_category)).values().order_by('product_name')
		elif search_by_product: products=Product.objects.filter(product_name__icontains=search_by_product).values().order_by('product_name')
		else: products=Product.objects.all().values()
		#products = Product.objects.filter(category=Category.objects.get(category_name=selected_category)).values().order_by('product_name') if selected_category else Product.objects.all().values().order_by('product_name')
		paginator = Paginator(products,15)
		page_number = request.GET.get('page')
		page_obj = paginator.get_page(page_number)
		cart_exists= Cart.objects.filter(user=request.user).exists()
		for product in page_obj:
			cart_instance = Cart.objects.get(user=request.user)
			wishlist_instance = Wishlist.objects.get(user=request.user)
			product_instance = Product.objects.get(p_id=product.get('p_id'))
			product_in_cart = CartItem.objects.filter(cart=cart_instance,product=product_instance).exists()
			product['is_in_cart']=True if product_in_cart else False
			product_in_wishlist = WishlistItems.objects.filter(wishlist=wishlist_instance,product=product_instance).exists()
			product['is_in_wishlist']=True if product_in_wishlist else False
		products_in_cart,total_amount=getCart(request)
		return render(request,'store_products.html',{
			'page_obj':page_obj,
			'products_in_cart':products_in_cart,
			'list_categories':list_categories,
			'selected_category':selected_category,
			'total_amount':total_amount,
			'search_by_product':search_by_product})

@login_required
def getWishlist(request):
	if request.method=='GET':
		wishlist_exists = Wishlist.objects.filter(user=request.user)
		if wishlist_exists:
			wishlist_instance = Wishlist.objects.get(user=request.user)
			products_in_wishlist = WishlistItems.objects.filter(wishlist=wishlist_instance).order_by('created_at')
		else:
			products_in_wishlist = []
		cart_exists= Cart.objects.filter(user=request.user).exists()
		products_in_wishlist_and_cart =[]
		if cart_exists:
			for product_in_wishlist in products_in_wishlist:
					cart_instance = Cart.objects.get(user=request.user)
					wishlist_instance = Wishlist.objects.get(user=request.user)
					product_instance = Product.objects.get(p_id=product_in_wishlist.product_id)
					product_in_cart = CartItem.objects.filter(cart=cart_instance,product=product_instance).exists()
					products_in_wishlist_and_cart.append((product_in_wishlist,True if product_in_cart else False))
		else:
			for product_in_wishlist in products_in_wishlist:
				products_in_wishlist_and_cart.append((product_in_wishlist,False))
		products_in_cart,total_amount=getCart(request)
		return render(request,'wishlist.html',{
			'products_in_wishlist_and_cart':products_in_wishlist_and_cart,
			'products_in_cart':products_in_cart,
			'total_amount':total_amount})
	if request.method=='POST':
		if request.POST.get('make_order',None):
			products_in_cart,total_amount = getCart(request)
			if products_in_cart:
				makeOrder(request,products_in_cart,total_amount)
		if request.POST.get('product_quantity',None):
			updateQuantity(request,request.POST.get('product_id'))
		if request.POST.get('remove_cart',None):
			removeToCart(request,request.POST.get('product_id'))
		if request.POST.get('remove_wishlist',None):
			removeToWishlist(request,request.POST.get('product_id'))	
		if request.POST.get('add_cart',None):
			addToCart(request,request.POST.get('product_id'))
		wishlist_exists = Wishlist.objects.filter(user=request.user)
		if wishlist_exists:
			wishlist_instance = Wishlist.objects.get(user=request.user)
			products_in_wishlist = WishlistItems.objects.filter(wishlist=wishlist_instance).order_by('created_at')
		else:
			products_in_wishlist = []
		cart_exists= Cart.objects.filter(user=request.user).exists()
		products_in_wishlist_and_cart =[]
		if cart_exists:
			for product_in_wishlist in products_in_wishlist:
					cart_instance = Cart.objects.get(user=request.user)
					wishlist_instance = Wishlist.objects.get(user=request.user)
					product_instance = Product.objects.get(p_id=product_in_wishlist.product_id)
					product_in_cart = CartItem.objects.filter(cart=cart_instance,product=product_instance).exists()
					products_in_wishlist_and_cart.append((product_in_wishlist,True if product_in_cart else False))
		else:
			for product_in_wishlist in products_in_wishlist:
				products_in_wishlist_and_cart.append(product_in_wishlist,False)
		products_in_cart,total_amount=getCart(request)
		return render(request,'wishlist.html',{
			'products_in_wishlist_and_cart':products_in_wishlist_and_cart,
			'products_in_cart':products_in_cart,
			'total_amount':total_amount})

@login_required
def productDetail(request,product_name):
	if request.method=='GET':
		product = get_object_or_404(Product,product_name=unquote(product_name))
		cart_exists = Cart.objects.filter(user=request.user).exists()
		if cart_exists:
			cart_instance = Cart.objects.get(user=request.user)
			wishlist_instance = Wishlist.objects.get(user=request.user)
			products_in_cart,total_amount=getCart(request)
			is_in_cart = CartItem.objects.filter(cart=cart_instance,product=product).exists()
			is_in_wishlist = WishlistItems.objects.filter(wishlist=wishlist_instance,product=product)
		else:
			products_in_cart,total_amount=[],0
			is_in_cart,is_in_wishlist=False,False
		return render(request,'product_detail.html',{
			'product':product,
			'products_in_cart':products_in_cart,
			'total_amount':total_amount,
			'is_in_cart':is_in_cart,
			'is_in_wishlist':is_in_wishlist})
	if request.method=='POST':
		if request.POST.get('make_order',None):
			products_in_cart,total_amount = getCart(request)
			if products_in_cart:
				makeOrder(request,products_in_cart,total_amount)
		if request.POST.get('product_quantity',None):
			updateQuantity(request,request.POST.get('product_id'))
		if request.POST.get('remove_cart',None):
			removeToCart(request,request.POST.get('product_id'))
		if request.POST.get('remove_wishlist',None):
			removeToWishlist(request,request.POST.get('product_id'))	
		if request.POST.get('add_cart',None):
			addToCart(request,request.POST.get('product_id'))
		if request.POST.get('add_wishlist',None):
			addToWishlist(request,request.POST.get('product_id'))
		product = get_object_or_404(Product,product_name=unquote(product_name))
		cart_exists = Cart.objects.filter(user=request.user).exists()
		if cart_exists:
			cart_instance = Cart.objects.get(user=request.user)
			wishlist_instance = Wishlist.objects.get(user=request.user)
			products_in_cart,total_amount=getCart(request)
			is_in_cart = CartItem.objects.filter(cart=cart_instance,product=product).exists()
			is_in_wishlist = WishlistItems.objects.filter(wishlist=wishlist_instance,product=product)
		else:
			products_in_cart,total_amount=[],0
			is_in_cart,is_in_wishlist=False,False
		return render(request,'product_detail.html',{
			'product':product,
			'products_in_cart':products_in_cart,
			'total_amount':total_amount,
			'is_in_cart':is_in_cart,
			'is_in_wishlist':is_in_wishlist})

@login_required
def getOrders(request):
	if request.method=='GET':
		print(request.user)
		products_in_cart,total_amount=getCart(request)
		orders= Order.objects.filter(user=request.user)
		return render(request,'orders.html',{
			'orders':orders,
			'products_in_cart':products_in_cart,
			'total_amount':total_amount})
	if request.method=='POST':
		print(request.POST)
		if request.POST.get('make_order',None):
			products_in_cart,total_amount = getCart(request)
			if products_in_cart:
				makeOrder(request,products_in_cart,total_amount)
		if request.POST.get('Cancelled',None):
			order_instance = Order.objects.get(user=request.user,id=request.POST.get('order_id'))
			order_instance.status = request.POST.get('Cancelled')
			order_instance.save()
		if request.POST.get('product_quantity',None):
			updateQuantity(request,request.POST.get('product_id'))
		if request.POST.get('remove_cart',None):
			removeToCart(request,request.POST.get('product_id'))
		orders= Order.objects.filter(user=request.user)
		products_in_cart,total_amount=getCart(request)
		return render(request,'orders.html',{
			'orders':orders,
			'products_in_cart':products_in_cart,
			'total_amount':total_amount})

@login_required
def getOrderDetail(request,id):
	order_instance = Order.objects.get(user=request.user,id=id)
	products_in_order = OrderDetail.objects.filter(order=order_instance)
	return render(request,'order_detail.html',{
		'order_instance':order_instance,
		'products_in_order':products_in_order})

@login_required
def getCart(request):
	current_time=datetime.datetime.now()
	cart_instance, created =Cart.objects.get_or_create(user=request.user,defaults={'total_amount':0,
		'created_at':current_time,'updated_at':current_time})
	products_in_cart = CartItem.objects.filter(cart=cart_instance).order_by('created_at')
	total_amount=0
	for product in products_in_cart:
		total_amount+=product.price
	return products_in_cart,total_amount

@login_required
def addToCart(request,p_id):
	product_instance = Product.objects.get(p_id=p_id)
	cart_exists = Cart.objects.filter(user=request.user).exists()
	current_time = datetime.datetime.now()
	if not cart_exists:
		cart_instance=Cart.objects.create(user=request.user,total_amount=0,created_at=current_time,
			updated_at=current_time)
	else:
		cart_instance=Cart.objects.get(user=request.user)
	cartitem_exists = CartItem.objects.filter(cart=cart_instance,product=product_instance).exists()
	if not cartitem_exists:
		CartItem.objects.create(cart=cart_instance,product=product_instance,quantity=1,
			price=product_instance.price,created_at=current_time)

@login_required
def removeToCart(request,p_id):
	cart_instance = Cart.objects.get(user=request.user)
	product_instance = Product.objects.get(p_id=p_id)
	cartitem_instance = get_object_or_404(CartItem,cart=cart_instance,product=product_instance)
	cartitem_instance.delete()

@login_required
def updateQuantity(request,p_id):
	cart_instance = Cart.objects.get(user=request.user)
	product_instance = Product.objects.get(p_id=p_id)
	cartitem_instance = get_object_or_404(CartItem,cart=cart_instance,product=product_instance)
	cartitem_instance.quantity = request.POST.get('product_quantity',1)
	cartitem_instance.price = cartitem_instance.product.price*Decimal(cartitem_instance.quantity)
	cartitem_instance.save()

@login_required
def addToWishlist(request,p_id):
	product_instance = Product.objects.get(p_id=p_id)
	current_time = datetime.datetime.now()
	wishlist_instance, created = Wishlist.objects.get_or_create(user=request.user,defaults={'created_at':current_time,'updated_at':current_time})
	WishlistItems.objects.get_or_create(wishlist=wishlist_instance,product=product_instance,created_at=current_time)

@login_required
def removeToWishlist(request,p_id):
	wishlist_instance = Wishlist.objects.get(user=request.user)
	product_instance = Product.objects.get(p_id=p_id)
	wishlistitem_instance = get_object_or_404(WishlistItems,wishlist=wishlist_instance,product=product_instance)
	wishlistitem_instance.delete()

@login_required
def makeOrder(request,products_in_cart,total_amount):
	cart_instance = Cart.objects.filter(user=request.user)
	current_time = datetime.datetime.now()
	order_instance = Order.objects.create(user=request.user,total_amount=total_amount,created_at=current_time,
		updated_at=current_time)
	for product in products_in_cart:
		product_instance = Product.objects.get(p_id=product.product_id)
		orderdetail_instance = OrderDetail.objects.create(order=order_instance,product=product_instance,
			quantity=product.quantity,price=product.quantity*product.product.price,created_at=current_time)
	cart_instance.delete()
	cart_instance, created =Cart.objects.get_or_create(user=request.user,defaults={'total_amount':0,
		'created_at':current_time,'updated_at':current_time})