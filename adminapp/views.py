from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model, login, authenticate, logout
from django.utils.text import slugify
from .models import *
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from userapp.models import *

User = get_user_model()

def index(request):
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
    }

    return render(request, 'index.html', context)

# Add these views to your views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages

@staff_member_required
def homepage_sections_manage(request):
    sections = HomepageSection.objects.all().prefetch_related(
        'homepage_products__product__category',
        'categories'
    )
    categories = Category.objects.all()

    # Map section → category → products
    section_category_products = {}

    for section in sections:
        category_map = {}

        for category in section.categories.all():
            category_map[category] = Product.objects.filter(
                category=category
            )

        section_category_products[section.id] = category_map

    return render(request, 'homepage/section.html', {
        'sections': sections,
        'categories': categories,
        'section_category_products': section_category_products,
    })



@staff_member_required
def homepage_section_add_product(request, section_id):
    """Add product to a homepage section"""
    section = get_object_or_404(HomepageSection, id=section_id)
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            
            # Check if already exists
            if not HomepageProduct.objects.filter(section=section, product=product).exists():
                HomepageProduct.objects.create(section=section, product=product)
                messages.success(request, f'{product.name} added to {section.name}')
            else:
                messages.warning(request, f'{product.name} is already in {section.name}')
        
        return redirect('homepage_sections_manage')
    
    # Get products not in this section
    existing_product_ids = section.homepage_products.values_list('product_id', flat=True)
    available_products = Product.objects.exclude(id__in=existing_product_ids).select_related('category')
    
    return render(request, 'homepage/add_product.html', {
        'section': section,
        'products': available_products
    })


@staff_member_required
def homepage_product_remove(request, hp_id):
    """Remove product from homepage section"""
    hp = get_object_or_404(HomepageProduct, id=hp_id)
    section_name = hp.section.name
    product_name = hp.product.name
    hp.delete()
    messages.success(request, f'{product_name} removed from {section_name}')
    return redirect('homepage_sections_manage')


@staff_member_required
def homepage_section_toggle(request, section_id):
    """Toggle section active status"""
    section = get_object_or_404(HomepageSection, id=section_id)
    section.is_active = not section.is_active
    section.save()
    status = "activated" if section.is_active else "deactivated"
    messages.success(request, f'{section.name} {status}')
    return redirect('homepage_sections_manage')


@staff_member_required
def homepage_section_update_categories(request, section_id):
    section = get_object_or_404(HomepageSection, id=section_id)

    if request.method == 'POST':
        category_ids = request.POST.getlist('categories')
        section.categories.set(category_ids)
        messages.success(request, "Categories updated successfully")

    return redirect('homepage_sections_manage')




def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user:
            login(request, user)
            return redirect('dashboard' if user.is_staff else 'user_home')

        messages.error(request, "Invalid email or password")
        return redirect('index')

    return redirect('index')


def logout_view(request):
    logout(request)
    return redirect('/')  # redirect to login page


def register_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('register')

        if mobile and User.objects.filter(mobile=mobile).exists():
            messages.error(request, "Mobile already exists")
            return redirect('register')

        # ✅ Creates user and hashes password correctly
        user = User.objects.create_user(
            email=email,
            mobile=mobile,
            password=password
        )

        # ✅ This is REQUIRED because you have 2 authentication backends (allauth + ModelBackend)
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)

        messages.success(request, "Account created successfully!")
        return redirect('index')

    return render(request, 'register.html')


from django.db.models import Sum, Prefetch, Count
from django.db.models.functions import TruncMonth, TruncDay
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

@login_required
def dashboard(request):
    # Check if user is admin/staff
    if not request.user.is_staff:
        messages.error(request, "Access denied")
        return redirect('index')
    
    # Get statistics
    total_users = User.objects.filter(is_staff=False).count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    
    # Calculate total revenue from all completed orders
    total_revenue = Order.objects.filter(
        # status__in=['delivered', 'completed']
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # Recent statistics (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # New users in last 30 days
    new_users_30_days = User.objects.filter(
        date_joined__gte=thirty_days_ago,
        is_staff=False
    ).count()
    
    # New orders in last 30 days
    new_orders_30_days = Order.objects.filter(
        created_at__gte=thirty_days_ago
    ).count()
    
    # Revenue in last 30 days
    revenue_30_days = Order.objects.filter(
        created_at__gte=thirty_days_ago,
        # status__in=['delivered', 'completed']
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # New products in last 30 days
    new_products_30_days = Product.objects.filter(
        created_at__gte=thirty_days_ago
    ).count() if hasattr(Product, 'created_at') else 0
    
    # Weekly user registration data for bar chart (last 7 days aligned to week)
    today = timezone.now().date()
    
    # Get the current day of week (0=Monday, 6=Sunday)
    current_weekday = today.weekday()
    
    # Calculate days since last Sunday
    # In Python's weekday: Monday=0, Sunday=6
    # We want: Sunday=0, Saturday=6
    days_since_sunday = (current_weekday + 1) % 7
    
    # Get last Sunday's date
    last_sunday = today - timedelta(days=days_since_sunday)
    
    # Get daily user counts from last Sunday to today
    daily_users = User.objects.filter(
        date_joined__date__gte=last_sunday,
        date_joined__date__lte=today,
        is_staff=False
    ).annotate(
        day=TruncDay('date_joined')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Create a dictionary of dates to counts
    user_counts_dict = {
        item['day'].date(): item['count'] 
        for item in daily_users
    }
    
    # Create array for the week (Sunday to Saturday)
    weekly_user_data = []
    for i in range(7):  # 0 to 6 (Sunday to Saturday)
        date = last_sunday + timedelta(days=i)
        weekly_user_data.append(user_counts_dict.get(date, 0))
    
    # Debug print (you can remove these later)
    print(f"Today: {today} ({today.strftime('%A')})")
    print(f"Last Sunday: {last_sunday}")
    print(f"Weekly data: {weekly_user_data}")
    print(f"Days: {[(last_sunday + timedelta(days=i)).strftime('%A') for i in range(7)]}")
    
    # Monthly revenue for chart (last 12 months)
    current_year = timezone.now().year
    monthly_revenue = Order.objects.filter(
        created_at__year=current_year,
        # status__in=['delivered', 'completed']
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        revenue=Sum('total_price')
    ).order_by('month')
    
    # Create array of 12 months with revenue data
    monthly_data = [0] * 12
    for item in monthly_revenue:
        month_index = item['month'].month - 1
        monthly_data[month_index] = float(item['revenue'] or 0)
    
    # Recent orders
    recent_orders = Order.objects.select_related(
        'user', 
        'address'
    ).prefetch_related(
        'items__product__images'
    ).order_by('-created_at')[:5]
    
    # Latest registered users
    latest_users = User.objects.filter(
        is_staff=False
    ).order_by('-date_joined')[:5]
    
    # Recent products
    recent_products = Product.objects.select_related(
        'category'
    ).prefetch_related(
        'images'
    ).order_by('-id')[:5]
    
    # Stock products
    stock_products = Product.objects.select_related(
        'category'
    ).prefetch_related(
        'images'
    ).order_by('stock')[:5]
    
    context = {
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'new_users_30_days': new_users_30_days,
        'new_orders_30_days': new_orders_30_days,
        'revenue_30_days': revenue_30_days,
        'new_products_30_days': new_products_30_days,
        'recent_orders': recent_orders,
        'latest_users': latest_users,
        'recent_products': recent_products,
        'stock_products': stock_products,
        'monthly_revenue': monthly_data,
        'weekly_user_data': weekly_user_data,
    }
    
    return render(request, "dashboard.html", context)
@login_required
def user_dashboard(request):
    return render(request, "user_dashboard.html")


# Add this to your views.py file
from django.shortcuts import render
from django.db.models import Q
from .models import Product  # Adjust import based on your model location
from django.db.models import Q, Count




def category_create(request):
    if request.method == "POST":
        name = request.POST.get("name")

        if not name:
            messages.error(request, "Category name is required")
            return redirect("category_create")

        slug = slugify(name)

        # Prevent duplicate names
        if Category.objects.filter(slug=slug).exists():
            messages.error(request, "This category already exists.")
            return redirect("category_create")

        Category.objects.create(
            name=name,
            slug=slug
        )

        messages.success(request, "Category created successfully!")
        return redirect("category_list")

    return render(request, "categories/create.html")

def category_update(request, id):
    category = get_object_or_404(Category, id=id)

    if request.method == "POST":
        name = request.POST.get("name")
        if not name:
            messages.error(request, "Category name is required")
            return redirect("category_update", id=id)

        slug = slugify(name)

        # Prevent duplicate slug except itself
        if Category.objects.filter(slug=slug).exclude(id=id).exists():
            messages.error(request, "Another category with this name already exists.")
            return redirect("category_update", id=id)

        category.name = name
        category.slug = slug
        category.save()

        messages.success(request, "Category updated successfully!")
        return redirect("category_list")

    return render(request, "categories/create.html", {
        "edit": True,
        "category": category
    })


def category_list(request):
    categories = Category.objects.all()
    return render(request, "categories/list.html", {"categories": categories})

def category_delete(request, id):
    category = get_object_or_404(Category, id=id)
    category.delete()
    messages.success(request, "Category deleted successfully!")
    return redirect("category_list")


def subcategory_create(request):
    categories = Category.objects.all()

    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category")

        if not name or not category_id:
            messages.error(request, "All fields are required")
            return redirect("subcategory_create")

        category = Category.objects.get(id=category_id)
        slug = slugify(name)

        # Prevent duplicate subcategory under same category
        if SubCategory.objects.filter(category=category, slug=slug).exists():
            messages.error(request, "SubCategory already exists under this Category")
            return redirect("subcategory_create")

        SubCategory.objects.create(
            category=category,
            name=name,
            slug=slug
        )

        messages.success(request, "SubCategory created successfully!")
        return redirect("subcategory_list")

    return render(request, "subcategory/create.html", {"categories": categories,"edit": False})


def subcategory_list(request):
    subcategories = SubCategory.objects.select_related("category").all()
    return render(request, "subcategory/list.html", {"subcategories": subcategories})


def subcategory_update(request, id):
    sub = get_object_or_404(SubCategory, id=id)
    categories = Category.objects.all()

    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category")

        if not name or not category_id:
            messages.error(request, "All fields are required")
            return redirect("subcategory_update", id=id)

        category = Category.objects.get(id=category_id)
        slug = slugify(name)

        # prevent duplicate
        if SubCategory.objects.filter(category=category, slug=slug).exclude(id=id).exists():
            messages.error(request, "Another SubCategory with same name exists")
            return redirect("subcategory_update", id=id)

        sub.name = name
        sub.slug = slug
        sub.category = category
        sub.save()

        messages.success(request, "SubCategory updated successfully!")
        return redirect("subcategory_list")

    return render(request, "subcategory/create.html", {
        "subcategory": sub,
        "categories": categories,
        "edit": True
    })


def subcategory_delete(request, id):
    sub = get_object_or_404(SubCategory, id=id)
    sub.delete()
    messages.success(request, "SubCategory deleted successfully!")
    return redirect("subcategory_list")


def brand_create(request):
    if request.method == "POST":
        name = request.POST.get("name")

        if not name:
            messages.error(request, "Brand name is required")
            return redirect("brand_create")

        # check duplicates
        if Brand.objects.filter(name__iexact=name).exists():
            messages.error(request, "This brand already exists")
            return redirect("brand_create")

        Brand.objects.create(name=name)
        messages.success(request, "Brand created successfully!")
        return redirect("brand_list")

    return render(request, "brand/create.html", {"edit": False})


def brand_list(request):
    brands = Brand.objects.all().order_by("name")
    return render(request, "brand/list.html", {"brands": brands})



def brand_update(request, id):
    brand = get_object_or_404(Brand, id=id)

    if request.method == "POST":
        name = request.POST.get("name")

        if not name:
            messages.error(request, "Brand name is required")
            return redirect("brand_update", id=id)

        # prevent duplicate names
        if Brand.objects.filter(name__iexact=name).exclude(id=id).exists():
            messages.error(request, "Another brand with this name exists")
            return redirect("brand_update", id=id)

        brand.name = name
        brand.save()

        messages.success(request, "Brand updated successfully!")
        return redirect("brand_list")

    return render(request, "brand/create.html", {"brand": brand,"edit": True})



def brand_delete(request, id):
    brand = get_object_or_404(Brand, id=id)
    brand.delete()
    messages.success(request, "Brand deleted successfully!")
    return redirect("brand_list")



def product_create(request):
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()
    brands = Brand.objects.all()

    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category")
        subcategory_id = request.POST.get("subcategory")
        brand_id = request.POST.get("brand")
        description = request.POST.get("description")
        price = request.POST.get("price")
        offer_price = request.POST.get("offer_price")
        stock = request.POST.get("stock")
        sku = request.POST.get("sku")
        is_featured = True if request.POST.get("is_featured") == "on" else False

        if not name or not category_id:
            messages.error(request, "Name and Category are required")
            return redirect("product_create")

        slug = slugify(name)

        if Product.objects.filter(slug=slug).exists():
            messages.error(request, "Product with this name already exists")
            return redirect("product_create")

        product = Product.objects.create(
            name=name,
            slug=slug,
            category=Category.objects.get(id=category_id),
            subcategory=SubCategory.objects.get(id=subcategory_id) if subcategory_id else None,
            brand=Brand.objects.get(id=brand_id) if brand_id else None,
            description=description,
            price=price or 0,
            offer_price=offer_price or 0,
            stock=stock or 0,
            sku=sku,
            is_featured=is_featured
        )

        messages.success(request, "Product created successfully!")
        return redirect("product_list")

    return render(request, "product/create.html", {
        "categories": categories,
        "subcategories": subcategories,
        "brands": brands,
        "edit": False
    })

def product_list(request):
    products = Product.objects.select_related("category", "subcategory", "brand").prefetch_related("images").all()
    
    # Filter by category if provided
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    # Filter by price range if provided
    price_range = request.GET.get('price')
    if price_range:
        if price_range == '0-99':
            products = products.filter(price__gte=0, price__lte=99.99)
        elif price_range == '100-199':
            products = products.filter(price__gte=100, price__lte=199.99)
        elif price_range == '200-plus':
            products = products.filter(price__gte=200)
    
    # Filter by color if provided
    color = request.GET.get('color')
    if color:
        products = products.filter(attributes__key='color', attributes__value__icontains=color).distinct()
    
    categories = Category.objects.all()
    
    # The primary_image property already handles getting the primary image
    # No need to assign it here since it's a @property
    
    # Add product count for each category
    for category in categories:
        category.product_count = Product.objects.filter(category=category).count()

    return render(request, "product/list.html", {
        "products": products,
        "categories": categories
    })

def product_detail(request, slug):
    """
    Display product details
    """
    product = get_object_or_404(
        Product.objects.select_related('category', 'subcategory', 'brand')
                       .prefetch_related('images', 'attributes'),
        slug=slug
    )

    context = {
        'product': product,
    }
    
    return render(request, 'product/detail.html', context)

def product_update(request, id):
    product = get_object_or_404(Product, id=id)

    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()
    brands = Brand.objects.all()

    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category")
        subcategory_id = request.POST.get("subcategory")
        brand_id = request.POST.get("brand")
        description = request.POST.get("description")
        price = request.POST.get("price")
        offer_price = request.POST.get("offer_price")
        stock = request.POST.get("stock")
        sku = request.POST.get("sku")
        is_featured = True if request.POST.get("is_featured") == "on" else False

        if not name:
            messages.error(request, "Name is required")
            return redirect("product_update", id=id)

        slug = slugify(name)

        if Product.objects.filter(slug=slug).exclude(id=id).exists():
            messages.error(request, "Another product with this name already exists")
            return redirect("product_update", id=id)

        product.name = name
        product.slug = slug
        product.category = Category.objects.get(id=category_id)
        product.subcategory = SubCategory.objects.get(id=subcategory_id) if subcategory_id else None
        product.brand = Brand.objects.get(id=brand_id) if brand_id else None
        product.description = description
        product.price = price or 0
        product.offer_price=offer_price or None
        product.stock = stock or 0
        product.sku = sku
        product.is_featured = is_featured
        product.save()

        messages.success(request, "Product updated successfully!")
        return redirect("product_list")

    return render(request, "product/create.html", {
        "product": product,
        "categories": categories,
        "subcategories": subcategories,
        "brands": brands,
        "edit": True
    })





def product_delete(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    messages.success(request, "Product deleted successfully!")
    return redirect("product_list")


def product_image_list(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == "POST":
        files = request.FILES.getlist("images")
        
        if not files:
            messages.error(request, "Please select at least one image")
        else:
            for img in files:
                ProductImage.objects.create(product=product, image=img)
            messages.success(request, "Images uploaded successfully!")
        
        return redirect("product_image_list", product_id=product_id)
    
    images = ProductImage.objects.filter(product=product)
    return render(request, "product_image/list.html", {
        "product": product,
        "images": images
    })
def product_image_make_primary(request, id):
    image = get_object_or_404(ProductImage, id=id)
    product = image.product

    # remove existing primary
    ProductImage.objects.filter(product=product).update(is_primary=False)

    # make selected primary
    image.is_primary = True
    image.save()

    messages.success(request, "Primary image set successfully!")
    return redirect("product_image_list", product_id=product.id)


def product_image_delete(request, id):
    image = get_object_or_404(ProductImage, id=id)
    product_id = image.product.id
    image.delete()

    messages.success(request, "Image deleted successfully!")
    return redirect("product_image_list", product_id=product_id)



def attribute_list(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    attributes = ProductAttribute.objects.filter(product=product)

    return render(request, "product_attribute/list.html", {
        "product": product,
        "attributes": attributes
    })

def attribute_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        key = request.POST.get("key")
        value = request.POST.get("value")

        if not key or not value:
            messages.error(request, "Both fields are required")
            return redirect("attribute_add", product_id=product_id)

        ProductAttribute.objects.create(
            product=product,
            key=key,
            value=value
        )

        messages.success(request, "Attribute added successfully!")
        return redirect("attribute_list", product_id=product_id)

    return render(request, "product_attribute/add.html", {"product": product})



def attribute_update(request, id):
    attribute = get_object_or_404(ProductAttribute, id=id)
    product = attribute.product

    if request.method == "POST":
        key = request.POST.get("key")
        value = request.POST.get("value")

        if not key or not value:
            messages.error(request, "Both fields are required")
            return redirect("attribute_update", id=id)

        attribute.key = key
        attribute.value = value
        attribute.save()

        messages.success(request, "Attribute updated successfully!")
        return redirect("attribute_list", product_id=product.id)

    return render(request, "product_attribute/add.html", {
        "attribute": attribute,
        "product": product,
        "edit": True

    })



def attribute_delete(request, id):
    attribute = get_object_or_404(ProductAttribute, id=id)
    product_id = attribute.product.id
    attribute.delete()

    messages.success(request, "Attribute deleted successfully!")
    return redirect("attribute_list", product_id=product_id)



# ORDER LIST
def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, "orders/order_list.html", {"orders": orders})

# ORDER DETAIL

from userapp.models import Order, STATUS_CHOICES

def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    items = order.items.all()

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, "Order status updated successfully.")
            return redirect("order_detail", pk=order.pk)

    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
            "items": items,
            "status_choices": STATUS_CHOICES,   # ✅ pass explicitly
        }
    )


# ORDER DELETE
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.delete()
    return redirect("order_list")



def user_list(request):
    users = User.objects.all().order_by("-date_joined")
    return render(request, "users/user_list.html", {"users": users})


# ----------------------
# USER DETAIL VIEW
# ----------------------
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from userapp.models import Order, Address

User = get_user_model()

def user_detail(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    
    # Get user's orders (recent 5)
    recent_orders = Order.objects.filter(user=user_obj).select_related('address').prefetch_related('items__product').order_by('-created_at')[:5]
    total_orders = Order.objects.filter(user=user_obj).count()
    
    # Calculate total spent
    total_spent = sum(order.total_price for order in Order.objects.filter(user=user_obj))
    
    # Get saved addresses
    saved_addresses = Address.objects.filter(user=user_obj).order_by('-id')
    
    context = {
        "user_obj": user_obj,
        "recent_orders": recent_orders,
        "total_orders": total_orders,
        "total_spent": total_spent,
        "saved_addresses": saved_addresses,
    }
    
    return render(request, "users/user_detail.html", context)


# ----------------------
# USER DELETE (simple delete like you asked)
# ----------------------
def user_delete(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    user_obj.delete()
    return redirect("user_list")

from datetime import datetime

from datetime import datetime

@login_required
def coupon_create(request):
    if not request.user.is_staff:
        return redirect("index")

    if request.method == "POST":
        code = request.POST.get("code", "").upper()
        discount = request.POST.get("discount")
        usage_limit = request.POST.get("usage_limit") or None



        valid_from = timezone.make_aware(
            datetime.strptime(request.POST["valid_from"], "%Y-%m-%dT%H:%M"),
            timezone.get_current_timezone()
        )

        valid_to = timezone.make_aware(
            datetime.strptime(request.POST["valid_to"], "%Y-%m-%dT%H:%M"),
            timezone.get_current_timezone()
        )


        if Coupon.objects.filter(code=code).exists():
            messages.error(request, "Coupon already exists")
            return redirect("coupon_create")

        Coupon.objects.create(
            code=code,
            discount=discount,
            valid_from=valid_from,
            valid_to=valid_to,
            usage_limit=usage_limit,
            is_active=True,
        )

        messages.success(request, "Coupon created successfully")
        return redirect("coupon_list")

    return render(request, "coupon/create.html")




@login_required
def coupon_list(request):
    if not request.user.is_staff:
        return redirect("index")

    coupons = Coupon.objects.all().order_by("-created_at")
    return render(request, "coupon/list.html", {"coupons": coupons})


@login_required
def coupon_update(request, id):
    if not request.user.is_staff:
        return redirect("index")

    coupon = get_object_or_404(Coupon, id=id)

    if request.method == "POST":
        coupon.code = request.POST.get("code", "").upper()
        coupon.discount = request.POST.get("discount")
        coupon.usage_limit = request.POST.get("usage_limit") or None
        coupon.is_active = request.POST.get("is_active") == "on"

        coupon.valid_from = timezone.make_aware(
            datetime.strptime(request.POST.get("valid_from"), "%Y-%m-%dT%H:%M")
        )
        coupon.valid_to = timezone.make_aware(
            datetime.strptime(request.POST.get("valid_to"), "%Y-%m-%dT%H:%M")
        )



        coupon.save()
        messages.success(request, "Coupon updated successfully")
        return redirect("coupon_list")

    return render(request, "coupon/create.html", {
        "coupon": coupon,
        "edit": True
    })



@login_required
def coupon_delete(request, id):
    if not request.user.is_staff:
        return redirect("index")

    Coupon.objects.filter(id=id).delete()
    messages.success(request, "Coupon deleted")
    return redirect("coupon_list")
