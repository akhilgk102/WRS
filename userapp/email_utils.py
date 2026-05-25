from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_html_email(subject, template_name, context, recipient):

    html_content = render_to_string(template_name, context)

    email = EmailMultiAlternatives(
        subject,
        "",
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
    )

    email.attach_alternative(html_content, "text/html")
    email.send()


def send_order_confirmation_email(order):

    send_html_email(
        subject=f"Order #{order.id} Confirmed",
        template_name="emails/order_confirmation.html",
        context={
            "order": order,
            "user": order.user,
        },
        recipient=order.user.email
    )


def send_order_shipped_email(order):

    send_html_email(
        subject=f"Order #{order.id} Shipped",
        template_name="emails/order_shipped.html",
        context={
            "order": order,
            "user": order.user,
        },
        recipient=order.user.email
    )


def send_order_delivered_email(order):

    send_html_email(
        subject=f"Order #{order.id} Delivered",
        template_name="emails/order_delivered.html",
        context={
            "order": order,
            "user": order.user,
        },
        recipient=order.user.email
    )


def send_order_cancelled_email(order):

    send_html_email(
        subject=f"Order #{order.id} Cancelled",
        template_name="emails/order_cancelled.html",
        context={
            "order": order,
            "user": order.user,
        },
        recipient=order.user.email
    )


def send_welcome_email(user):

    send_html_email(
        subject="Welcome to WRS Office Automation",
        template_name="emails/welcome_email.html",
        context={
            "user": user,
        },
        recipient=user.email
    )