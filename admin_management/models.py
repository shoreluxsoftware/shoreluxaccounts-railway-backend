from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_delete, pre_save



########### models.py #############

class CustomUserManager(UserManager):
    def create_superuser(self, username, password=None, email="", **extra_fields):
        extra_fields.setdefault('role', 'ADMIN')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return super().create_superuser(
            username=username,
            password=password,
            email=email,
            **extra_fields
        )


class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('STAFF', 'Staff'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STAFF')
    can_login = models.BooleanField(default=False)   # ✅ NEW FIELD
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    aadhaar_number = models.CharField(max_length=12, unique=True, null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)

    aadhaar_card = models.FileField(upload_to='aadhaar_cards/', null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)

    staff_unique_id = models.CharField(max_length=30, unique=True, null=True, blank=True)

    designation = models.CharField(max_length=100, blank=True, null=True) # ✅ NEW FIELD

    is_active_employee = models.BooleanField(default=True)

    objects = CustomUserManager()

    class Meta:
        db_table = 'users'
        ordering = ['-id']

    def save(self, *args, **kwargs):
        if self.role == "STAFF" and not self.staff_unique_id:
            prefix = "SHORELUXSTAFF"
            last_user = User.objects.filter(staff_unique_id__startswith=prefix).order_by('-id').first()

            last_num = int(last_user.staff_unique_id.replace(prefix, '')) if last_user else 0
            self.staff_unique_id = f"{prefix}{(last_num + 1):03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"


# Ensure files are removed from storage when a User is deleted
@receiver(post_delete, sender=User)
def delete_user_files(sender, instance, **kwargs):
    try:
        if instance.aadhaar_card:
            instance.aadhaar_card.delete(save=False)
    except Exception:
        pass

    try:
        if instance.profile_image:
            instance.profile_image.delete(save=False)
    except Exception:
        pass


# When replacing a file on an existing User, delete the old file to avoid orphaned files
@receiver(pre_save, sender=User)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return

    # Aadhaar card changed
    try:
        if old.aadhaar_card and old.aadhaar_card != instance.aadhaar_card:
            old.aadhaar_card.delete(save=False)
    except Exception:
        pass

    # Profile image changed
    try:
        if old.profile_image and old.profile_image != instance.profile_image:
            old.profile_image.delete(save=False)
    except Exception:
        pass





class OTPVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp = models.CharField(max_length=6)
    
    # Track what this OTP is for
    verification_type = models.CharField(max_length=50, choices=[
        ('booking_edit', 'Booking Edit'),
        ('expense_edit', 'Expense Edit'),
        ('sales_income_edit', 'Sales Income Edit'),
        ('other_income_edit', 'Other Income Edit'),
    ])
    
    # Link to the object being edited
    object_id = models.PositiveIntegerField(null=True, blank=True)
    
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-created_at']
    
    def is_valid(self):
        """Check if OTP hasn't expired"""
        return timezone.now() < self.expires_at
    
    def __str__(self):
        return f"OTP for {self.user.username} - {self.verification_type}"