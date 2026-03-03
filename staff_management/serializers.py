from rest_framework import serializers
from .models import *


class CategoryMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryMaster
        fields = "__all__"

class StockItemSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = StockItem
        fields = "__all__"
        
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None
        

    
class RoomCleaningSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomCleaning
        fields = "__all__"
        # `end_time` will be provided by the frontend; keep only `created_at` read-only
        read_only_fields = ["created_at"]
        


class StockItemListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = StockItem
        fields = ["id", "item_name", "quantity", "description", "category_name"]



        
class LaundryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaundryLog
        fields = "__all__"




        
######################## serializers.py #############################
class OtherIncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherIncome
        fields = "__all__"
        
        
class SalesIncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesIncome
        fields = "__all__"

    
class PaymentVoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentVoucher
        fields = "__all__"
        read_only_fields = ["created_at"]

    def validate(self, data):
        paid_by = data.get("paid_by")

        # Cheque validation
        if paid_by == "Cheque" and not data.get("bank_details"):
            raise serializers.ValidationError(
                {"bank_details": "Bank details are required when payment is made by Cheque."}
            )

        # Online payment validation
        if paid_by == "Online" and not data.get("online_payment_mode"):
            raise serializers.ValidationError(
                {"online_payment_mode": "Online payment mode is required (GPay / PhonePe / etc.)."}
            )

        # Cleanup irrelevant fields
        if paid_by == "Cash":
            data["bank_details"] = ""
            data["online_payment_mode"] = ""

        if paid_by == "Cheque":
            data["online_payment_mode"] = ""

        if paid_by == "Online":
            data["bank_details"] = ""

        return data




    ############ serializers.py ############
class BaseExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseExpense
        fields = "__all__"

    def validate(self, data):
        # When partial update, get existing values from instance
        bill = data.get("bill_file", getattr(self.instance, "bill_file", None))
        voucher = data.get("voucher_file", getattr(self.instance, "voucher_file", None))
        voucher_no = data.get("voucher_no", getattr(self.instance, "voucher_no", None))

        # case 1: none uploaded
        if not bill and not voucher:
            raise serializers.ValidationError("Upload either bill_file or voucher_file.")

        # case 2: both uploaded
        if bill and voucher:
            raise serializers.ValidationError("You cannot upload both bill and voucher.")

        # case 3: voucher uploaded but no voucher_no
        if voucher and not voucher_no:
            raise serializers.ValidationError("voucher_no is required when uploading voucher_file.")

        # case 4: bill uploaded → voucher_no must be empty
        if bill and voucher_no and self.instance and not self.instance.voucher_file:
            raise serializers.ValidationError("voucher_no must be empty when uploading bill_file.")

        return data





class LaundryExpenseSerializer(BaseExpenseSerializer):
    class Meta(BaseExpenseSerializer.Meta):
        model = LaundryExpense


class CleaningExpenseSerializer(BaseExpenseSerializer):
    class Meta(BaseExpenseSerializer.Meta):
        model = CleaningExpense


class MessExpenseSerializer(BaseExpenseSerializer):
    class Meta(BaseExpenseSerializer.Meta):
        model = MessExpense


############## serializers.py #############

class SalaryExpenseSerializer(BaseExpenseSerializer):
    staff_code = serializers.CharField(required=True)

    class Meta(BaseExpenseSerializer.Meta):
        model = SalaryExpense
        fields = "__all__"


class CafeteriaExpenseSerializer(BaseExpenseSerializer):
    class Meta(BaseExpenseSerializer.Meta):
        model = CafeteriaExpense


class RentalExpenseSerializer(BaseExpenseSerializer):
    class Meta(BaseExpenseSerializer.Meta):
        model = RentalExpense


class MiscExpenseSerializer(BaseExpenseSerializer):
    class Meta(BaseExpenseSerializer.Meta):
        model = MiscellaneousExpense


class MaintenanceExpenseSerializer(BaseExpenseSerializer):
    class Meta(BaseExpenseSerializer.Meta):
        model = MaintenanceExpense


class CapitalExpenseSerializer(BaseExpenseSerializer):
    class Meta(BaseExpenseSerializer.Meta):
        model = CapitalExpense


class OtherExpenseSerializer(BaseExpenseSerializer):
    class Meta(BaseExpenseSerializer.Meta):
        model = OtherExpense






######################### serializers.py #######################

class BookingTypeMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingTypeMaster
        fields = "__all__"
        read_only_fields = ["created_at"]

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"
        read_only_fields = ("invoice_no", "created_at","source")
        
class BookingFetchSerializer(serializers.ModelSerializer):
    gst_percentage = serializers.SerializerMethodField()
    booking_type_name = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = "__all__"

    def get_booking_type_name(self, obj):
        # If booking_type is a string name, just return it
        # If it's an ID stored as a string, fetch the name
        if not obj.booking_type:
            return None
        
        try:
            # Try treating it as an ID/FK first
            return obj.booking_type.name
        except AttributeError:
            # If it's just a string, return the string itself
            return str(obj.booking_type)

    def get_gst_percentage(self, obj):
        try:
            # We need to find the actual Master record to get the percentage
            # This logic works whether booking_type is an ID or a Name string
            master = None
            if hasattr(obj.booking_type, 'id'):
                master = obj.booking_type
            else:
                # Search by name or ID depending on what's in your DB
                master = BookingTypeMaster.objects.filter(name=obj.booking_type).first() or \
                         BookingTypeMaster.objects.filter(id=obj.booking_type).first()
            
            return master.gst_percentage if master else 0
        except Exception:
            return 0

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Clean up the output for the React frontend
        data["booking_type"] = data.pop("booking_type_name", None)
        return data


        

class WebsiteBookingFetchSerializer(serializers.ModelSerializer):
    booking_source_label = serializers.CharField(
        source="get_booking_source_display",
        read_only=True
    )

    class Meta:
        model = Booking
        fields = "__all__"





        ############### serializers.py ##############

class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = [
            "id", "date", "source_type", "source_id", "description",
            "debit", "credit", "created_at"
        ]



