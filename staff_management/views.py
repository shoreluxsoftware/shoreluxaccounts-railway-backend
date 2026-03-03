from rest_framework.views import APIView
from rest_framework.response import Response

from .models import *
from .serializers import *
from django.db import transaction
from rest_framework.permissions import AllowAny

from rest_framework import status,permissions
from decimal import Decimal
from django.shortcuts import get_object_or_404

from admin_management.models import OTPVerification
from rest_framework.permissions import IsAuthenticated
from admin_management.models import *




from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear
from rest_framework.views import APIView
from rest_framework.response import Response

CATEGORY_MODEL_MAP = {
    "Laundry": (LaundryExpense, LaundryExpenseSerializer),
    "Cleaning": (CleaningExpense, CleaningExpenseSerializer),
    "Mess": (MessExpense, MessExpenseSerializer),
    "Salary": (SalaryExpense, SalaryExpenseSerializer),
    "Cafeteria": (CafeteriaExpense, CafeteriaExpenseSerializer),
    "Rental": (RentalExpense, RentalExpenseSerializer),
    "Miscellaneous": (MiscellaneousExpense, MiscExpenseSerializer),
    "Maintenance": (MaintenanceExpense, MaintenanceExpenseSerializer),
    "Capital": (CapitalExpense, CapitalExpenseSerializer),
    "Other Expenses": (OtherExpense, OtherExpenseSerializer),
}
################# Stock Management APIs  ###############################

# -----------------------------------------------
# CATEGORY MASTER APIs
# -----------------------------------------------

class AddCategoryAPIView(APIView):

    def post(self, request):
        serializer = CategoryMasterSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Category added successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ListCategoryAPIView(APIView):

    def get(self, request):
        categories = CategoryMaster.objects.all()
        serializer = CategoryMasterSerializer(categories, many=True)
        return Response(serializer.data, status=200)


class DeleteCategoryAPIView(APIView):
    
    def delete(self, request, pk):
        try:
            category = CategoryMaster.objects.get(pk=pk)
        except CategoryMaster.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)

        category.delete()

        return Response({"message": "Category deleted successfully"}, status=200)


# -----------------------------------------------
# STOCK ITEM APIs
# -----------------------------------------------

class AddStockItemAPIView(APIView):

    def post(self, request):
        serializer = StockItemSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Stock item added successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListStockItemAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        items = StockItem.objects.all()
        serializer = StockItemSerializer(items, many=True)
        return Response({"data": serializer.data}, status=200)


class UpdateStockItemAPIView(APIView):
    def put(self, request, pk):
        try:
            item = StockItem.objects.get(pk=pk)
        except StockItem.DoesNotExist:
            return Response({"error": "Stock item not found"}, status=404)

        # Allow only quantity updates
        if "quantity" not in request.data:
            return Response({"error": "Only 'quantity' field can be updated"}, status=400)

        qty = request.data.get("quantity")
        try:
            qty_int = int(qty)
        except (TypeError, ValueError):
            return Response({"error": "Quantity must be an integer"}, status=400)

        if qty_int < 0:
            return Response({"error": "Quantity cannot be negative"}, status=400)

        item.quantity = qty_int
        item.save()

        serializer = StockItemSerializer(item)
        return Response({
            "message": "Stock item quantity updated successfully",
            "data": serializer.data
        }, status=200)
    

class DeleteStockItemAPIView(APIView):
    
    def delete(self, request, pk):
        try:
            item = StockItem.objects.get(pk=pk)
        except StockItem.DoesNotExist:
            return Response({"error": "Stock item not found"}, status=404)

        item.delete()
        return Response({"message": "Stock item deleted successfully"}, status=204)

###############################  ################################

class LogRoomCleaningAPIView(APIView):
    
    @transaction.atomic
    def post(self, request):
        products_used = request.data.get("products_used", [])

        # 1️⃣ Validate stock availability
        for item in products_used:
            item_id = item["item_id"]
            qty_needed = item["quantity"]

            try:
                stock_item = StockItem.objects.get(id=item_id)
            except StockItem.DoesNotExist:
                return Response({"error": f"Stock item {item_id} not found"}, status=404)

            if stock_item.quantity < qty_needed:
                return Response({
                    "error": f"Insufficient stock for {stock_item.item_name}",
                    "available": stock_item.quantity,
                    "required": qty_needed
                }, status=400)

        # 2️⃣ Save cleaning log
        serializer = RoomCleaningSerializer(data=request.data)
        if serializer.is_valid():
            cleaning_log = serializer.save()

            # 3️⃣ Deduct stock
            for item in products_used:
                stock_item = StockItem.objects.get(id=item["item_id"])
                stock_item.quantity -= item["quantity"]
                stock_item.save()

            return Response({
                "message": "Room cleaning logged successfully & stock updated",
                "data": RoomCleaningSerializer(cleaning_log).data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



######################### commented out code #########################
# class DeleteStockItemAPIView(APIView):

#     def delete(self, request, pk):
#         try:
#             item = StockItem.objects.get(pk=pk)
#         except StockItem.DoesNotExist:
#             return Response({"error": "Stock item not found"}, status=404)

#         item.delete()

#         return Response({"message": "Stock item deleted successfully"}, status=200)







#-----------------------------------------
# ROOM CLEANING item LIST API
#-----------------------------------------
class GetRoomCleaningItemsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            category = CategoryMaster.objects.get(name="Room Cleaning")
        except CategoryMaster.DoesNotExist:
            return Response(
                {"error": "Room Cleaning category not found"},
                status=404
            )

        items = StockItem.objects.filter(category=category)

        serializer = StockItemListSerializer(items, many=True)
        return Response({"data": serializer.data}, status=200)
    
#---------------------------
# Laundry item api
#---------------------------
class GetLaundryItemsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            category = CategoryMaster.objects.get(name="Laundry")
        except CategoryMaster.DoesNotExist:
            return Response(
                {"error": "Laundry category not found"},
                status=404
            )

        items = StockItem.objects.filter(category=category)

        serializer = StockItemListSerializer(items, many=True)
        return Response({"data": serializer.data}, status=200)
    
    #---------------------------
# List log cleaning API
#--------------------------
class ListRoomCleaningItemsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        cleanings = RoomCleaning.objects.all()
        serializer = RoomCleaningSerializer(cleanings, many=True)
        return Response({"data": serializer.data}, status=200)
    

    
#------------------------------------------
# log laundry API
#------------------------------------------

class CreateLaundryLogAPIView(APIView):
    def post(self, request):
        serializer = LaundryLogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Laundry log created", "data": serializer.data})
        return Response(serializer.errors, status=400)

class ListLaundryLogAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        logs = LaundryLog.objects.all()
        serializer = LaundryLogSerializer(logs, many=True)
        return Response({"data": serializer.data}, status=200)

class UpdateLaundryReceivedAPIView(APIView):
    def patch(self, request, pk, item_id):
        try:
            log = LaundryLog.objects.get(pk=pk)
        except LaundryLog.DoesNotExist:
            return Response({"error": "Laundry log not found"}, status=404)

        data = request.data
        received_quantity = data.get("received_quantity")
        received_date = data.get("received_date")

        if received_quantity is None or received_date is None:
            return Response(
                {"error": "received_quantity and received_date are required"},
                status=400
            )

        updated = False
        products = log.products_used

        # Loop items in JSON
        for item in products:
            if str(item.get("item_id")) == str(item_id):

                # Add new keys to the specific item
                item["received_quantity"] = received_quantity
                item["received_date"] = received_date

                updated = True
                break

        if not updated:
            return Response({"error": "Item not found in products_used"}, status=404)

        log.products_used = products
        log.save()

        return Response({
            "message": "Laundry item updated",
            "data": log.products_used
        })
    


    ############################ views.py ##################################
# -----------------------
# OTHER INCOME APIs
# -----------------------
class CreateOtherIncomeAPIView(APIView):
    def post(self, request):
        serializer = OtherIncomeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Other income added", "data": serializer.data})
        return Response(serializer.errors, status=400)
    
    
class ListOtherIncomeAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        incomes = OtherIncome.objects.all()
        serializer = OtherIncomeSerializer(incomes, many=True)
        return Response({"data": serializer.data}, status=200)
    
# -----------------------
# SALES INCOME APIs
# -----------------------
class CreateSalesIncomeAPIView(APIView):
    def post(self, request):
        serializer = SalesIncomeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Sale record added", "data": serializer.data})
        return Response(serializer.errors, status=400)
    
    
class ListSalesIncomeAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        sales = SalesIncome.objects.all()
        serializer = SalesIncomeSerializer(sales, many=True)
        return Response({"data": serializer.data}, status=200)
    

###################### otp edit #############

def verify_otp_for_edit(request, verification_type):
    """
    Check if OTP is verified for the given action.
    Returns: (is_valid, error_message)
    """
    try:
        otp_record = OTPVerification.objects.filter(
            user=request.user,
            verification_type=verification_type,
            is_verified=True
        ).latest('created_at')
    except OTPVerification.DoesNotExist:
        return False, "OTP verification required. Please verify OTP first."
    
    # Check if OTP verification is within 5 minutes (freshness)
    if timezone.now() - otp_record.created_at > timedelta(minutes=5):
        return False, "OTP verification expired. Please verify again."
    
    return True, None


# ===================================
# UPDATED EDIT EXPENSE API
# ===================================
class UpdateExpenseAPIView(APIView):
    def put(self, request, pk):
        # Verify OTP first
        is_verified, error = verify_otp_for_edit(request, 'expense_edit')
        if not is_verified:
            return Response({"error": error}, status=status.HTTP_403_FORBIDDEN)
        
        category = request.data.get("category")

        if category not in CATEGORY_MODEL_MAP:
            return Response({"error": "Invalid category"}, status=400)

        ModelClass, SerializerClass = CATEGORY_MODEL_MAP[category]

        try:
            obj = ModelClass.objects.get(pk=pk)
        except ModelClass.DoesNotExist:
            return Response({"error": "Record not found"}, status=404)

        serializer = SerializerClass(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Updated", "data": serializer.data})

        return Response(serializer.errors, status=400)


# ===================================
# UPDATED EDIT SALES INCOME API
# ===================================
class UpdateSalesIncomeAPIView(APIView):
    def put(self, request, pk):
        # Verify OTP first
        is_verified, error = verify_otp_for_edit(request, 'sales_income_edit')
        if not is_verified:
            return Response({"error": error}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            sale = SalesIncome.objects.get(pk=pk)
        except SalesIncome.DoesNotExist:
            return Response({"error": "Sales income record not found"}, status=404)

        serializer = SalesIncomeSerializer(sale, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Sales income record updated successfully",
                "data": serializer.data
            })

        return Response(serializer.errors, status=400)


# ===================================
# UPDATED EDIT OTHER INCOME API
# ===================================
class UpdateOtherIncomeAPIView(APIView):
    def put(self, request, pk):
        # Verify OTP first
        is_verified, error = verify_otp_for_edit(request, 'other_income_edit')
        if not is_verified:
            return Response({"error": error}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            income = OtherIncome.objects.get(pk=pk)
        except OtherIncome.DoesNotExist:
            return Response({"error": "Other income record not found"}, status=404)

        serializer = OtherIncomeSerializer(income, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Other income record updated successfully",
                "data": serializer.data
            })

        return Response(serializer.errors, status=400)



####################### views.py ########################
# ------------------------------------
# 1. API → Get next voucher number
# ------------------------------------
class NextVoucherNumberAPIView(APIView):
    def get(self, request):
        next_no = PaymentVoucher.get_next_voucher_no()
        return Response({"next_voucher_no": next_no}, status=200)


# ------------------------------------
# 2. Create voucher
# ------------------------------------
class CreatePaymentVoucherAPIView(APIView):
   
    def post(self, request):
        serializer = PaymentVoucherSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Voucher created", "data": serializer.data}, status=201)
        return Response(serializer.errors, status=400)

# ------------------------------------
# 3. List all vouchers
# ------------------------------------
class ListPaymentVouchersAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        vouchers = PaymentVoucher.objects.all().order_by("-id")
        serializer = PaymentVoucherSerializer(vouchers, many=True)
        return Response({"data": serializer.data}, status=200)



# ----------------------- 
#  EXPENSE APIs 
# -----------------------
class CreateExpenseAPIView(APIView):
    def post(self, request):
        category = request.data.get("category")

        if category not in CATEGORY_MODEL_MAP:
            return Response({"error": "Invalid category"}, status=400)

        ModelClass, SerializerClass = CATEGORY_MODEL_MAP[category]

        serializer = SerializerClass(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Expense added",
                "category": category,
                "data": serializer.data
            })

        return Response(serializer.errors, status=400)


class ExpenseListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        all_data = []

        for category, (ModelClass, SerializerClass) in CATEGORY_MODEL_MAP.items():
            items = ModelClass.objects.all().order_by("-id")
            for obj in items:
                all_data.append({
                    "id": obj.id,
                    "category": category,
                    "date": obj.date,
                    "amount": obj.amount,
                    "description": obj.description,
                    "voucher_no": obj.voucher_no,
                    "bill_file": obj.bill_file.url if obj.bill_file else None,
                    "voucher_file": obj.voucher_file.url if obj.voucher_file else None,
                })
        all_data = sorted(all_data, key=lambda x: x["id"], reverse=True)
        return Response({"data": all_data}, status=200)

# -----------------------
# BOOKING APIs
# -----------------------
class CreateBookingTypeAPIView(APIView):
    def post(self, request):
        serializer = BookingTypeMasterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Booking type added", "data": serializer.data})
        return Response(serializer.errors, status=400)


class BookingTypeListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        types = BookingTypeMaster.objects.all()
        serializer = BookingTypeMasterSerializer(types, many=True)
        return Response({"data": serializer.data})

class UpdateBookingTypeAPIView(APIView):
    def put(self, request, pk):
        try:
            bt = BookingTypeMaster.objects.get(pk=pk)
        except BookingTypeMaster.DoesNotExist:
            return Response({"error": "Booking type not found"}, status=404)

        serializer = BookingTypeMasterSerializer(bt, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Booking type updated", "data": serializer.data})
        return Response(serializer.errors, status=400)

class DeleteBookingTypeAPIView(APIView):
    def delete(self, request, pk):
        try:
            bt = BookingTypeMaster.objects.get(pk=pk)
        except BookingTypeMaster.DoesNotExist:
            return Response({"error": "Booking type not found"}, status=404)

        bt.delete()
        return Response({"message": "Booking type deleted"})


class CreateBookingAPIView(APIView):
    def post(self, request):
        data = request.data.copy()
        data["source"] = 0  # ⭐ STAFF

        serializer = BookingSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Booking added", "data": serializer.data},
                status=201
            )

        return Response(serializer.errors, status=400)

class BookingListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        bookings = Booking.objects.all().order_by("-id")
        serializer = BookingFetchSerializer(bookings, many=True)
        return Response({"data": serializer.data}, status=200)



class UpdateBookingAPIView(APIView):
    def put(self, request, pk):
        # OTP checking
        # is_verified, error = verify_otp_for_edit(request, 'booking_edit')
        # if not is_verified:
        #     return Response({"error": error}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            booking = Booking.objects.get(pk=pk)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=404)

        # Prevent editing booking_type & booking_price
        non_editable_fields = ["booking_type", "booking_price"]
        data = request.data.copy()
        for field in non_editable_fields:
            if field in data:
                data.pop(field)

        serializer = BookingSerializer(booking, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()   # DRF calls update() then ONE save()
            return Response({
                "message": "Booking updated successfully",
                "data": serializer.data
            })

        return Response(serializer.errors, status=400)

class DeleteBookingAPIView(APIView):
    def delete(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=404)

        booking.delete()
        return Response({"message": "Booking deleted successfully"}, status=200)


from django.conf import settings
class WebsiteBookingAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        api_key = request.headers.get("X-API-KEY")

        if api_key != settings.WEBSITE_API_KEY:
            return Response(
                {"status": "error", "message": "Unauthorized access"},
                status=401
            )

        data = request.data.copy()
        data["source"] = 1  # ⭐ WEBSITE

        serializer = BookingSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "success", "message": "Website booking saved"},
                status=201
            )

        return Response(serializer.errors, status=400)
    
class WebsiteBookingListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        bookings = Booking.objects.filter(
            booking_source=1
        ).order_by("-id")

        serializer = WebsiteBookingFetchSerializer(bookings, many=True)
        return Response({
            "source": "website",
            "count": bookings.count(),
            "data": serializer.data
        }, status=200)




#-----------------------
#Ledger Entry signal handlers
#-----------------------
#Daybook: list entries for a date
class DaybookAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]  # change as needed

    def get(self, request):
        date = request.query_params.get("date")
        if not date:
            return Response({"error": "date query param required, format YYYY-MM-DD"}, status=400)
        entries = LedgerEntry.objects.filter(date=date).order_by("id")
        serializer = LedgerEntrySerializer(entries, many=True)
        return Response({"data":serializer.data})


class LedgerAPIView(APIView):
    def get(self, request):
        account = request.query_params.get("account")

        queryset = LedgerEntry.objects.filter(source_type=account).order_by("date", "id")

        results = []
        running_balance = 0

        for entry in queryset:
            debit = float(entry.debit or 0)
            credit = float(entry.credit or 0)

            # Correct accounting logic:
            # Charges & pending = debit  (+)
            # Payments = credit          (-)
            running_balance += (credit - debit)

            results.append({
                "id": entry.id,
                "date": entry.date,
                "description": entry.description,
                "debit": debit,
                "credit": credit,
                "running_balance": running_balance
            })

        return Response({"results": results})



# Backfill endpoint: generates ledger entries for all existing income/expense/booking rows.
# Be careful: run once and remove or protect it in production.
class BackfillLedgerAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        """
        Recreate ledger entries for all existing objects by triggering the save handlers.
        WARNING: This deletes existing ledger entries and re-writes them. Use with care.
        """
        from .signals import _delete_existing_entries  # reuse helper if exposed
        count = 0
        with transaction.atomic():
            # clear all ledger rows first
            LedgerEntry.objects.all().delete()

            # Recreate by iterating all sources and saving them (triggers post_save)
            for model in [SalesIncome, OtherIncome, Booking]:
                for obj in model.objects.all():
                    obj.save()
                    count += 1

            # Expenses: iterate over all BaseExpense subclasses
            # If models are in same file and imported in signals, saving them will trigger signal handlers
            # You can import them explicitly if needed.
            # Example:
            from .models import (
                LaundryExpense, CleaningExpense, MessExpense, CafeteriaExpense,
                RentalExpense, SalaryExpense, MiscellaneousExpense,
                MaintenanceExpense, CapitalExpense, OtherExpense,
            )

            expense_models = [
                LaundryExpense, CleaningExpense, MessExpense, CafeteriaExpense,
                RentalExpense, SalaryExpense, MiscellaneousExpense, MaintenanceExpense,
                CapitalExpense, OtherExpense
            ]
            for model in expense_models:
                for obj in model.objects.all():
                    obj.save()
                    count += 1

        return Response({"status": "ok", "processed_objects": count})





# -----------------------
# UNIFIED INCOME API
# -----------------------
class UnifiedIncomeListAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        all_income = []

        # 1. Booking Income
        bookings = Booking.objects.all()
        for booking in bookings:

            # Convert booking_type ID → Name
            try:
                booking_type_name = BookingTypeMaster.objects.get(
                    id=int(booking.booking_type)
                ).name
            except:
                booking_type_name = booking.booking_type  # fallback (text)

            all_income.append({
                "id": booking.id,
                "type": "Booking",
                "date": booking.booking_date,
                "amount": booking.booking_price,
                "description": (
                    f"Guest: {booking.guest_name}, "
                    f"Room: {booking.room_no}, "
                    f"Type: {booking_type_name}"
                ),
                "details": {
                    "guest_name": booking.guest_name,
                    "room_no": booking.room_no,
                    "phone_number": booking.phone_number,
                    "booking_type": booking_type_name,
                    "checkin_date": booking.checkin_date,
                    "checkout_date": booking.checkout_date,
                    "paid_amount": booking.paid_amount,
                    "pending_amount": booking.pending_amount
                }
            })
        
        # 2. Sales Income
        sales = SalesIncome.objects.all()
        for sale in sales:
            all_income.append({
                "id": sale.id,
                "type": "Sales Income",
                "date": sale.date,
                "amount": sale.amount,
                "description": sale.description,
                "details": {
                    "category": sale.category
                }
            })
        
        # 3. Other Income
        other_incomes = OtherIncome.objects.all()
        for income in other_incomes:
            all_income.append({
                "id": income.id,
                "type": "Other Income",
                "date": income.date,
                "amount": income.amount,
                "description": income.description,
                "details": {
                    "category": income.category
                }
            })
        
        # Sort by date (most recent first)
        all_income = sorted(all_income, key=lambda x: x["date"], reverse=True)
        
        # Calculate total income
        total_income = sum(float(item["amount"]) for item in all_income)
        
        return Response({
            "data": all_income,
            "total_income": total_income,
            "count": len(all_income)
        }, status=200)
    



# ------------------------------------
# CREATE INVOICE NUMBER FOR BOOKING 
# -----------------------------------

class NextInvoiceNumberAPIView(APIView):
    def get(self, request):
        next_no = Booking.get_next_invoice_no()
        return Response({"next_invoice_no": next_no}, status=200)


#------------------------
#cafeteria expense api
#------------------------
class CreateCafeteriaExpenseAPIView(APIView):
    def post(self, request):
        serializer = CafeteriaExpenseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Cafeteria expense added",
                "data": serializer.data
            }, status=201)
        
        return Response(serializer.errors, status=400)
        

class CafeteriaExpenseListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        expenses = CafeteriaExpense.objects.all().order_by("-id")
        serializer = CafeteriaExpenseSerializer(expenses, many=True)
        return Response({"data": serializer.data}, status=200)

class UpdateCafeteriaExpenseAPIView(APIView):
    def put(self, request, pk):
        try:
            expense = CafeteriaExpense.objects.get(pk=pk)
        except CafeteriaExpense.DoesNotExist:
            return Response({"error": "Record not found"}, status=404)

        serializer = CafeteriaExpenseSerializer(expense, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Updated", "data": serializer.data})

        return Response(serializer.errors, status=400)


#-------------------------------------
#salary expense api
#-------------------------------------
class CreateSalaryExpenseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SalaryExpenseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Salary expense added",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SalaryExpenseListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        expenses = SalaryExpense.objects.all().order_by("-id")

        data = []
        for exp in expenses:
            data.append({
                "id": exp.id,
                "category": "Salary",
                "date": exp.date,
                "amount": exp.amount,
                "staff_code": exp.staff_code,
                "description": exp.description,
                "voucher_no": exp.voucher_no,
                "bill_file": exp.bill_file.url if exp.bill_file else None,
                "voucher_file": exp.voucher_file.url if exp.voucher_file else None,
            })

        return Response({"data": data}, status=status.HTTP_200_OK)


class UpdateSalaryExpenseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            expense = SalaryExpense.objects.get(pk=pk)
        except SalaryExpense.DoesNotExist:
            return Response(
                {"error": "Salary expense not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SalaryExpenseSerializer(
            expense,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Salary expense updated",
                "data": serializer.data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#-------------------------------
#Monthly Ledger Summary
#------------------------------


# class MonthlyLedgerSummaryAPIView(APIView):
#     def get(self, request):
#         account = request.query_params.get("account")
#         year = request.query_params.get("year")

#         queryset = LedgerEntry.objects.all()

#         if account:
#             queryset = queryset.filter(source_type=account)

#         if year:
#             queryset = queryset.filter(date__year=int(year))

#         summary = (
#             queryset
#             .annotate(
#                 year=ExtractYear("date"),
#                 month=ExtractMonth("date")
#             )
#             .values("year", "month")
#             .annotate(
#                 total_credit=Sum("credit"),
#                 total_debit=Sum("debit")
#             )
#             .order_by("year", "month")
#         )

#         month_names = {
#             1: "January", 2: "February", 3: "March", 4: "April",
#             5: "May", 6: "June", 7: "July", 8: "August",
#             9: "September", 10: "October", 11: "November", 12: "December"
#         }

#         results = []
#         for row in summary:
#             results.append({
#                 "year": row["year"],
#                 "month": month_names[row["month"]],
#                 "credit": float(row["total_credit"] or 0),
#                 "debit": float(row["total_debit"] or 0),
#             })

#         return Response({
#             "account": account,
#             "results": results
#         })
        
        
########## without passing account ################

class MonthlyLedgerSummaryAPIView(APIView):
    def get(self, request):

        year = request.query_params.get("year")

        if not year:
            return Response(
                {"error": "Year parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            year = int(year)
        except ValueError:
            return Response(
                {"error": "Year must be a valid number"},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = LedgerEntry.objects.filter(date__year=year)

        summary = (
            queryset
            .annotate(month=ExtractMonth("date"))
            .values("month", "source_type")
            .annotate(
                total_credit=Sum("credit"),
                total_debit=Sum("debit")
            )
            .order_by("month", "source_type")
        )

        month_names = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        }

        results = []

        for row in summary:
            results.append({
                "year": year,
                "month": month_names.get(row["month"]),
                "source_type": row["source_type"],
                "credit": float(row["total_credit"] or 0),
                "debit": float(row["total_debit"] or 0),
            })

        return Response({
            "year": year,
            "results": results
        })