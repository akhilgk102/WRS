from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        # ✅ This ensures the password is hashed using set_password()
        password = form.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        user.save()
        return user
