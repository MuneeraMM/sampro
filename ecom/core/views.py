
from http.client import HTTPResponse
from itertools import product

from urllib import response
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.shortcuts import render,redirect
from core.forms import *
from core.models import *
from django.utils import timezone


    # auth=(settings.RAZORPAY_ID, settings.RAZORPAY_SECRET))

# from django.views.decorators.csrf import csrf_exempt

# Create your views here.
def index(request):
    # to get all products from database table
    products = Product.objects.all()
    return render(request,"core/index.html",{'products':products})
    
def add_product(request):
    if request.method == 'POST':
        form=ProductForm(request.POST,request.FILES)
        if form.is_valid():
            print("True")
            form.save()
    
            print("Data saved successfully")
            messages.success(request,"Product added successfully")
            return redirect('/')
        else:
            print("Not working")
            messages.info(request,"Product is not added, try again")
    else:
        print("form not valid")
        form = ProductForm()
    return render(request, "core/add_product.html", {'form':form})

def product_desc(request,pk):
    # Get that particular product of id = pk
    product = Product.objects.get(pk=pk)
    return render(request,'core/product_desc.html',{'product':product})

def add_to_cart(request,pk):
    # Get that particular product of id = pk
    product = Product.objects.get(pk=pk)
    # Create Order item
    order_item, created = OrderItem.objects.get_or_create(
        product = product,
        user = request.user,
        ordered = False,
    )

    # Get query set of order object of particular user
    order_qs = Order.objects.filter(user=request.user,ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk = pk).exists():
            order_item.quantity +=1
            order_item.save()
            messages.info(request,"Added quantity item")
            return redirect("product_desc",pk=pk)
        else:
            order.items.add(order_item)
            messages.info(request,"Item added to cart")
            return redirect("product_desc",pk=pk)
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user,ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request,"Item added to cart")
        return redirect("product_desc",pk=pk)

def orderlist(request):
    if Order.objects.filter(user=request.user,ordered=False).exists():
        order = Order.objects.get(user = request.user,ordered=False)
        return render(request,'core/orderlist.html',{'order':order})
    return render(request,'core/orderlist.html',{'message':"Your cart is empty"})

def add_item(request,pk):
    # Get that particular product of id = pk
    product = Product.objects.get(pk=pk)
    # Create Order item
    order_item, created = OrderItem.objects.get_or_create(
        product = product,
        user = request.user,
        ordered = False,
    )

    # Get query set of order object of particular user
    order_qs = Order.objects.filter(user=request.user,ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk = pk).exists():
            if order_item.quantity < product.product_available_count:
                order_item.quantity +=1
                order_item.save()
                messages.info(request,"Added quantity item")
                return redirect("orderlist")
            else:
                messages.info(request,"Sorry! Product is out of stock")
                return redirect("orderlist")
        else:
            order.items.add(order_item)
            messages.info(request,"Item added to cart")
            return redirect("product_desc",pk=pk)
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user,ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request,"Item added to cart")
        return redirect("product_desc",pk=pk)

def remove_item(request,pk):
    item = get_object_or_404(Product,pk=pk)
    order_qs = Order.objects.filter(
        user = request.user,
        ordered = False,
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk=pk).exists():
            order_item = OrderItem.objects.filter(
                product=item,
                user = request.user,
                ordered = False,
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order_item.delete()
            messages.info(request,"Item quantity was updated")
            return redirect("orderlist")
        else:
            messages.info(request,"This item is not in your cart")
            return redirect("orderlist")
    else:
        messages.info(request,"You do not have any order")
        return redirect("orderlist")

def checkout_page(request):
    if CheckoutAddress.objects.filter(user=request.user).exists():
        return render(request, 'core/checkout_address.html',{'payment_allow':"allow"})
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        try:
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip_code = form.cleaned_data.get('zip')
                checkout_address = CheckoutAddress(
                    user = request.user,
                    street_address = street_address,
                    apartment_address = apartment_address,
                    country = country,
                    zip_code= zip_code,
                )
                checkout_address.save()
                print("It should render the summary page")
                return render(request, 'core/checkout_address.html',{'payment_allow':"allow"})
        except Exception as e:
            messages.warning(request, "Failed checkout")
            return redirect('checkout_page')
    else:
        form = CheckoutForm()
        return render(request, 'core/checkout_address.html', {'form': form})

def payment(request):
    # if request.method == "POST":
        try:
            order = Order.objects.get(user=request.user, ordered=False)
            address = CheckoutAddress.objects.get(user=request.user)
            order_amount = order.get_total_price()
            order_currency = "INR"


            order_receipt = order.order_id
            notes = {
                "street_address" : address.street_address,
                "apartment_address" : address.apartment_address,
                "country" : address.country.name,
                "zip" : address.zip_code,
                }
            razorpay_order = razorpay_client.order.create(dict(
                amount=order_amount *100,
                currency=order_currency,
                receipt=order_receipt,
                notes=notes,
                payment_capture="0"
            ))

            print(razorpay_order["id"])
            order.razorpay_order_id = razorpay_order["id"]
            order.save()
            
            print("It should render the summary page")
            return render(request, "core/paymentsummaryrazorpay.html",
                {
                    "order" : order,
                    "order_id" : razorpay_order["id"],
                    "orderId" : order.order_id,
                    "final_price" : order_amount,
                    "razorpay_merchant_id" : settings.RAZORPAY_ID,
                },
            )
        except Order.DoesNotExist:
                print("Order not found")
                return HTTPResponse("404 Error")

#Adding payment gateway
import razorpay
from django.conf import settings
# authorize razorpay client with API Keys.
# razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_ID, settings.RAZORPAY_SECRET))
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_ID, settings.RAZORPAY_SECRET))
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def handlerequest(request):
    
    # this handle request only for taking data from the razorpay dashboard.
    if request.method == "POST":
        try:
            order_id = request.POST.get('razorpay_order_id', '')
            payment_id = request.POST.get('razorpay_payment_id', '')
            signature = request.POST.get('razorpay_signature', '')
            print(payment_id, order_id, signature)
            params_dict = {
                'razorpay_order_id' : order_id,
                'razorpay_payment_id' : payment_id,
                'razorpay_signature' : signature,
            }
            
            try:
                order_db = Order.objects.get(razorpay_order_id=order_id)
                print("Order found")
            except:
                print("Order not found")
                return HTTPResponse("505 Not found")
                
            order_db.razorpay_payment_id = payment_id
            order_db.razorpay_signature = signature
            order_db.save()
            print("Working.........")
           
            result = razorpay_client.utility.verify_payment_signature (params_dict)
              
            if result == None:
                print("Working final fine...........")
                
                amount = order_db.get_total_price()
                amount = amount * 100 #we have to pass in paise.
                payment_status = razorpay_client.payment.capture(payment_id, amount)
                if payment_status is not None:
                    print(payment_status)
                    order_db.ordered = True
                    order_db.save()
                    print("Payment success")
                    checkout_address = CheckoutAddress.objects.get(user=request.user)
                    request.session[
                        "order_complete"
                    ]= "Your order is successfully placed, you will receive your order within 5 working days"
                    return render(request, "core/invo/invoice.html",{"order":order_db,"payment_status":payment_status,"checkout_address":checkout_address})
                else:
                    print("Payment failed")
                    order_db.ordered = False
                    order_db.save()
                    request.session[
                        "order_failed"
                    ]= "Unfortunately your order could not be placed, try again!"
                    return redirect("/")
            else:
                order_db.ordered = False
                order_db.save()
                return render(request, "core/paymentfailed.html")
        except:
            return HTTPResponse("Error occured")




def invoice(request):
    return render(request, "core/invo/invoice.html")



    # 37