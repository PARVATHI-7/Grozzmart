from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from random import randint

class User(AbstractUser):

    is_verified=models.BooleanField(default=False)

    otp=models.CharField(max_length=5,null=True,blank=True)
    
    phone=models.CharField(max_length=10,null=True)

    def generate_otp(self):

        self.otp=str(randint(1000,9999))+str(self.id)

        self.save()

class BaseModel(models.Model):

    created_date=models.DateTimeField(auto_now_add=True)

    updated_date=models.DateTimeField(auto_now=True)

    is_active=models.BooleanField(default=True)



class Brand(BaseModel):

    name=models.CharField(max_length=200)

    def __str__(self):

        return self.name


class Size(BaseModel):

    name=models.CharField(max_length=200)

    def __str__(self):
        return self.name
    


class Category(BaseModel):

    name=models.CharField(max_length=200)

    def __str__(self):
        return self.name
    


class Product(BaseModel):

    title=models.CharField(max_length=200)

    description=models.TextField()

    price=models.PositiveIntegerField()
    
    manufacturer=models.CharField(max_length=100)

    picture=models.ImageField(upload_to="product_images",null=True,blank=True)

    brand_object=models.ForeignKey(Brand,on_delete=models.CASCADE)

    category_object=models.ForeignKey(Category,on_delete=models.CASCADE)

    size_objects=models.ManyToManyField(Size)
    
    item_purchased = models.BooleanField(default=False)




    def __str__(self):

        return self.title
    
    
class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject  


class Basket(BaseModel):

    owner=models.OneToOneField(User,on_delete=models.CASCADE,related_name="cart")


# Query to fetch basket of authenticated user

# Basket.objects.get(owner=request.user)

# request.user.cart.all()


class BasketItem(BaseModel):

    product_object=models.ForeignKey(Product,on_delete=models.CASCADE)

    quantity=models.PositiveIntegerField(default=1)

    size_object=models.ForeignKey(Size,on_delete=models.CASCADE)
    

    is_order_placed=models.BooleanField(default=False)

    basket_object=models.ForeignKey(Basket,on_delete=models.CASCADE,related_name="cart_item")
    
    @property
    def item_total(self):
        
        return self.product_object.price*self.quantity
    
    
class Order(BaseModel):
    
    ORDER_STATUS = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
    )

    products = models.ForeignKey(Product, on_delete=models.CASCADE,null=True)

    customer=models.ForeignKey(User,on_delete=models.CASCADE,related_name="orders")

    address=models.TextField()

    phone=models.CharField(max_length=20)

    PAYMENT_OPTIONS=(
        ("COD","COD"),
        ("ONLINE","ONLINE")
    )

    payment_method=models.CharField(max_length=15,choices=PAYMENT_OPTIONS,default="COD")

    rzp_order_id=models.CharField(max_length=100,null=True)

    is_paid=models.BooleanField(default=False)
    
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='PENDING')
    
    
    @property
    def order_total(self):
        
        total=sum([oi.item_total for oi in self.orderitems.all()])

        return total
    
class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.FloatField(null=True, blank=True)  
    is_active = models.BooleanField(default=True)
    
 

    def __str__(self):
        return self.code
    
    

class OrderItem(BaseModel):

    order_object=models.ForeignKey(
                                   Order,on_delete=models.CASCADE,
                                   related_name="orderitems"
                                   )
    
    product_object=models.ForeignKey(Product,on_delete=models.CASCADE)

    quantity=models.PositiveIntegerField(default=1)

    size_object=models.ForeignKey(Size,on_delete=models.CASCADE)
    
    image_object=models.ImageField(upload_to="product_images",null=True,blank=True)
    
    coupon_object=models.ForeignKey(Coupon,on_delete=models.CASCADE,null=True,blank=True)
        

    
    @property
    def item_total(self):
        
        return self.product_object.price*self.quantity̦



def create_basket(sender,instance,created,**kwargs):

    if created:

        Basket.objects.create(owner=instance)

post_save.connect(create_basket,User)


        
        
class ReviewRating(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    subject = models.CharField(max_length=100, blank=True)

    review = models.TextField(max_length=500, blank=True)

    rating = models.FloatField()

    status = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


