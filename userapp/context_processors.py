from adminapp.models import Category

def categories_processor(request):
    """Make categories available in all templates"""
    return {
        'all_categories': Category.objects.all()
    }


from userapp.models import Cart

# userapp/context_processors.py

from decimal import Decimal
from .models import Cart


def cart_context(request):
    """
    Makes cart summary (subtotal, tax, shipping, total) available
    in every template — not just the cart page.
    """

    if not request.user.is_authenticated:
        return {
            "cart": None,
            "subtotal": Decimal("0"),
            "discount": Decimal("0"),
            "shipping_cost": Decimal("0"),
            "tax_rate": Decimal("5"),
            "tax": Decimal("0"),
            "total": Decimal("0"),
        }

    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = None

    if not cart or not cart.items.exists():
        return {
            "cart": cart,
            "subtotal": Decimal("0"),
            "discount": Decimal("0"),
            "shipping_cost": Decimal("0"),
            "tax_rate": Decimal("5"),
            "tax": Decimal("0"),
            "total": Decimal("0"),
        }

    # ── Subtotal (always use final_price = offer_price if set, else price) ──
    subtotal = sum(
        Decimal(str(item.product.final_price)) * item.quantity
        for item in cart.items.select_related("product").all()
    )

    # ── Coupon discount from session ──
    discount = Decimal(request.session.get("coupon_discount", "0"))
    if discount > subtotal:
        discount = subtotal

    # ── Shipping: free if subtotal ≥ 500, else AED 50 ──
    shipping_cost = Decimal("50") if subtotal < Decimal("500") else Decimal("0")

    # ── Tax (5%) applied after discount ──
    tax_rate = Decimal("5")
    tax = (subtotal - discount) * tax_rate / Decimal("100")

    # ── Grand total ──
    total = subtotal - discount + shipping_cost + tax

    return {
        "cart": cart,
        "subtotal": subtotal,
        "discount": discount,
        "shipping_cost": shipping_cost,
        "tax_rate": tax_rate,
        "tax": tax,
        "total": total,
    }