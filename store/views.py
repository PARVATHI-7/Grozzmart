from django.shortcuts import render,redirect, get_object_or_404

from django.views.generic import View

from store.forms import SignUpForm,LoginForm,OrderForm,ReviewForm

from django.core.mail import send_mail

from store.models import User,Size,BasketItem,OrderItem,Order,ReviewRating,Coupon,Wishlist

from django.contrib import messages

from django.contrib.auth import authenticate,login,logout

from store.models import Product

from django.core.paginator import Paginator

from django.views.decorators.csrf import csrf_exempt

from django.utils.decorators import method_decorator

from decouple import config

from django.http import HttpResponse

from django.template.loader import render_to_string

from store.decorators import signin_required

from django.views.decorators.cache import never_cache

from .models import Wishlist

from django.contrib.auth.decorators import login_required

RZP_KEY_ID=config('RZP_KEY_ID')

RZP_KEY_SECRET=config('RZP_KEY_SECRET')


decs=[signin_required,never_cache]


def home_redirect(request):
    return redirect('/signup/')

def send_otp_phone(otp):
    from twilio.rest import Client
    account_sid = config('TWILIO_ACCOUNT_SID')
    auth_token = config('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)
    message = client.messages.create(
    from_='+17178645080',
    body=otp,
    to='+918075428796'
    )
    print(message.sid)
    
def send_otp_email(user):

    user.generate_otp()
    
    send_otp_phone(user.otp)

    subject="verify your email"

    message=f"otp for account verification is {user.otp}"

    from_email="zyraxgaming04@gmail.com"

    to_email=[user.email]
    
    try:

        send_mail(subject,message,from_email,to_email)

    except:
        
        print("failed to send email")


class SignUpView(View):
    
    template_name = 'register.html'
    form_class = SignUpForm
    
    def get(self, request, *args, **kwargs):
        
        form = self.form_class()
        
        context = {
            'form':form
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        
        form_data = request.POST
        form = self.form_class(form_data)
        
        if form.is_valid():
            
            user_obj = form.save(commit=False)
            user_obj.is_active = False
            
            user_obj.save()
            
            send_otp_email(user_obj)

            return redirect('verify-email')
        
        context = {
            'form':form
        }
        
        return render(request, self.template_name, context)
        
   
class VerifyEmailView(View):

    template_name = 'verify_email.html'
    
    def get(self, request, *args, **kwargs):
        
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        
        otp = request.POST.get('otp')
        
        try:
            user_obj = User.objects.get(otp=otp)
        
            user_obj.is_active = True
            user_obj.is_verified = True
            user_obj.otp = None
            
            user_obj.save()
            return redirect('signin')
        
        except:
            
            messages.error(request, 'Invalid OTP')
            
            return render(request, self.template_name)   
        
        
class SignInView(View):
    
    template_name="login.html"
    
    form_class=LoginForm
    
    def get(self,request,*args,**kwargs):
        
        form_instance=self.form_class()
        
        return render(request,self.template_name,{"form":form_instance})
    
    def post(self,request,*args,**kwargs):
        
        form_data=request.POST
        
        form_instance=self.form_class(form_data)
        
        if form_instance.is_valid():
            
            uname=form_instance.cleaned_data.get("username")
            
            pwd=form_instance.cleaned_data.get("password")
            
            user_object=authenticate(request,username=uname,password=pwd)
            
            if user_object:
                # Ensure the user has a wishlist
               
                
                login(request,user_object)
                
                return redirect("product-list")
            
        return render(request,self.template_name,{"form":form_instance})
                
class SignOutView(View):
    
    def get(self, request, *args, **kwargs):
        
        logout(request)
        
        return redirect('signin')                 


@method_decorator(decs,name="dispatch")
class ProductListView(View):
    
    template_name="index.html"
    
    def get(self,request,*args,**kwargs):
        
        
        qs=BasketItem.objects.filter(basket_object=request.user.cart,is_order_placed=False)

        basket_item_count=qs.count()
        
        query = request.GET.get('q')
        sort_by = request.GET.get('sort_by')
        category = request.GET.get('category')
        
        
        if query:
            products = Product.objects.filter(title__icontains=query)
        else:
            products = Product.objects.all()
        
        if category:
            products = products.filter(category_object__name__icontains=category)
        
        if sort_by:
            products = products.order_by(sort_by)
        
        paginator = Paginator(products, 8)  # Show 8 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, self.template_name, {'page_obj': page_obj, 'query': query,"basket_item_count":basket_item_count})
    
   

@method_decorator(decs,name="dispatch")
class ProductDetailView(View):
    
    template_name="product_detail.html"
    
    def get(self,request,*args,**kwargs):
        
        id=kwargs.get("pk")
        
        qs=Product.objects.get(id=id)
        
        reviews=ReviewRating.objects.filter(product=qs)
        
        aas=BasketItem.objects.filter(basket_object=request.user.cart,is_order_placed=False)

        basket_item_count=aas.count()
        
        # Check if the user has purchased the product
        has_purchased = False
        if request.user.is_authenticated:
            has_purchased = OrderItem.objects.filter(
                order_object__customer=request.user,
                product_object_id=id,
                order_object__is_paid=True
            ).exists()
            if has_purchased:
                qs.item_purchased = True
                qs.save()
       
        return render(request,self.template_name,{"product":qs,"reviews":reviews, "has_purchased": has_purchased,"basket_item_count":basket_item_count})
    

@method_decorator(decs, name="dispatch")
class AddToCartView(View):
    def post(self, request, *args, **kwargs):
        id = kwargs.get("pk")
        size = request.POST.get("size")
        quantity = int(request.POST.get("quantity"))

        product_obj = Product.objects.get(id=id)
        size_obj = Size.objects.get(name=size)
        basket_obj = request.user.cart

        # Check if the item already exists in the cart
        basket_item = BasketItem.objects.filter(
            product_object=product_obj,
            size_object=size_obj,
            basket_object=basket_obj,
            is_order_placed=False
        ).first()

        if basket_item:
            # If the item exists, check the total quantity
            total_quantity = basket_item.quantity + quantity
            if total_quantity > 5:
                messages.error(request, 'The maximum quantity for each item is 5.')
                return redirect("cart-summary")
            basket_item.quantity = total_quantity
            basket_item.save()
        else:
            # If the item does not exist, create a new basket item
            if quantity > 5:
                messages.error(request, 'The maximum quantity for each item is 5.')
                return redirect("cart-summary")
            BasketItem.objects.create(
                product_object=product_obj,
                quantity=quantity,
                size_object=size_obj,
                basket_object=basket_obj,
            )

        print("item has been added to cart")

        # Update cart item count
        basket_item_count = BasketItem.objects.filter(basket_object=request.user.cart, is_order_placed=False).count()
        request.session['basket_item_count'] = basket_item_count

        return redirect("cart-summary")
    
       


    

@method_decorator(decs,name="dispatch")
class CartSummaryView(View):

    template_name="cart_summary.html"

    def get(self,request,*args,**kwargs):
        qs=BasketItem.objects.filter(basket_object=request.user.cart,is_order_placed=False)
        basket_item_count=qs.count()
        basket_total=sum([bi.item_total for bi in qs])
        coupon_code = request.session.get('coupon_code', '')
        discount_percentage = request.session.get('discount_percentage', 0)
        discount_amount = (basket_total * discount_percentage) / 100
        total_after_discount = basket_total - discount_amount

        return render(request, self.template_name, {
            "basket_items": qs,
            "basket_total": basket_total,
            "basket_item_count": basket_item_count,
            "coupon_code": coupon_code,
            "discount_percentage": discount_percentage,
            "discount_amount": discount_amount,
            "total_after_discount": total_after_discount
        })

    def post(self, request, *args, **kwargs):
        coupon_code = request.POST.get('coupon_code')
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            discount_percentage = coupon.discount_percentage if coupon.discount_percentage is not None else 0
            request.session['coupon_code'] = coupon_code
            request.session['discount_percentage'] = float(discount_percentage)
            messages.success(request, 'Coupon applied successfully.')
        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')
            request.session['coupon_code'] = ''
            request.session['discount_percentage'] = 0

        return redirect('cart-summary')
    

@method_decorator(decs,name="dispatch")    
class ItemDeleteView(View):

    def get(self,request,*args,**kwargs):

        id=kwargs.get("pk")

        BasketItem.objects.get(id=id).delete()

        return redirect("cart-summary")




import razorpay
@method_decorator(decs,name="dispatch")
class PlaceOrderView(View):

    form_class=OrderForm

    template_name="place_order.html"

    def get(self,request,*args,**kwargs):
        qs=BasketItem.objects.filter(basket_object=request.user.cart,is_order_placed=False)
        basket_item_count=qs.count()
        total=sum([bi.item_total for bi in qs])
        coupon_code = request.session.get('coupon_code', '')
        discount_percentage = request.session.get('discount_percentage', 0)
        discount_amount = (total * discount_percentage) / 100
        total_after_discount = total - discount_amount

        form_instance=self.form_class()

        return render(request, self.template_name, {
            "form": form_instance,
            "items": qs,
            "total": total,
            "basket_item_count": basket_item_count,
            "coupon_code": coupon_code,
            "discount_percentage": discount_percentage,
            "discount_amount": discount_amount,
            "total_after_discount": total_after_discount
        })

    def post(self,request,*args,**kwargs):
        form_data=request.POST 
        form_instance=self.form_class(form_data)

        if form_instance.is_valid():
            form_instance.instance.customer=request.user
            order_instance=form_instance.save()
            basket_item=request.user.cart.cart_item.filter(is_order_placed=False)
            payment_method=form_instance.cleaned_data.get("payment_method")
            total=sum([bi.item_total for bi in basket_item])

            # Apply coupon code
            coupon_code = request.session.get('coupon_code', '')
            discount_percentage = request.session.get('discount_percentage', 0)
            discount_amount = (total * discount_percentage) / 100
            total_after_discount = total - discount_amount

            if payment_method == "COD" and total_after_discount > 2000:
                messages.error(request, 'The maximum amount for Cash on Delivery (COD) is Rs2000.')
                return render(request, self.template_name, {
                    "form": form_instance,
                    "items": basket_item,
                    "total": total,
                    "coupon_code": coupon_code,
                    "discount_percentage": discount_percentage,
                    "discount_amount": discount_amount,
                    "total_after_discount": total_after_discount
                })

            for bi in basket_item:
                OrderItem.objects.create(
                    order_object=order_instance,
                    product_object=bi.product_object,
                    quantity=bi.quantity,
                    size_object=bi.size_object,
                )
                bi.is_order_placed=True
                bi.save()

            if payment_method=="ONLINE":
                client = razorpay.Client(auth=(RZP_KEY_ID,RZP_KEY_SECRET))
                total_after_discount *= 100
                data = { "amount": total_after_discount, "currency": "INR", "receipt": "order_rcptid_11" }
                payment = client.order.create(data=data)
                print(payment)
                rzp_order_id=payment.get("id")
                order_instance.rzp_order_id=rzp_order_id
                order_instance.save()
                context={
                    "amount":total_after_discount,
                    "key_id":RZP_KEY_ID,
                    "order_id":rzp_order_id,
                    "currency":"INR"
                }
                return render(request,"payment.html",context)

        return redirect("product-list")



@method_decorator(decs,name="dispatch")
class OrderStatusView(View):

    template_name = "order_status.html"

    def get(self, request, *args, **kwargs):
        
        

        order_id = kwargs.get('order_id')

        try:
            order = Order.objects.get(id=order_id, customer=request.user)

            context = {

                'order': order,
                'order_item':order.products,
                'order_status': order.status,
                'total_amount': order.address,
            }
            return render(request, self.template_name, context)
        
        except Order.DoesNotExist:
            
            return render(request, '404.html')
        


@method_decorator(decs,name="dispatch")
class InvoiceDownloadView(View):

    def get(self, request, order_id, *args, **kwargs):

        try:
            order = get_object_or_404(Order, id=order_id, customer=request.user)

            html_invoice = render_to_string('invoice.html', {'order': order, 'order_items': order.orderitems.all()})

            response = HttpResponse(html_invoice, content_type='text/html')

            response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.html"'

            return response
        
        except Order.DoesNotExist:

            return HttpResponse("Order not found", status=404)    


    
@method_decorator([csrf_exempt],name="dispatch")
class PaymentVerificationView(View):


    def post(self,request,*args,**kwargs):

        client = razorpay.Client(auth=(RZP_KEY_ID,RZP_KEY_SECRET))

        try:
            client.utility.verify_payment_signature(request.POST)
            print("payment sucess")

            order_id=request.POST.get("razorpay_order_id")

            order_object=Order.objects.get(rzp_order_id=order_id)

            order_object.is_paid=True

            order_object.save()
            
            login(request,order_object.customer)
            
        except:
            print("payment failed")

        

        print(request.POST)

        return redirect("order-status",order_id=order_object.id)




@method_decorator(decs, name="dispatch")
class SubmitReviewView(View):

    form_class = ReviewForm

    template_name = "product_detail.html"

    def get(self, request, *args, **kwargs):

        form_instance = self.form_class()

        return render(request, self.template_name, {"form": form_instance})

    def post(self, request, *args, **kwargs):

        form_data = request.POST

        form_instance = self.form_class(form_data)

        product = get_object_or_404(Product, pk=kwargs.get("pk"))

        has_purchased = OrderItem.objects.filter(
            order_object__customer=request.user,
            product_object=product
        ).exists()

        if not has_purchased:
            messages.error(request, "You can only review products you have purchased.")

            return redirect("product-detail", pk=product.pk)

        has_reviewed = ReviewRating.objects.filter(
            product=product,
            user=request.user
        ).exists()

        if has_reviewed:
            messages.error(request, "You have already reviewed this product.")

            return redirect("product-detail", pk=product.pk)

        if form_instance.is_valid():

            review = form_instance.save(commit=False)

            review.product = product

            review.user = request.user

            review.save()

            messages.success(request, "Review added successfully.")

            return redirect("product-detail", pk=product.pk)

        messages.error(request, "Review not added.")

        return render(request, self.template_name, {"form": form_instance})

    
    
    
@method_decorator(decs,name="dispatch")
class OrderSummaryView(View):

    template_name="order_summary.html"

    def get(self,request,*args,**kwargs):
        
        Qs=BasketItem.objects.filter(basket_object=request.user.cart,is_order_placed=False)

        basket_item_count=Qs.count()

        qs=request.user.orders.all().order_by("-created_date")

        order_reviews = {}
        for order in qs:
            order_reviews[order.id] = {}
            for item in order.orderitems.all():
                reviews = ReviewRating.objects.filter(product=item.product_object)
                order_reviews[order.id][item.product_object.id] = reviews

        return render(request, self.template_name, {"orders": qs, "order_reviews": order_reviews,"basket_item_count":basket_item_count})
    


@method_decorator(csrf_exempt, name='dispatch') 

class UpdateQuantityView(View):

    def post(self, request, item_id, *args, **kwargs): 

        try:
            new_quantity = request.POST.get("quantity") 

            if new_quantity:
                new_quantity = int(new_quantity)
                if new_quantity > 5:
                    messages.error(request, 'The maximum quantity for each item is 5.')
                    return redirect('cart-summary')

                basket_item = BasketItem.objects.get(id=item_id)
                basket_item.quantity = new_quantity
                basket_item.save()

        except BasketItem.DoesNotExist:
            pass  

        return redirect('cart-summary')


@method_decorator(login_required, name='dispatch')
class WishlistView(View):
    def get(self, request, *args, **kwargs):
        Qs=BasketItem.objects.filter(basket_object=request.user.cart,is_order_placed=False)

        basket_item_count=Qs.count()
        
        wishlist_items = Wishlist.objects.filter(user=request.user)
        
        return render(request, 'wishlist.html', {'wishlist_items': wishlist_items,"basket_item_count":basket_item_count})

@method_decorator(login_required, name='dispatch')
class AddToWishlistView(View):
    def post(self, request, *args, **kwargs):
        product_id = kwargs.get('product_id')
        product = Product.objects.get(id=product_id)
        Wishlist.objects.get_or_create(user=request.user, product=product)
        return redirect('wishlist')

@method_decorator(login_required, name='dispatch')
class RemoveFromWishlistView(View):
    def post(self, request, *args, **kwargs):
        product_id = kwargs.get('product_id')
        product = Product.objects.get(id=product_id)
        Wishlist.objects.filter(user=request.user, product=product).delete()
        return redirect('wishlist')