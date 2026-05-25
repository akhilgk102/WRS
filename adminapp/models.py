# adminapp/models
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    
    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=255)
    slug = models.SlugField()

    def __str__(self):
        return f"{self.category.name} → {self.name}"

class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)

    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)   # Original price
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # 🔥 Offer price
    stock = models.PositiveIntegerField(default=0)

    # brochures include many stationery variations
    sku = models.CharField(max_length=50, unique=True, null=True, blank=True)

    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    @property
    def primary_image(self):
        """Get the primary image for this product"""
        return self.images.filter(is_primary=True).first() or self.images.first()

    @property
    def final_price(self):
        """Return offer price if exists, else normal price"""
        return self.offer_price if self.offer_price else self.price


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attributes")
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.product.name} - {self.key}: {self.value}"






from django.db import models

# ... (keep your existing models)

class HomepageSection(models.Model):
    SECTION_CHOICES = [
        ('banner', 'Banner Products'),
        ('featured', 'Featured Products'),
        ('deals', 'Deals of the Day'),
        ('new_arrival', 'New Arrivals'),
        ('best_seller', 'Best Sellers'),
    ]

    DISPLAY_TYPE = [
        ('manual', 'Manual Products'),
        ('category', 'By Category'),
    ]

    name = models.CharField(max_length=100)
    section_type = models.CharField(max_length=20, choices=SECTION_CHOICES, unique=True)
    display_type = models.CharField(
        max_length=20, choices=DISPLAY_TYPE, default='manual'
    )

    categories = models.ManyToManyField(
        Category, blank=True, related_name='homepage_sections'
    )

    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.name



class HomepageProduct(models.Model):
    """Products assigned to homepage sections"""
    section = models.ForeignKey(HomepageSection, on_delete=models.CASCADE, related_name='homepage_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    display_order = models.IntegerField(default=0)
    
    
    class Meta:
        ordering = ['display_order']
        unique_together = ['section', 'product']
    
    def __str__(self):
        return f"{self.product.name} in {self.section.name}"




from django.db import models
from django.utils import timezone

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True, null=True)


    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    from django.utils import timezone

    def is_valid(self):
        now = timezone.now()

        valid_from = timezone.localtime(self.valid_from)
        valid_to = timezone.localtime(self.valid_to)

        if not self.is_active:
            return False

        if not (valid_from <= now <= valid_to):
            return False

        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False

        return True


    def __str__(self):
        return self.code


from django.conf import settings



class CouponUsage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE
    )

    order = models.ForeignKey(
        "userapp.Order",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "coupon")

    def __str__(self):
        return f"{self.user.email} used {self.coupon.code}"