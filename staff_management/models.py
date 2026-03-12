from django.db import models
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class CategoryMaster(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class StockItem(models.Model):
    date = models.DateField()
    category = models.ForeignKey(CategoryMaster, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.item_name} ({self.category.name}) - {self.date}"  
        
    
# ---------------------------
#  ROOM CLEANING MODEL 
# ---------------------------
class RoomCleaning(models.Model):
    room_number = models.CharField(max_length=10)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)

    # Username of staff who performed the cleaning (provided by frontend)
    username = models.CharField(max_length=150, blank=True)

    products_used = models.JSONField(
        default=list,
        help_text='Example: [{"item_id":1,"item_name": "Floor Cleaner", "quantity": 2}]'
    )

    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Do not auto-calculate `end_time` here. Frontend should supply it.
        super().save(*args, **kwargs)





# ---------------------------
#  LAUNDRY LOG MODEL
# ---------------------------
############## models.py ################

class LaundryLog(models.Model):
    date = models.DateField()  # When items were sent to laundry
    
    company_name = models.CharField(max_length=255)   # ✅ NEW FIELD

    products_used = models.JSONField(
        default=list,
        help_text='Example: [{"item_id":1,"item_name": "Bedsheet", "quantity": 10}]'
    )

    description = models.TextField(blank=True)

    received_date = models.DateField(blank=True, null=True)
    received_quantity = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Laundry on {self.date} - {self.company_name}"





        ############################## models.py #####################

# ---------------------------
#  OTHER INCOME MODEL
# ---------------------------
class OtherIncome(models.Model):
    date = models.DateField()

    # simple category text
    category = models.CharField(max_length=200)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.category} - {self.amount}"


# ---------------------------
#  SALES INCOME MODEL
# ---------------------------
class SalesIncome(models.Model):
    date = models.DateField()

    # simple category text
    category = models.CharField(max_length=200)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.category} - {self.amount}"
    




#---------------------------
#  PAYMENT VOUCHER MODEL
#---------------------------
#---------------------------
#  PAYMENT VOUCHER MODEL
#---------------------------
class PaymentVoucher(models.Model):
    VOUCHER_PREFIX = "SHLVR"

    voucher_no = models.CharField(max_length=20, unique=True, blank=True)
    date = models.DateField()

    paid_to = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    being = models.TextField(blank=True)

    # Cash / Cheque / Online
    paid_by = models.CharField(
        max_length=20,
        choices=[
            ("Cash", "Cash"),
            ("Cheque", "Cheque"),
            ("Online", "Online"),
        ]
    )

    bank_details = models.CharField(max_length=200, blank=True, null=True)

    # ✅ NEW FIELD
    online_payment_mode = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="GPay / PhonePe / Paytm / UPI / NetBanking"
    )

    authorized_by = models.CharField(max_length=200)

    receiver_signature_name = models.CharField(max_length=200)
    receiver_signature = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.voucher_no} - {self.paid_to}"

    # Generate voucher number while saving ONLY IF not provided already
    def save(self, *args, **kwargs):
        if not self.voucher_no:
            self.voucher_no = self.generate_voucher_no()
        super().save(*args, **kwargs)

    # For saving
    def generate_voucher_no(self):
        prefix = self.VOUCHER_PREFIX
        last = PaymentVoucher.objects.order_by("id").last()
        if not last:
            return f"{prefix}001"
        last_number = int(last.voucher_no.replace(prefix, ""))
        new_number = last_number + 1
        return f"{prefix}{new_number:03d}"

    # For frontend preview before saving
    @classmethod
    def get_next_voucher_no(cls):
        prefix = cls.VOUCHER_PREFIX
        last = cls.objects.order_by("id").last()
        if not last:
            return f"{prefix}001"
        last_number = int(last.voucher_no.replace(prefix, ""))
        new_number = last_number + 1
        return f"{prefix}{new_number:03d}"



############ models #######

class BaseExpense(models.Model):
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    bill_file = models.FileField(upload_to="expenses/bills/", blank=True, null=True)
    voucher_file = models.FileField(upload_to="expenses/vouchers/", blank=True, null=True)
    voucher_no = models.CharField(max_length=50, blank=True, null=True)


    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.amount} - {self.date}"
    

    # ---------------------------
#  INDIVIDUAL CATEGORY MODELS
# ---------------------------

class LaundryExpense(BaseExpense):
    pass

class CleaningExpense(BaseExpense):
    pass

class MessExpense(BaseExpense):
    pass

class CafeteriaExpense(BaseExpense):
    pass

class RentalExpense(BaseExpense):
    pass

############### models.py ##############

class SalaryExpense(BaseExpense):
    staff_code = models.CharField(max_length=50)
    designation = models.CharField(max_length=100)  # 🔥 NEW
    salary_type = models.CharField(                 # 🔥 NEW
        max_length=20,
        choices=[
            ('daily_wage', 'Daily Wage'),
            ('monthly', 'Monthly')
        ],
        default='daily_wage'
    )


class MiscellaneousExpense(BaseExpense):
    pass

class MaintenanceExpense(BaseExpense):
    pass

class CapitalExpense(BaseExpense):
    pass

class OtherExpense(BaseExpense):
    pass








# ---------------------------
#  BOOKING MODEL
# ---------------------------

class BookingTypeMaster(models.Model):
    name = models.CharField(max_length=100, unique=True)   # Corporate / Regular / VIP
    default_price = models.DecimalField(max_digits=12, decimal_places=2)
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.default_price}"
    


class Booking(models.Model):
    INVOICE_PREFIX = "SHLINV"
    
    SOURCE_CHOICES = (
        (0, "STAFF"),
        (1, "WEBSITE"),
    )

    # Auto generated on save
    invoice_no = models.CharField(max_length=20, unique=True, blank=True)

    booking_date = models.DateField()
    guest_name = models.CharField(max_length=200)
    room_no = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    # Stores booking type name or ID (your current setup)
    booking_type = models.CharField(max_length=50, blank=True, null=True)

    checkin_date = models.DateTimeField() # data type changed from DateField to DateTimeField
    checkout_date = models.DateTimeField() # data type changed from DateField to DateTimeField

    booking_price = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2)
    pending_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # NEW FIELD
    source = models.PositiveSmallIntegerField(
        choices=SOURCE_CHOICES,
        default=0
    )

    website_item_id = models.CharField(max_length=50,unique=True,null=True,blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.guest_name} - {self.room_no}"

    # Auto-generate invoice number only if not already assigned
    def save(self, *args, **kwargs):
        if not self.invoice_no:
            self.invoice_no = self.generate_invoice_no()
        super().save(*args, **kwargs)

    # BACKEND GENERATOR
    def generate_invoice_no(self):
        prefix = self.INVOICE_PREFIX
        last = Booking.objects.order_by("id").last()

        # No previous invoice — start at 001
        if not last or not last.invoice_no:
            return f"{prefix}001"

        # Extract number from last invoice_no
        try:
            last_number = int(last.invoice_no.replace(prefix, ""))
        except:
            last_number = 0

        new_number = last_number + 1
        return f"{prefix}{new_number:03d}"

    # FRONTEND PREVIEW (Without saving)
    @classmethod
    def get_next_invoice_no(cls):
        prefix = cls.INVOICE_PREFIX
        last = cls.objects.order_by("id").last()

        if not last or not last.invoice_no:
            return f"{prefix}001"

        try:
            last_number = int(last.invoice_no.replace(prefix, ""))
        except:
            last_number = 0

        return f"{prefix}{last_number + 1:03d}"

#----------------------
#  Ledger Model
#----------------------
class LedgerEntry(models.Model):
    """
    Unified ledger entry. Each source object (income/expense/booking) will create one
    or more LedgerEntry rows. Use source_type+source_id to find & manage entries.
    """
    date = models.DateField()
    # source_type values: 'salesincome', 'otherincome', 'booking', 'laundryexpense', ...
    source_type = models.CharField(max_length=100, db_index=True)
    source_id = models.PositiveIntegerField(db_index=True)
    description = models.TextField(blank=True)

    # Debit / Credit accounting amounts. One of them will be non-zero.
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["source_type", "source_id"]),
        ]
        ordering = ["date", "id"]

    def __str__(self):
        return f"{self.date} | {self.source_type}:{self.source_id} | D:{self.debit} C:{self.credit}"