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
from django.urls import reverse
from django.db.models import Avg, Count, Q
from decimal import Decimal
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Cart, Address, Order, OrderItem
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import (Cart,Order,OrderItem,Address,)
from adminapp.models import Coupon, Product,CouponUsage
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import login  # keep this import
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.core.paginator import Paginator
from django.db.models import Q, Count
from adminapp.models import Product, Category
from django.shortcuts import render
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from adminapp.models import Coupon
from .models import Cart
from adminapp.models import CouponUsage
from adminapp.models import Category
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import OrderItem
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import ReplacementOrder
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import ReplacementOrder
from .email_utils import send_order_confirmation_email
from userapp.email_utils import send_order_shipped_email
from userapp.email_utils import send_order_delivered_email
from userapp.email_utils import send_order_cancelled_email





def user_index(request):
    sections = HomepageSection.objects.filter(is_active=True).prefetch_related(
        'homepage_products__product__images',
        'homepage_products__product__category',
        'categories'
    )

    homepage_data = {}

    # -----------------------------
    # Build homepage section data
    # -----------------------------
    for section in sections:
        if section.display_type == 'manual':
            products = [
                hp.product
                for hp in section.homepage_products.all().order_by('display_order')
            ]
        else:
            products = Product.objects.filter(
                category__in=section.categories.all()
            ).distinct().order_by('-created_at')

        homepage_data[section.section_type] = {
            'name': section.name,
            'products': products,
            'categories': section.categories.all()
        }

    # -----------------------------
    # Featured Products
    # -----------------------------
    featured_section = homepage_data.get('featured', {})
    featured_products = featured_section.get('products', [])

    # -----------------------------
    # Deals of the Day
    # -----------------------------
    deals_section = homepage_data.get('deals', {})
    deals_products = deals_section.get('products', [])

    # -----------------------------
    # Best Sellers (grouped by category)
    # -----------------------------
    best_seller_categories = homepage_data.get('best_seller', {}).get('categories', [])
    best_seller_products = homepage_data.get('best_seller', {}).get('products', [])

    best_sellers_by_category = {
        category.id: [
            p for p in best_seller_products
            if p.category_id == category.id
        ]
        for category in best_seller_categories
    }

    # -----------------------------
    # New Arrivals (grouped by category)
    # -----------------------------
    new_arrival_categories = homepage_data.get('new_arrival', {}).get('categories', [])
    new_arrival_products = homepage_data.get('new_arrival', {}).get('products', [])

    new_arrivals_by_category = {
        category.id: [
            p for p in new_arrival_products
            if p.category_id == category.id
        ]
        for category in new_arrival_categories
    }

    # -----------------------------
    # Final Context
    # -----------------------------

    categories = Category.objects.all()

    context = {
        'homepage_data': homepage_data,

        # Featured Products
        'featured_products': featured_products,

        # Deals of the Day
        'deals_products': deals_products,

        # New Arrivals
        'new_arrivals': new_arrival_products,
        'new_arrival_categories': new_arrival_categories,
        'new_arrivals_by_category': new_arrivals_by_category,

        # Best Sellers
        'best_seller_categories': best_seller_categories,
        'best_sellers_by_category': best_sellers_by_category,
        'categories': categories
    }

    return render(request, 'userapp/user_index.html', context)




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
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect("dashboard")
        return redirect("user_home")
    return render(request, 'userapp/static_pages/contact.html')

def about_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect("dashboard")
        return redirect("user_home")
    return render(request, 'userapp/static_pages/about.html')

def service_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect("dashboard")
        return redirect("user_home")
    return render(request, 'userapp/static_pages/services.html')



@login_required(login_url="/login/")
def product_detail(request, slug):

    product = get_object_or_404(Product, slug=slug)

    # Check if user has bought this product
    user_can_review = OrderItem.objects.filter(
        order__user=request.user,
        product=product,
        order__payment_status="PAID"
    ).exists()

    # =====================================
    # HANDLE REVIEW SUBMISSION
    # =====================================
    if request.method == "POST":

        # User must purchase product
        if not user_can_review:
            messages.error(
                request,
                "You can review only purchased products."
            )
            return redirect("product_detail", slug=slug)

        # Prevent duplicate reviews
        already_reviewed = Review.objects.filter(
            product=product,
            user=request.user
        ).exists()

        if already_reviewed:
            messages.warning(
                request,
                "You already submitted a review for this product."
            )
            return redirect("product_detail", slug=slug)

        # Get form data safely
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        rating = request.POST.get("rating", "").strip()

        # Validate required fields
        if not title or not content or not rating:
            messages.error(
                request,
                "All review fields are required."
            )
            return redirect("product_detail", slug=slug)

        # Validate rating
        try:
            rating = int(rating)

            if rating < 1 or rating > 5:
                messages.error(
                    request,
                    "Rating must be between 1 and 5."
                )
                return redirect("product_detail", slug=slug)

        except ValueError:
            messages.error(
                request,
                "Invalid rating value."
            )
            return redirect("product_detail", slug=slug)

        # Optional content length validation
        if len(content) < 5:
            messages.error(
                request,
                "Review content is too short."
            )
            return redirect("product_detail", slug=slug)

        # Create review
        Review.objects.create(
            product=product,
            user=request.user,
            title=title,
            content=content,
            rating=rating,
        )

        messages.success(
            request,
            "Thank you! Your review has been submitted."
        )

        return redirect("product_detail", slug=slug)

    # =====================================
    # CATEGORIES
    # =====================================
    categories = Category.objects.all()

    for category in categories:
        category.product_count = Product.objects.filter(
            category=category,
            stock__gt=0
        ).count()

    # =====================================
    # RELATED PRODUCTS
    # =====================================
    related_products = Product.objects.exclude(
        id=product.id
    ).filter(
        stock__gt=0
    )[:4]

    # =====================================
    # REVIEW STATS
    # =====================================
    reviews = product.reviews.all()

    total_reviews = reviews.count()

    if total_reviews > 0:
        average_rating = round(
            reviews.aggregate(
                Avg("rating")
            )["rating__avg"],
            1
        )
    else:
        average_rating = 0

    # Rating counts
    rating_counts = {
        5: reviews.filter(rating=5).count(),
        4: reviews.filter(rating=4).count(),
        3: reviews.filter(rating=3).count(),
        2: reviews.filter(rating=2).count(),
        1: reviews.filter(rating=1).count(),
    }

    # Rating percentages
    rating_percent = {
        star: (
            rating_counts[star] / total_reviews * 100
        ) if total_reviews else 0
        for star in rating_counts
    }

    return render(
        request,
        "userapp/product_detail.html",
        {
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

            # Percentages
            "rating_5_percent": rating_percent[5],
            "rating_4_percent": rating_percent[4],
            "rating_3_percent": rating_percent[3],
            "rating_2_percent": rating_percent[2],
            "rating_1_percent": rating_percent[1],
        }
    )

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

@login_required
def get_available_coupons(request):
    from django.utils import timezone
    from adminapp.models import Coupon, CouponUsage

    now = timezone.now()

    # Coupons already used by this user
    used_ids = CouponUsage.objects.filter(
        user=request.user
    ).values_list('coupon_id', flat=True)

    coupons = Coupon.objects.filter(
        is_active=True,
        valid_from__lte=now,
        valid_to__gte=now,
    ).exclude(id__in=used_ids)

    data = []
    for c in coupons:
        if c.usage_limit is None or c.used_count < c.usage_limit:
            data.append({
                'code': c.code,
                'discount': float(c.discount),
                'valid_to': c.valid_to.strftime('%d %b %Y'),
            })

    return JsonResponse({'coupons': data})


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
    ).filter(stock__gt=0)[:4].annotate(
        avg_rating=Avg("reviews__rating")
    )

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
    if request.method == "POST":
        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__user=request.user
        )

        cart = cart_item.cart
        cart_item.delete()

        item_count = cart.items.count()
        subtotal = sum(
            item.product.price * item.quantity
            for item in cart.items.all()
        )

        return JsonResponse({
            "success": True,
            "item_id": item_id,
            "item_count": item_count,
            "subtotal": float(subtotal),
        })

    return JsonResponse({"success": False}, status=400)


@login_required
def update_cart_quantity(request, item_id):
    if request.method == 'POST':
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))

            if quantity < 1:
                return JsonResponse({'success': False, 'message': 'Quantity must be at least 1'})

            if quantity > cart_item.product.stock:
                return JsonResponse({'success': False, 'message': f'Only {cart_item.product.stock} in stock'})

            cart_item.quantity = quantity
            cart_item.save()

            # Recalculate cart totals
            cart = cart_item.cart
            subtotal = sum(
                Decimal(str(item.product.final_price)) * item.quantity
                for item in cart.items.all()
            )

            return JsonResponse({
                'success': True,
                'item_count': cart.items.count(),
                'subtotal': float(subtotal),
                'item_total': float(Decimal(str(cart_item.product.final_price)) * quantity),
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid method'})


@login_required
def checkout(request):

    user = request.user
    cart, _ = Cart.objects.get_or_create(user=user)

    if not cart.items.exists():
        messages.error(
            request,
            "Your cart is empty"
        )
        return redirect("view_cart")

    addresses = Address.objects.filter(user=user)

    subtotal = sum(
        Decimal(item.product.final_price) * item.quantity
        for item in cart.items.all()
    )

    discount = Decimal(
        request.session.get(
            "coupon_discount",
            "0"
        )
    )

    if discount > subtotal:
        discount = subtotal

    shipping_cost = (
        Decimal("50")
        if subtotal > 0 and subtotal < 500
        else Decimal("0")
    )

    tax_rate = Decimal("5")

    tax = (
        (subtotal - discount)
        * tax_rate
        / Decimal("100")
    )

    total = (
        subtotal
        - discount
        + shipping_cost
        + tax
    )

    amount_paise = int(total * 100)

    if request.method == "POST":

        address_id = request.POST.get("address_id")

        if address_id:
            # Use saved address
            address = get_object_or_404(Address, id=address_id, user=user)

        else:
            # Validate new address fields
            full_name = request.POST.get("full_name", "").strip()
            phone     = request.POST.get("phone", "").strip()
            street    = request.POST.get("street", "").strip()
            city      = request.POST.get("city", "").strip()
            state     = request.POST.get("state", "").strip()
            pincode   = request.POST.get("pincode", "").strip()

            if not all([full_name, phone, street, city, state, pincode]):
                messages.error(
                    request,
                    "Please select a saved address or fill in all address fields."
                )
                return render(
                    request,
                    "userapp/checkout.html",
                    {
                        "cart": cart,
                        "addresses": addresses,
                        "subtotal": subtotal,
                        "discount": discount,
                        "shipping_cost": shipping_cost,
                        "tax": tax,
                        "tax_rate": tax_rate,
                        "total": total,
                    }
                )

            address = Address.objects.create(
                user=user,
                full_name=full_name,
                phone=phone,
                street=street,
                city=city,
                state=state,
                pincode=pincode,
            )

        request.session[
            "selected_address"
        ] = address.id

        checkout_session = stripe.checkout.Session.create(

            payment_method_types=["card"],

            line_items=[{

                "price_data": {

                    "currency": "inr",

                    "product_data": {
                        "name": f"Order #{user.id}"
                    },

                    "unit_amount": amount_paise,
                },

                "quantity": 1

            }],

            mode="payment",

            success_url=request.build_absolute_uri(
                reverse(
                    "order_success"
                )
            ) + "?session_id={CHECKOUT_SESSION_ID}",

            cancel_url=request.build_absolute_uri(
                reverse(
                    "checkout"
                )
            )
        )

        return redirect(
            checkout_session.url,
            code=303
        )

    return render(
        request,
        "userapp/checkout.html",
        {
            "cart": cart,
            "addresses": addresses,
            "subtotal": subtotal,
            "discount": discount,
            "shipping_cost": shipping_cost,
            "tax": tax,
            "tax_rate": tax_rate,
            "total": total,
        }
    )


@csrf_protect
@login_required
def payment_success(request):

    session_id = request.GET.get("session_id")

    if not session_id:
        return HttpResponse("Session missing")

    try:
        session = stripe.checkout.Session.retrieve(session_id)

    except Exception as e:
        return HttpResponse(str(e))

    # Payment check
    if session.payment_status != "paid":
        return HttpResponse("Payment failed")

    user = request.user

    cart = get_object_or_404(
        Cart,
        user=user
    )

    address_id = request.session.get(
        "selected_address"
    )

    address = get_object_or_404(
        Address,
        id=address_id
    )

    subtotal = sum(
        Decimal(item.product.final_price) * item.quantity
        for item in cart.items.all()
    )

    discount = Decimal(
        request.session.get(
            "coupon_discount",
            "0"
        )
    )

    shipping_fee = (
        Decimal("50")
        if subtotal > 0 and subtotal < 500
        else Decimal("0")
    )

    tax = (
        (subtotal - discount)
        * Decimal("5")
        / Decimal("100")
    )

    total = (
        subtotal
        - discount
        + shipping_fee
        + tax
    )

    with transaction.atomic():

        from django.db import IntegrityError

        try:
            order = Order.objects.create(
                user=user,
                address=address,

                subtotal=subtotal,
                tax=tax,
                shipping_fee=shipping_fee,
                discount_amount=discount,
                total_price=total,

                payment_status="PAID",

                stripe_session_id=session.id,
                stripe_payment_intent=session.payment_intent
            )

        except IntegrityError:
            return redirect("order_history")

        # SAVE COUPON USAGE
        coupon_id = request.session.get("coupon_id")

        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id)

                # Save user coupon usage
                CouponUsage.objects.get_or_create(
                    user=user,
                    coupon=coupon,
                    order=order
                )

                # Increase coupon used count
                coupon.used_count += 1
                coupon.save()

                # Save coupon in order
                order.coupon = coupon
                order.save()

            except Coupon.DoesNotExist:
                pass

        # CREATE ORDER ITEMS + UPDATE STOCK
        for item in cart.items.select_related("product"):

            product = Product.objects.select_for_update().get(
                id=item.product.id
            )

            if product.stock < item.quantity:
                return HttpResponse(
                    f"{product.name} out of stock"
                )

            product.stock -= item.quantity
            product.save()

            OrderItem.objects.create(
                order=order,
                product=product,
                price=product.final_price,
                quantity=item.quantity
            )

        cart.items.all().delete()

        send_order_confirmation_email(order)

    # CLEAR SESSION
    request.session.pop("coupon_id", None)
    request.session.pop("coupon_code", None)
    request.session.pop("coupon_discount", None)
    request.session.pop("selected_address", None)

    return redirect("order_history")

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    
    # Add expected delivery date to each order (order date + 3 days)
    for order in orders:
        order.expected_delivery = order.created_at + timedelta(days=3)
    
    return render(request, "userapp/orders.html", {"orders": orders})




@login_required
def user_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    items = order.items.select_related("product")

    expected_delivery = order.created_at + timedelta(days=3)

    # ✅ REAL replacement logic
    replacement_allowed = False

    if order.status == "DELIVERED":
        delivered_at = order.updated_at   # or delivered_at if you add later
        replacement_deadline = delivered_at + timedelta(days=7)

        replacement_allowed = timezone.now() <= replacement_deadline
    else:
        replacement_deadline = None

    return render(
        request,
        "userapp/order_detail.html",
        {
            "order": order,
            "items": items,
            "expected_delivery": expected_delivery,
            "replacement_allowed": replacement_allowed,
            "replacement_deadline": replacement_deadline,
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


def user_home(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'user_base.html', context)






def all_products(request):
    if request.user.is_authenticated:
        return redirect("user_home")  # or logged-in products page
    """
    Display all products without requiring login with filtering and sorting
    """
    # Get all products with stock
    products = Product.objects.filter(
        stock__gt=0
    ).select_related('category', 'subcategory', 'brand').prefetch_related('images').annotate(
        avg_rating=Avg("reviews__rating")
    )
    
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
    if request.user.is_authenticated:
        return redirect("user_home")  # or logged-in products page
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
        ).prefetch_related('images').annotate(
        avg_rating=Avg("reviews__rating")
    )

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
    if request.user.is_authenticated:
        return redirect("user_home")  # or logged-in products page
    """
    Display products for a specific category without requiring login
    """
    category = get_object_or_404(Category, slug=slug)
    
    products = Product.objects.filter(
        category=category,
        stock__gt=0
    ).select_related('category', 'subcategory', 'brand').prefetch_related('images').annotate(
        avg_rating=Avg("reviews__rating")
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
    if request.user.is_authenticated:
        return redirect("user_home")  # or logged-in products page
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
        "login_next_url": reverse("product_detail", args=[product.slug]),
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


def product_page(request, slug):

    product = get_object_or_404(
        Product,
        slug=slug
    )

    if request.user.is_authenticated:
        return product_detail(request, slug)

    return product_detail_no_login(request, slug)

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    product_slug = review.product.slug
    
    if request.method == "POST":
        review.delete()
        messages.success(request, "Your review has been deleted successfully.")
        return redirect("product_detail", slug=product_slug)
    
    return redirect("product_detail", slug=product_slug)



@login_required
def apply_coupon(request):

    if request.method != "POST":
        return redirect("view_cart")

    code = request.POST.get("coupon_code", "").strip().upper()

    if not code:
        messages.error(request, "Please enter a coupon code")
        return redirect("view_cart")

    # =========================
    # GET COUPON
    # =========================
    try:
        coupon = Coupon.objects.get(
            code=code,
            is_active=True
        )
    except Coupon.DoesNotExist:
        messages.error(request, "Invalid coupon code")
        return redirect("view_cart")

    # =========================
    # VALIDITY CHECK
    # =========================
    if not coupon.is_valid():
        messages.error(
            request,
            "Coupon expired or usage limit reached"
        )
        return redirect("view_cart")

    # =========================
    # PREVENT SAME USER REUSE
    # =========================
    already_used = CouponUsage.objects.filter(
        user=request.user,
        coupon=coupon
    ).exists()

    if already_used:
        messages.error(
            request,
            "You already used this coupon"
        )
        return redirect("view_cart")

    # =========================
    # GET CART
    # =========================
    cart, created = Cart.objects.get_or_create(
        user=request.user
    )

    if not cart.items.exists():
        messages.error(
            request,
            "Your cart is empty"
        )
        return redirect("view_cart")

    # =========================
    # CALCULATE SUBTOTAL
    # =========================
    subtotal = Decimal("0")

    for item in cart.items.all():

        product_price = (
            item.product.offer_price
            if item.product.offer_price
            else item.product.price
        )

        subtotal += Decimal(product_price) * item.quantity

    # =========================
    # PREVENT OVER DISCOUNT
    # =========================
    discount = Decimal(coupon.discount)

    if discount > subtotal:
        discount = subtotal

    # =========================
    # STORE IN SESSION
    # =========================
    request.session["coupon_id"] = coupon.id
    request.session["coupon_code"] = coupon.code
    request.session["coupon_discount"] = str(discount)

    messages.success(
        request,
        f"Coupon {coupon.code} applied successfully"
    )

    return redirect("view_cart")


@login_required
def remove_coupon(request):
    request.session.pop("coupon_id", None)
    request.session.pop("coupon_code", None)
    request.session.pop("coupon_discount", None)
    messages.success(request, "Coupon removed")
    return redirect("view_cart")


@login_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)

    # ❌ Block cancellation after shipping
    if order.status in ["SHIPPED", "DELIVERED", "CANCELLED"]:
        messages.error(request, "This order cannot be cancelled after shipping.")
        return redirect("order_history")

    if request.method == "POST":
        order.cancel_reason = request.POST.get("reason")
        order.refund_account_name = request.POST.get("account_name")
        order.refund_account_number = request.POST.get("account_number")
        order.refund_ifsc = request.POST.get("ifsc")
        order.refund_bank_name = request.POST.get("bank_name")

        order.status = "CANCELLED"
        order.refund_status = "PENDING"
        order.cancelled_at = timezone.now()   # ✅ AUTO SET DATE & TIME
        order.save()

        # 🔄 Restore stock
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

        messages.success(
            request,
            "Order cancelled successfully before shipping. Refund will be processed."
        )
        return redirect("order_history")

    return render(request, "userapp/cancel_order.html", {"order": order})



User = get_user_model()

def forgot_password(request):

    if request.method == "POST":

        email = request.POST.get("email", "").strip()

        # ==========================================
        # ALWAYS SHOW SAME MESSAGE
        # ==========================================
        success_message = (
            "If an account exists with this email, "
            "a password reset link has been sent."
        )

        try:
            user = User.objects.get(email=email)

            # ==========================================
            # BLOCK GOOGLE LOGIN USERS
            # ==========================================
            if user.has_usable_password():

                uid = urlsafe_base64_encode(
                    force_bytes(user.pk)
                )

                token = default_token_generator.make_token(user)

                reset_link = request.build_absolute_uri(
                    reverse(
                        "reset_password",
                        args=[uid, token]
                    )
                )

                # ==========================================
                # SEND RESET EMAIL
                # ==========================================
                send_mail(
                    subject="Reset your password",
                    message=(
                        f"Click the link below to reset "
                        f"your password:\n\n{reset_link}"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )

        except User.DoesNotExist:

            # ==========================================
            # IMPORTANT:
            # DO NOTHING
            # ==========================================
            pass

        # ==========================================
        # SAME RESPONSE FOR EVERY CASE
        # ==========================================
        messages.success(request, success_message)

        return redirect("login")

    return render(
        request,
        "userapp/forgot_password.html"
    )


def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, "Invalid or expired reset link")
        return redirect("forgot_password")

    if request.method == "POST":
        password = request.POST.get("password")
        confirm = request.POST.get("confirm_password")

        if password != confirm:
            messages.error(request, "Passwords do not match")
            return redirect(request.path)

        user.set_password(password)
        user.save()

        messages.success(request, "Password reset successful. Please login.")
        return redirect("login")

    return render(request, "userapp/reset_password.html")


@login_required
def request_replacement(request, item_id):
    item = get_object_or_404(
        OrderItem,
        id=item_id,
        order__user=request.user
    )

    order = item.order

    if order.status != "DELIVERED":
        messages.error(request, "Replacement allowed only after delivery.")
        return redirect("user_order_detail", pk=order.id)

    replacement_deadline = order.updated_at + timedelta(days=7)

    if timezone.now() > replacement_deadline:
        messages.error(request, "Replacement window expired.")
        return redirect("user_order_detail", pk=order.id)

    if item.replacement_requested:
        messages.warning(request, "Replacement already requested.")
        return redirect("user_order_detail", pk=order.id)

    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()

        if not reason:
            messages.error(request, "Reason is required.")
            return redirect(request.path)

        item.mark_replacement_requested(reason)

        messages.success(request, "Replacement request submitted.")
        return redirect("user_order_detail", pk=order.id)

    return render(request, "userapp/request_replacement.html", {
        "item": item,
        "order": order,
        "replacement_deadline": replacement_deadline,
    })




@login_required
def replacement_orders(request):
    orders = ReplacementOrder.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "userapp/replacement_orders.html",
        {"orders": orders}
    )




@login_required
def replacement_order_detail(request, pk):
    order = get_object_or_404(
        ReplacementOrder,
        pk=pk,
        user=request.user
    )

    expected_delivery = order.created_at + timedelta(days=3)

    return render(
        request,
        "userapp/replacement_order_detail.html",
        {
            "order": order,
            "expected_delivery": expected_delivery
        }
    )
