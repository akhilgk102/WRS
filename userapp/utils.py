# userapp/utils.py (optional but clean)

from datetime import timedelta,timezone

def can_replace(order):
    if order.status != "DELIVERED":
        return False

    delivered_date = order.updated_at  # or delivered_at if you add it
    return delivered_date + timedelta(days=7) >= timezone.now()
