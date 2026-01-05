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

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Add these fields
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # ✅ ADD THIS
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="PLACED")

        # 🔥 COUPON FIELDS
    coupon = models.ForeignKey(Coupon,on_delete=models.SET_NULL,null=True,blank=True)
    discount_amount = models.DecimalField(max_digits=10,decimal_places=2,default=0)


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

    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} → {self.user.username}"


# Add this method to OrderItem model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"
    
    def get_total(self):
        """Calculate total for this order item"""
        return self.price * self.quantity


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    title = models.CharField(max_length=255)
    content = models.TextField()
    rating = models.PositiveIntegerField(default=5)  # 1–5 stars

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} Review by {self.user.username}"
