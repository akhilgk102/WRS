from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        password = form.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        user.save()
        return user

    def get_login_redirect_url(self, request):
        next_url = request.GET.get("next")
        if next_url:
            return next_url
        return super().get_login_redirect_url(request)


# 🔥 THIS IS THE MISSING PIECE
class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Auto-link Google account to existing user with same email
        and SKIP the signup page completely.
        """

        # If already logged in → do nothing
        if request.user.is_authenticated:
            return

        email = sociallogin.account.extra_data.get("email")
        if not email:
            return

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return

        # 🔥 Connect Google account to existing user
        sociallogin.connect(request, user)
