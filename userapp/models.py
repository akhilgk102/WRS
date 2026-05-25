# userapp/models
from django.db import models
from django.conf import settings   # ✅ add this
from adminapp.models import Product,Coupon

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # ✅ changed
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.user.username


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")  # ✅ changed
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    street = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    def __str__(self):
        return f" {self.street}, {self.city}, {self.state} - {self.pincode}"



class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")  # ✅ changed

    def __str__(self):
        return self.user.username


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def get_total_price(self):
        return self.product.final_price * self.quantity

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"


class Wishlist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist")  # ✅ changed

    def __str__(self):
        return self.user.username


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return self.product.name



STATUS_CHOICES = [
    ("PLACED", "Placed"),
    ("PROCESSING", "Processing"),
    ("SHIPPED", "Shipped"),
    ("DELIVERED", "Delivered"),
    ("CANCELLED", "Cancelled"),
]

# In userapp/models.py - Update the Order model

from django.db import models
from django.conf import settings
from django.db import models
from django.conf import settings
from django.utils import timezone
from adminapp.models import Product, Coupon
from .models import Address   # or wherever Address is defined


class Order(models.Model):

    STATUS_CHOICES = [
        ("PLACED", "Placed"),
        ("PROCESSING", "Processing"),
        ("SHIPPED", "Shipped"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    ]

    REFUND_STATUS_CHOICES = [
        ("NA", "Not Applicable"),
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True
    )

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Coupon
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Order status
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PLACED"
    )

    # Payment
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("NOT_PAID", "Not Paid"),
            ("PENDING", "Pending"),
            ("PAID", "Paid"),
            ("FAILED", "Failed"),
            ("REFUNDED", "Refunded"),
        ],
        default="NOT_PAID"
    )
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True)

    # 🔴 Cancellation & Refund
    cancel_reason = models.CharField(max_length=255, blank=True, null=True)

    refund_status = models.CharField(
        max_length=20,
        choices=REFUND_STATUS_CHOICES,
        default="NA"
    )

    refund_account_name = models.CharField(max_length=255, blank=True, null=True)
    refund_account_number = models.CharField(max_length=30, blank=True, null=True)
    refund_ifsc = models.CharField(max_length=15, blank=True, null=True)
    refund_bank_name = models.CharField(max_length=100, blank=True, null=True)

    cancelled_at = models.DateTimeField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} → {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    # Replacement
    replacement_requested = models.BooleanField(default=False)
    replacement_reason = models.TextField(blank=True, null=True)

    replacement_status = models.CharField(
        max_length=20,
        choices=[
            ("NA", "Not Applicable"),
            ("REQUESTED", "Requested"),
            ("APPROVED", "Approved"),
            ("REJECTED", "Rejected"),
            ("COMPLETED", "Completed"),
        ],
        default="NA"
    )

    replacement_requested_at = models.DateTimeField(blank=True, null=True)

    replacement_order = models.OneToOneField(
        "ReplacementOrder",   # ✅ STRING
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_item"
    )

    def mark_replacement_requested(self, reason):
        self.replacement_requested = True
        self.replacement_reason = reason
        self.replacement_status = "REQUESTED"
        self.replacement_requested_at = timezone.now()
        self.save()

    def get_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product} × {self.quantity}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    title = models.CharField(max_length=255)
    content = models.TextField()
    rating = models.PositiveIntegerField(default=5)  # 1–5 stars

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} Review by {self.user.username}"

class ReplacementOrder(models.Model):
    STATUS_CHOICES = [
        ("PROCESSING", "Processing"),
        ("SHIPPED", "Shipped"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="replacement_orders"
    )

    original_order = models.ForeignKey(
        "Order",   # ✅ STRING REFERENCE
        on_delete=models.CASCADE,
        related_name="replacement_orders"
    )

    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PROCESSING"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Replacement #{self.id}"


class ReplacementOrderItem(models.Model):
    replacement_order = models.ForeignKey(
        ReplacementOrder,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True
    )

    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product} × {self.quantity}"
