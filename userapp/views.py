# userapp/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from adminapp.models import *
from accounts.models import *
from .models import *
from django.contrib import messages
import json
from django.http import JsonResponse
from django.db.models import Avg
from decimal import Decimal
from django.db import transaction

from django.db.models import Avg, Count, Q

def home(request):
    products = Product.objects.filter(stock__gt=0).annotate(
        avg_rating=Avg("reviews__rating")
    )

    # Add categories with product counts
    categories = Category.objects.all()
    for category in categories:
        category.product_count = Product.objects.filter(
            category=category, stock__gt=0
        ).count()

    # Category filter
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)

    # Price filter
    price_range = request.GET.get('price')
    if price_range:
        if price_range == '0-99':
            products = products.filter(
                Q(offer_price__gte=0, offer_price__lt=100) |
                Q(offer_price__isnull=True, price__gte=0, price__lt=100)
            )
        elif price_range == '100-199':
            products = products.filter(
                Q(offer_price__gte=100, offer_price__lt=200) |
                Q(offer_price__isnull=True, price__gte=100, price__lt=200)
            )
        elif price_range == '200-plus':
            products = products.filter(
                Q(offer_price__gte=200) |
                Q(offer_price__isnull=True, price__gte=200)
            )

    # Color filter
    color = request.GET.get('color')
    if color:
        products = products.filter(
            attributes__key='color',
            attributes__value__icontains=color
        ).distinct()

    # Sorting
    sort_by = request.GET.get('sort', 'name')

    if sort_by == 'price_low':
        products = sorted(products, key=lambda p: p.final_price)
    elif sort_by == 'price_high':
        products = sorted(products, key=lambda p: p.final_price, reverse=True)
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('name')

    return render(request, "userapp/home.html", {
        "products": products,
        "categories": categories,
        "sort_by": sort_by,
    })


def contact_view(request):
    return render(request, 'userapp/static_pages/contact.html')

def about_view(request):
    return render(request, 'userapp/static_pages/about.html')

def service_view(request):
    return render(request, 'userapp/static_pages/services.html')



@login_required
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    # Check if user has bought this product
    user_can_review = OrderItem.objects.filter(
        order__user=request.user,
        product=product,
        order__payment_status="PAID"
    ).exists()

    # Handle review submit
    if request.method == "POST" and user_can_review:
        title = request.POST.get("title")
        content = request.POST.get("content")
        rating = request.POST.get("rating")

        if title and content and rating:
            Review.objects.create(
                product=product,
                user=request.user,
                title=title,
                content=content,
                rating=int(rating),
            )
            messages.success(request, "Thank you! Your review has been submitted.")
            return redirect("product_detail", slug=slug)

    # Categories for sidebar
    categories = Category.objects.all()
    for category in categories:
        category.product_count = Product.objects.filter(category=category, stock__gt=0).count()

    related_products = Product.objects.exclude(id=product.id).filter(stock__gt=0)[:4]
    

        # Calculate review stats
    reviews = product.reviews.all()
    total_reviews = reviews.count()

    if total_reviews > 0:
        average_rating = round(reviews.aggregate(Avg("rating"))["rating__avg"], 1)
    else:
        average_rating = 0

    # Count each rating
    rating_counts = {
        5: reviews.filter(rating=5).count(),
        4: reviews.filter(rating=4).count(),
        3: reviews.filter(rating=3).count(),
        2: reviews.filter(rating=2).count(),
        1: reviews.filter(rating=1).count(),
    }

    # Percentages
    rating_percent = {
        star: (rating_counts[star] / total_reviews * 100) if total_reviews else 0
        for star in rating_counts
    }


    return render(request, "userapp/product_detail.html", {
        "product": product,
        "categories": categories,
        "related_products": related_products,
        "user_can_review": user_can_review,
            # Review stats
        "total_reviews": total_reviews,
        "average_rating": average_rating,

        # Counts
        "rating_5_count": rating_counts[5],
        "rating_4_count": rating_counts[4],
        "rating_3_count": rating_counts[3],
        "rating_2_count": rating_counts[2],
        "rating_1_count": rating_counts[1],

        # Percents
        "rating_5_percent": rating_percent[5],
        "rating_4_percent": rating_percent[4],
        "rating_3_percent": rating_percent[3],
        "rating_2_percent": rating_percent[2],
        "rating_1_percent": rating_percent[1],
    })



@login_required
def add_to_cart(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
    else:
        quantity = 1  # default fallback

    # Stock Check
    if product.stock < quantity:
        messages.error(request, "Not enough stock available!")
        return redirect("product_detail", slug=product.slug)

    # Get user cart from DB
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Get or create cart item
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    # Update quantity
    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity

    item.save()
    messages.success(request, f"{product.name} added to cart!")
    return redirect("view_cart")  # send user to cart page
from decimal import Decimal
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def view_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # ✅ subtotal (Decimal only)
    subtotal = sum(
        Decimal(item.product.final_price) * item.quantity
        for item in cart.items.all()
    )

    # ✅ coupon discount (session → Decimal)
    discount = Decimal(request.session.get("coupon_discount", "0"))

    if discount > subtotal:
        discount = subtotal

    # ✅ shipping
    shipping_cost = Decimal("50") if subtotal > 0 and subtotal < 500 else Decimal("0")

    # ✅ tax
    tax_rate = Decimal("5")
    tax = (subtotal - discount) * tax_rate / Decimal("100")

    # ✅ total
    total = subtotal - discount + shipping_cost + tax
    if total < 0:
        total = Decimal("0")

    # ✅ RELATED PRODUCTS (KEPT)
    cart_product_ids = cart.items.values_list("product_id", flat=True)
    related_products = Product.objects.exclude(
        id__in=cart_product_ids
    ).filter(stock__gt=0)[:4]

    # ✅ AJAX SUPPORT (KEPT)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        cart_items = [
            {
                "id": item.id,
                "product_id": item.product.id,
                "product_name": item.product.name,
                "price": float(item.product.final_price),
                "quantity": item.quantity,
                "total": float(
                    Decimal(item.product.final_price) * item.quantity
                ),
            }
            for item in cart.items.all()
        ]

        return JsonResponse({
            "cart_items": cart_items,
            "item_count": cart.items.count(),
            "subtotal": float(subtotal),
            "discount": float(discount),
            "total": float(total),
        })

    context = {
        "cart": cart,
        "subtotal": subtotal,
        "discount": discount,
        "shipping_cost": shipping_cost,
        "tax": tax,
        "tax_rate": tax_rate,
        "total": total,
        "related_products": related_products,
    }

    return render(request, "userapp/cart.html", context)


@login_required
def remove_from_cart(request, item_id):
    """Remove an item from the cart"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    
    # If AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product_name} has been removed from your cart.'
        })
    
    messages.success(request, f'{product_name} has been removed from your cart.')
    return redirect('view_cart')


@login_required
def update_cart_quantity(request, item_id):
    """Update cart item quantity via AJAX"""
    if request.method == 'POST':
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))
            
            # Validate quantity
            if quantity < 1:
                return JsonResponse({
                    'success': False,
                    'message': 'Quantity must be at least 1'
                })
            
            # Check stock availability
            if quantity > cart_item.product.stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Only {cart_item.product.stock} items available in stock'
                })
            
            # Update quantity
            cart_item.quantity = quantity
            cart_item.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Cart updated successfully'
            })
            
        except CartItem.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Cart item not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


import razorpay
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse

from .models import Cart, Address, Order, OrderItem

from decimal import Decimal



@login_required
def checkout(request):
    user = request.user
    cart, _ = Cart.objects.get_or_create(user=user)
    addresses = Address.objects.filter(user=user)

    # ===============================
    # 🔒 SAME PRICE LOGIC AS view_cart
    # ===============================
    subtotal = sum(
        Decimal(item.product.final_price) * item.quantity
        for item in cart.items.all()
    )

    discount = Decimal(request.session.get("coupon_discount", "0"))
    if discount > subtotal:
        discount = subtotal

    shipping_cost = Decimal("50") if subtotal > 0 and subtotal < 500 else Decimal("0")

    tax_rate = Decimal("5")
    tax = (subtotal - discount) * tax_rate / Decimal("100")

    total = subtotal - discount + shipping_cost + tax
    if total < 0:
        total = Decimal("0")

    # Razorpay requires paise
    amount_paise = max(int(total * 100), 100)

    # ===============================
    # ADDRESS HANDLING
    # ===============================
    if request.method == "POST":
        address_id = request.POST.get("address_id")

        if address_id:
            address = get_object_or_404(Address, id=address_id, user=user)
        else:
            full_name = request.POST.get("full_name")
            phone = request.POST.get("phone")
            street = request.POST.get("street")
            city = request.POST.get("city")
            state = request.POST.get("state")
            pincode = request.POST.get("pincode")

            if not all([full_name, phone, street, city, state, pincode]):
                messages.error(request, "Please enter a full address.")
                return redirect("checkout")

            address = Address.objects.create(
                user=user,
                full_name=full_name,
                phone=phone,
                street=street,
                city=city,
                state=state,
                pincode=pincode,
            )

        request.session["selected_address"] = address.id

    # ===============================
    # RAZORPAY ORDER
    # ===============================
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    razorpay_order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1,
        "notes": {
            "user_id": user.id,
            "address_id": request.session.get("selected_address"),
            "coupon": request.session.get("coupon_code"),
        }
    })

    return render(request, "userapp/checkout.html", {
        "cart": cart,
        "addresses": addresses,

        # ✅ SAME VALUES AS CART
        "subtotal": subtotal,
        "discount": discount,
        "shipping_cost": shipping_cost,
        "tax": tax,
        "tax_rate": tax_rate,
        "total": total,

        # Razorpay
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "razorpay_order_id": razorpay_order["id"],
        "amount": amount_paise,
        "address_id": request.session.get("selected_address"),
    })

from django.views.decorators.csrf import csrf_exempt



@csrf_exempt
@login_required
def payment_success(request):

    if request.method != "POST":
        return HttpResponse("Invalid method", status=400)

    payment_id = request.POST.get("razorpay_payment_id")
    order_id = request.POST.get("razorpay_order_id")
    signature = request.POST.get("razorpay_signature")

    if not all([payment_id, order_id, signature]):
        return HttpResponse("Missing payment details", status=400)

    address_id = request.session.get("selected_address")
    if not address_id:
        return HttpResponse("Address missing", status=400)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
    except:
        return HttpResponse("Signature verification failed", status=400)

    user = request.user
    cart = get_object_or_404(Cart, user=user)

    # SAME PRICE LOGIC
    subtotal = sum(
        Decimal(item.product.final_price) * item.quantity
        for item in cart.items.all()
    )

    discount = Decimal(request.session.get("coupon_discount", "0"))
    if discount > subtotal:
        discount = subtotal

    shipping_fee = Decimal("50") if subtotal > 0 and subtotal < 500 else Decimal("0")
    tax_rate = Decimal("5")
    tax = (subtotal - discount) * tax_rate / Decimal("100")
    total = subtotal - discount + shipping_fee + tax

    address = get_object_or_404(Address, id=address_id, user=user)

    order = Order.objects.create(
        user=user,
        address=address,
        subtotal=subtotal,
        tax=tax,
        shipping_fee=shipping_fee,
        discount_amount=discount,
        total_price=total,
        status="PLACED",
        payment_status="PAID",
        razorpay_order_id=order_id,
        razorpay_payment_id=payment_id,
        razorpay_signature=signature,
    )

    coupon_id = request.session.get("coupon_id")

    if coupon_id:
        coupon = Coupon.objects.filter(id=coupon_id, is_active=True).first()
        if coupon:
            coupon.used_count += 1
            coupon.save()


    for item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=item.product,
            price=item.product.final_price,
            quantity=item.quantity,
        )

        item.product.stock -= item.quantity
        item.product.save()

    cart.items.all().delete()

    # CLEAR SESSION
    request.session.pop("coupon_discount", None)
    request.session.pop("coupon_code", None)
    request.session.pop("selected_address", None)

    return redirect("order_history")


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import timedelta

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    
    # Add expected delivery date to each order (order date + 3 days)
    for order in orders:
        order.expected_delivery = order.created_at + timedelta(days=3)
    
    return render(request, "userapp/orders.html", {"orders": orders})



@login_required
def user_order_detail(request, pk):
    order = get_object_or_404(
        Order,
        pk=pk,
        user=request.user   # 🔒 security
    )

    items = order.items.select_related("product")

    expected_delivery = order.created_at + timedelta(days=3)

    return render(
        request,
        "userapp/order_detail.html",
        {
            "order": order,
            "items": items,
            "expected_delivery": expected_delivery,
        }
    )




# CREATE
@login_required
def address_create(request):
    if request.method == "POST":
        Address.objects.create(
            user=request.user,
            full_name=request.POST.get("full_name"),
            phone=request.POST.get("phone"),
            street=request.POST.get("street"),
            city=request.POST.get("city"),
            state=request.POST.get("state"),
            pincode=request.POST.get("pincode"),
        )
        messages.success(request, "Address added successfully!")
        return redirect("address_list")  # You can change this redirect URL

    return render(request, "userapp/address_create.html")


# UPDATE
@login_required
def address_update(request, id):
    address = get_object_or_404(Address, id=id, user=request.user)

    if request.method == "POST":
        address.full_name = request.POST.get("full_name")
        address.phone = request.POST.get("phone")
        address.street = request.POST.get("street")
        address.city = request.POST.get("city")
        address.state = request.POST.get("state")
        address.pincode = request.POST.get("pincode")
        address.save()

        messages.success(request, "Address updated successfully!")
        return redirect("address_list")

    return render(request, "userapp/address_update.html", {"address": address})


# DELETE
@login_required
def address_delete(request, id):
    address = get_object_or_404(Address, id=id, user=request.user)

    if request.method == "POST":  # Delete only on POST for safety
        address.delete()
        messages.error(request, "Address deleted!")
        return redirect("profile")

    return render(request, "address_delete.html", {"address": address})


from django.contrib.auth import login  # keep this import

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login

@login_required
def my_profile(request):
    user = request.user
    google_user = not user.has_usable_password()
    
    # Get user's addresses
    addresses = Address.objects.filter(user=request.user)

    if request.method == "POST":
        
        # Handle mobile and full_name update
        if "update_profile" in request.POST:
            mobile = request.POST.get("mobile")
            full_name = request.POST.get("full_name")
            
            # Check if mobile is being changed and if it's already taken by another user
            if mobile != user.mobile:
                if CustomUser.objects.filter(mobile=mobile).exclude(id=user.id).exists():
                    messages.error(request, "This mobile number is already registered with another account!")
                    return redirect("profile")
            
            user.mobile = mobile
            user.full_name = full_name
            user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")

        # Handle password change
        if "change_password" in request.POST:
            if google_user:
                messages.error(request, "Password change is not available for Google authenticated accounts!")
                return redirect("profile")
            
            current = request.POST.get("current_password")
            new = request.POST.get("new_password")
            confirm = request.POST.get("confirm_password")

            if not user.check_password(current):
                messages.error(request, "Current password is incorrect!")
                return redirect("profile")

            if new != confirm:
                messages.error(request, "New password and confirm password does not match!")
                return redirect("profile")

            user.set_password(new)
            user.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "Password changed successfully!")
            return redirect("profile")
        
        # Handle address creation
        if "add_address" in request.POST:
            Address.objects.create(
                user=request.user,
                full_name=request.POST.get("full_name"),
                phone=request.POST.get("phone"),
                street=request.POST.get("street"),
                city=request.POST.get("city"),
                state=request.POST.get("state"),
                pincode=request.POST.get("pincode"),
            )
            messages.success(request, "Address added successfully!")
            return redirect("profile")

    return render(request, "userapp/profile.html", {
        "user": user,
        "google_user": google_user,
        "addresses": addresses
    })


from django.db.models import Q, Count
from adminapp.models import Product, Category
from django.shortcuts import render

def product_search(request):
    query = request.GET.get('query', '')
    category_filter = request.GET.get('category', '')
    price_filter = request.GET.get('price', '')
    color_filter = request.GET.get('color', '')
    sort_by = request.GET.get('sort', 'name')

    products = []

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(category__name__icontains=query) |
            Q(subcategory__name__icontains=query) |
            Q(brand__name__icontains=query)
        ).distinct().select_related('category', 'subcategory', 'brand').prefetch_related('images').annotate(
            avg_rating=Avg("reviews__rating"),
            review_count=Count("reviews")
        )

        # Apply category filter
        if category_filter:
            products = products.filter(category__slug=category_filter)

        # Apply price filter
        if price_filter:
            if price_filter == '0-99':
                products = products.filter(
                    Q(offer_price__gte=0, offer_price__lt=100) | 
                    Q(offer_price__isnull=True, price__gte=0, price__lt=100)
                )
            elif price_filter == '100-199':
                products = products.filter(
                    Q(offer_price__gte=100, offer_price__lt=200) | 
                    Q(offer_price__isnull=True, price__gte=100, price__lt=200)
                )
            elif price_filter == '200-plus':
                products = products.filter(
                    Q(offer_price__gte=200) | 
                    Q(offer_price__isnull=True, price__gte=200)
                )

        # Apply color filter
        if color_filter:
            products = products.filter(attributes__key='color', attributes__value__icontains=color_filter).distinct()

        # Apply sorting
        if sort_by == 'price_low':
            # Sort by final price (offer_price if exists, else price)
            products = sorted(products, key=lambda p: p.final_price)
        elif sort_by == 'price_high':
            products = sorted(products, key=lambda p: p.final_price, reverse=True)
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        elif sort_by == 'name':
            products = products.order_by('name')

        # Limit results (after sorting)
        if isinstance(products, list):
            products = products[:20]
        else:
            products = products[:20]

    # Get categories that contain products matching the query
    categories = Category.objects.annotate(
        product_count=Count('product', filter=Q(
            product__name__icontains=query
        ) | Q(
            product__description__icontains=query
        ) | Q(
            product__sku__icontains=query
        ), distinct=True)
    ).filter(product_count__gt=0).order_by('name')

    return render(request, "userapp/search_results.html", {
        "query": query,
        "products": products,
        "categories": categories,
        "category_filter": category_filter,
        "price_filter": price_filter,
        "color_filter": color_filter,
        "sort_by": sort_by,
        "product_count": len(products) if products else 0
    })



from adminapp.models import Category

def user_home(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'user_base.html', context)




from django.core.paginator import Paginator


def all_products(request):
    """
    Display all products without requiring login with filtering and sorting
    """
    # Get all products with stock
    products = Product.objects.filter(
        stock__gt=0
    ).select_related('category', 'subcategory', 'brand').prefetch_related('images')
    
    # Apply category filter
    category_filter = request.GET.get('category', '')
    if category_filter:
        products = products.filter(category__slug=category_filter)
    
    # Apply price filter
    price_filter = request.GET.get('price', '')
    if price_filter:
        if price_filter == '0-99':
            products = products.filter(
                Q(offer_price__gte=0, offer_price__lt=100) | 
                Q(offer_price__isnull=True, price__gte=0, price__lt=100)
            )
        elif price_filter == '100-199':
            products = products.filter(
                Q(offer_price__gte=100, offer_price__lt=200) | 
                Q(offer_price__isnull=True, price__gte=100, price__lt=200)
            )
        elif price_filter == '200-plus':
            products = products.filter(
                Q(offer_price__gte=200) | 
                Q(offer_price__isnull=True, price__gte=200)
            )
    
    # Apply sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        # Sort by final price (offer_price if exists, else price)
        products = sorted(products, key=lambda p: p.final_price)
    elif sort_by == 'price_high':
        products = sorted(products, key=lambda p: p.final_price, reverse=True)
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'name':
        products = products.order_by('name')
    
    # Get all categories with product counts
    categories = Category.objects.annotate(
        product_count=Count('product', filter=Q(product__stock__gt=0))
    ).filter(product_count__gt=0).order_by('name')
    
    # Calculate price range counts dynamically
    all_products_for_count = Product.objects.filter(stock__gt=0)
    price_ranges = {
        'range_0_99': all_products_for_count.filter(
            Q(offer_price__gte=0, offer_price__lt=100) | 
            Q(offer_price__isnull=True, price__gte=0, price__lt=100)
        ).count(),
        'range_100_199': all_products_for_count.filter(
            Q(offer_price__gte=100, offer_price__lt=200) | 
            Q(offer_price__isnull=True, price__gte=100, price__lt=200)
        ).count(),
        'range_200_plus': all_products_for_count.filter(
            Q(offer_price__gte=200) | 
            Q(offer_price__isnull=True, price__gte=200)
        ).count(),
    }
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(products if isinstance(products, list) else products.all(), 20)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'category_filter': category_filter,
        'price_filter': price_filter,
        'sort_by': sort_by,
        'price_ranges': price_ranges,
        'total_products': paginator.count,
    }
    
    return render(request, 'userapp/all_products.html', context)


def product_search_no_login(request):
    """
    Search products without requiring login
    """
    query = request.GET.get('query', '').strip()
    category_filter = request.GET.get('category', '')
    price_filter = request.GET.get('price', '')
    sort_by = request.GET.get('sort', 'relevance')
    
    products = Product.objects.none()
    
    if query:
        # Search across multiple fields
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(category__name__icontains=query) |
            Q(subcategory__name__icontains=query) |
            Q(brand__name__icontains=query)
        ).filter(stock__gt=0).distinct().select_related(
            'category', 'subcategory', 'brand'
        ).prefetch_related('images')

        # Apply category filter
        if category_filter:
            products = products.filter(category__slug=category_filter)

        # Apply price filter (considering offer_price)
        if price_filter:
            if price_filter == '0-99':
                products = products.filter(
                    Q(offer_price__gte=0, offer_price__lt=100) | 
                    Q(offer_price__isnull=True, price__gte=0, price__lt=100)
                )
            elif price_filter == '100-199':
                products = products.filter(
                    Q(offer_price__gte=100, offer_price__lt=200) | 
                    Q(offer_price__isnull=True, price__gte=100, price__lt=200)
                )
            elif price_filter == '200-plus':
                products = products.filter(
                    Q(offer_price__gte=200) | 
                    Q(offer_price__isnull=True, price__gte=200)
                )
        
        # Apply sorting
        if sort_by == 'price_low':
            products = sorted(products, key=lambda p: p.final_price)
        elif sort_by == 'price_high':
            products = sorted(products, key=lambda p: p.final_price, reverse=True)
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        elif sort_by == 'name':
            products = products.order_by('name')

    # Get categories that have products matching the search
    if query:
        categories = Category.objects.annotate(
            product_count=Count(
                'product',
                filter=Q(
                    product__name__icontains=query,
                    product__stock__gt=0
                ) | Q(
                    product__description__icontains=query,
                    product__stock__gt=0
                ) | Q(
                    product__sku__icontains=query,
                    product__stock__gt=0
                ),
                distinct=True
            )
        ).filter(product_count__gt=0).order_by('name')
    else:
        categories = Category.objects.none()
    
    # Calculate price ranges for filtered results
    price_ranges = {
        '0-99': 0,
        '100-199': 0,
        '200-plus': 0,
    }
    
    if query and products.exists():
        all_matching = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(category__name__icontains=query) |
            Q(subcategory__name__icontains=query) |
            Q(brand__name__icontains=query)
        ).filter(stock__gt=0)
        
        price_ranges['0-99'] = all_matching.filter(
            Q(offer_price__gte=0, offer_price__lt=100) | 
            Q(offer_price__isnull=True, price__gte=0, price__lt=100)
        ).count()
        price_ranges['100-199'] = all_matching.filter(
            Q(offer_price__gte=100, offer_price__lt=200) | 
            Q(offer_price__isnull=True, price__gte=100, price__lt=200)
        ).count()
        price_ranges['200-plus'] = all_matching.filter(
            Q(offer_price__gte=200) | 
            Q(offer_price__isnull=True, price__gte=200)
        ).count()

    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(products if isinstance(products, list) else products, 20)
    page_obj = paginator.get_page(page_number)

    context = {
        "query": query,
        "products": page_obj,
        "categories": categories,
        "category_filter": category_filter,
        "price_filter": price_filter,
        "sort_by": sort_by,
        "price_ranges": price_ranges,
        "total_products": paginator.count if query else 0,
    }
    
    return render(request, "userapp/search_results_no_login.html", context)


def category_products_no_login(request, slug):
    """
    Display products for a specific category without requiring login
    """
    category = get_object_or_404(Category, slug=slug)
    
    products = Product.objects.filter(
        category=category,
        stock__gt=0
    ).select_related('category', 'subcategory', 'brand').prefetch_related('images')
    
    # Apply price filter (considering offer_price)
    price_filter = request.GET.get('price', '')
    if price_filter:
        if price_filter == '0-99':
            products = products.filter(
                Q(offer_price__gte=0, offer_price__lt=100) | 
                Q(offer_price__isnull=True, price__gte=0, price__lt=100)
            )
        elif price_filter == '100-199':
            products = products.filter(
                Q(offer_price__gte=100, offer_price__lt=200) | 
                Q(offer_price__isnull=True, price__gte=100, price__lt=200)
            )
        elif price_filter == '200-plus':
            products = products.filter(
                Q(offer_price__gte=200) | 
                Q(offer_price__isnull=True, price__gte=200)
            )
    
    # Apply sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = sorted(products, key=lambda p: p.final_price)
    elif sort_by == 'price_high':
        products = sorted(products, key=lambda p: p.final_price, reverse=True)
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'name':
        products = products.order_by('name')
    
    # Get all categories for sidebar
    categories = Category.objects.annotate(
        product_count=Count('product', filter=Q(product__stock__gt=0))
    ).filter(product_count__gt=0).order_by('name')
    
    # Calculate price ranges for this category
    category_products = Product.objects.filter(category=category, stock__gt=0)
    price_ranges = {
        '0-99': category_products.filter(
            Q(offer_price__gte=0, offer_price__lt=100) | 
            Q(offer_price__isnull=True, price__gte=0, price__lt=100)
        ).count(),
        '100-199': category_products.filter(
            Q(offer_price__gte=100, offer_price__lt=200) | 
            Q(offer_price__isnull=True, price__gte=100, price__lt=200)
        ).count(),
        '200-plus': category_products.filter(
            Q(offer_price__gte=200) | 
            Q(offer_price__isnull=True, price__gte=200)
        ).count(),
    }
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(products if isinstance(products, list) else products, 20)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'products': page_obj,
        'categories': categories,
        'price_filter': price_filter,
        'sort_by': sort_by,
        'price_ranges': price_ranges,
        'total_products': paginator.count,
    }
    
    return render(request, 'userapp/category_products_no_login.html', context)


@login_required
def category_products(request, slug):
    """
    Display products for a specific category - Login required
    """
    category = get_object_or_404(Category, slug=slug)
    
    products = Product.objects.filter(
        category=category,
        stock__gt=0
    ).select_related('category', 'subcategory', 'brand').prefetch_related('images').annotate(
            avg_rating=Avg("reviews__rating"),
            review_count=Count("reviews")
        )
    
    # Apply price filter (considering offer_price)
    price_filter = request.GET.get('price', '')
    if price_filter:
        if price_filter == '0-99':
            products = products.filter(
                Q(offer_price__gte=0, offer_price__lt=100) | 
                Q(offer_price__isnull=True, price__gte=0, price__lt=100)
            )
        elif price_filter == '100-199':
            products = products.filter(
                Q(offer_price__gte=100, offer_price__lt=200) | 
                Q(offer_price__isnull=True, price__gte=100, price__lt=200)
            )
        elif price_filter == '200-plus':
            products = products.filter(
                Q(offer_price__gte=200) | 
                Q(offer_price__isnull=True, price__gte=200)
            )
    
    # Apply sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = sorted(products, key=lambda p: p.final_price)
    elif sort_by == 'price_high':
        products = sorted(products, key=lambda p: p.final_price, reverse=True)
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'name':
        products = products.order_by('name')
    
    # Get all categories for sidebar
    categories = Category.objects.annotate(
        product_count=Count('product', filter=Q(product__stock__gt=0))
    ).filter(product_count__gt=0).order_by('name')
    
    # Calculate price ranges for this category
    category_products_qs = Product.objects.filter(category=category, stock__gt=0)
    price_ranges = {
        '0-99': category_products_qs.filter(
            Q(offer_price__gte=0, offer_price__lt=100) | 
            Q(offer_price__isnull=True, price__gte=0, price__lt=100)
        ).count(),
        '100-199': category_products_qs.filter(
            Q(offer_price__gte=100, offer_price__lt=200) | 
            Q(offer_price__isnull=True, price__gte=100, price__lt=200)
        ).count(),
        '200-plus': category_products_qs.filter(
            Q(offer_price__gte=200) | 
            Q(offer_price__isnull=True, price__gte=200)
        ).count(),
    }
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(products if isinstance(products, list) else products, 20)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'products': page_obj,
        'categories': categories,
        'price_filter': price_filter,
        'sort_by': sort_by,
        'price_ranges': price_ranges,
        'total_products': paginator.count,
    }
    
    return render(request, 'userapp/category_products.html', context)
    



def product_detail_no_login(request, slug):
    """
    Display product details without requiring login
    """
    # Get product with related data
    product = get_object_or_404(
        Product.objects.select_related('category', 'subcategory', 'brand')
        .prefetch_related('images', 'attributes', 'reviews__user'),
        slug=slug
    )
    
    # Calculate review statistics
    reviews = product.reviews.all()
    total_reviews = reviews.count()
    
    if total_reviews > 0:
        # Calculate average rating
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        average_rating = round(average_rating, 1)
        
        # Calculate rating distribution
        rating_counts = {
            5: reviews.filter(rating=5).count(),
            4: reviews.filter(rating=4).count(),
            3: reviews.filter(rating=3).count(),
            2: reviews.filter(rating=2).count(),
            1: reviews.filter(rating=1).count(),
        }
        
        # Calculate percentages
        rating_percentages = {
            rating: round((count / total_reviews) * 100, 1) if total_reviews > 0 else 0
            for rating, count in rating_counts.items()
        }
    else:
        average_rating = 0
        rating_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        rating_percentages = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    
    # User cannot review without being logged in
    user_can_review = False
    
    # Get related products from same category
    related_products = Product.objects.filter(
        category=product.category,
        stock__gt=0
    ).exclude(id=product.id).select_related(
        'category', 'brand'
    ).prefetch_related('images')[:4]
    
    context = {
        'product': product,
        'total_reviews': total_reviews,
        'average_rating': average_rating,
        'rating_5_count': rating_counts[5],
        'rating_4_count': rating_counts[4],
        'rating_3_count': rating_counts[3],
        'rating_2_count': rating_counts[2],
        'rating_1_count': rating_counts[1],
        'rating_5_percent': rating_percentages[5],
        'rating_4_percent': rating_percentages[4],
        'rating_3_percent': rating_percentages[3],
        'rating_2_percent': rating_percentages[2],
        'rating_1_percent': rating_percentages[1],
        'user_can_review': user_can_review,
        'related_products': related_products,
    }
    
    return render(request, 'userapp/product_detail_no_login.html', context)


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    product_slug = review.product.slug
    
    if request.method == "POST":
        review.delete()
        messages.success(request, "Your review has been deleted successfully.")
        return redirect("product_detail", slug=product_slug)
    
    return redirect("product_detail", slug=product_slug)

from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal

from .models import Coupon


@login_required
def apply_coupon(request):
    if request.method != "POST":
        return redirect("view_cart")

    code = request.POST.get("coupon_code", "").strip().upper()

    if not code:
        messages.error(request, "Please enter a coupon code")
        return redirect("view_cart")

    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        messages.error(request, "Invalid coupon code")
        return redirect("view_cart")

    if not coupon.is_valid():
        messages.error(request, "Coupon expired or usage limit reached")
        return redirect("view_cart")

    # ✅ prevent re-applying same coupon
    if request.session.get("coupon_code") == coupon.code:
        messages.warning(request, "Coupon already applied")
        return redirect("view_cart")

    # ✅ store SAFE values
    request.session["coupon_id"] = coupon.id
    request.session["coupon_code"] = coupon.code
    request.session["coupon_discount"] = str(coupon.discount)


    messages.success(request, f"Coupon {coupon.code} applied successfully")
    return redirect("view_cart")


@login_required
def remove_coupon(request):
    request.session.pop("coupon_code", None)
    request.session.pop("coupon_discount", None)
    messages.success(request, "Coupon removed")
    return redirect("view_cart")
