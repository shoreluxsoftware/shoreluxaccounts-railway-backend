# admin_management/views.py

import logging
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.permissions import IsAdminUser,IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from django.contrib.auth.hashers import make_password
from django.conf import settings

from admin_management.serializers import *
# from login.sms_service import *

from login.email_service import EmailNotificationService    # OTP via SMTP
import random
import string

logger = logging.getLogger(__name__)

class CreateStaffAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        
        try:
            staff = User.objects.create(
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                phone_number=data.get('phone_number', ''),
                aadhaar_number=data.get('aadhaar_number', ''),
                age=data.get('age', None),
                role="STAFF",
                can_login=False,
                aadhaar_card=data.get('aadhaar_card'),
                profile_image=data.get('profile_image'),
                designation=data.get('designation', ''),
                # 🔥 username = NULL/empty - user enters LATER when enabling login
            )
            
            return Response({
                "message": "Staff created successfully",
                "staff_unique_id": staff.staff_unique_id,
                "id": staff.id
            }, status=status.HTTP_201_CREATED)
            
        except IntegrityError:
            # 🔥 If username conflict → try with temp unique username
            staff_count = User.objects.filter(role="STAFF").count() + 1
            temp_username = f"staff_temp_{staff_count:04d}"
            
            staff = User.objects.create(
                username=temp_username,
                first_name=data.get('first_name', ''),
                designation=data.get('designation', ''),
                last_name=data.get('last_name', ''),
                phone_number=data.get('phone_number', ''),
                aadhaar_number=data.get('aadhaar_number', ''),
                age=data.get('age', None),
                role="STAFF",
                can_login=False,
                aadhaar_card=data.get('aadhaar_card'),
                profile_image=data.get('profile_image'),
            )
            
            return Response({
                "message": "Staff created successfully (temp username assigned)",
                "staff_unique_id": staff.staff_unique_id,
                "id": staff.id
            }, status=status.HTTP_201_CREATED)


class ListStaffAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        staff_members = User.objects.filter(role="STAFF")
        staff_list = []
        for staff in staff_members:
            # Safely build absolute URLs for file fields if available
            aadhaar_url = None
            profile_url = None
            try:
                if staff.aadhaar_card and hasattr(staff.aadhaar_card, 'url'):
                    aadhaar_url = request.build_absolute_uri(staff.aadhaar_card.url)
            except Exception:
                aadhaar_url = None

            try:
                if staff.profile_image and hasattr(staff.profile_image, 'url'):
                    profile_url = request.build_absolute_uri(staff.profile_image.url)
            except Exception:
                profile_url = None

            staff_list.append({
                "id": staff.id,
                "staff_unique_id": staff.staff_unique_id,
                "username": staff.username,
                "first_name": staff.first_name,
                "last_name": staff.last_name,
                "phone_number": staff.phone_number,
                "aadhaar_number": staff.aadhaar_number,
                "designation": staff.designation,
                "age": staff.age,
                "aadhaar_card": aadhaar_url,
                "profile_image": profile_url,
                "can_login": staff.can_login,
            })

        return Response({"staff_list": staff_list}, status=status.HTTP_200_OK)
    


class DeleteStaffAPIView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        # Try lookup by primary key first. If not found, try by staff_unique_id.
        try:
            staff = User.objects.get(pk=pk, role="STAFF")
        except User.DoesNotExist:
            try:
                staff = User.objects.get(staff_unique_id=pk, role="STAFF")
            except User.DoesNotExist:
                return Response({"detail": "Staff member not found."}, status=status.HTTP_404_NOT_FOUND)

        staff.delete()
        return Response({"message": "Staff member deleted successfully."}, status=status.HTTP_200_OK)
    
    
class UpdateStaffAPIView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        # Support updating by numeric PK or by staff_unique_id
        try:
            staff = User.objects.get(pk=pk, role="STAFF")
        except User.DoesNotExist:
            try:
                staff = User.objects.get(staff_unique_id=pk, role="STAFF")
            except User.DoesNotExist:
                return Response({"detail": "Staff member not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        staff.first_name = data.get('first_name', staff.first_name)
        staff.last_name = data.get('last_name', staff.last_name)
        staff.designation = data.get('designation', staff.designation) # ✅
        staff.phone_number = data.get('phone_number', staff.phone_number)
        staff.age = data.get('age', staff.age)

        # Update password if provided
        new_password = data.get('password')
        if new_password:
            staff.password = make_password(new_password)

        staff.save()

        return Response({
            "message": "Staff member updated successfully.",
            "staff_unique_id": staff.staff_unique_id,
            "username": staff.username,
            "designation": staff.designation,
            "first_name": staff.first_name,
            "last_name": staff.last_name,
            "phone_number": staff.phone_number,
            "age": staff.age,
        }, status=status.HTTP_200_OK)

     
class EnableLoginForStaffAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "username and password are required"},
                status=400
            )

        try:
            staff = User.objects.get(pk=pk, role="STAFF")
        except User.DoesNotExist:
            return Response({"error": "Staff not found"}, status=404)

        if staff.can_login:
            return Response({"error": "Login already enabled"}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=400)

        staff.username = username
        staff.set_password(password)
        staff.can_login = True
        staff.save()

        return Response({
            "message": "Login enabled successfully",
            "username": staff.username
        })

class DisableLoginForStaffAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):  # 🔥 CHANGE: post ← patch
        try:
            staff = User.objects.get(pk=pk, role="STAFF")
        except User.DoesNotExist:
            return Response({"detail": "Staff not found"}, status=404)

        staff.can_login = False
        staff.username = ""  # 🔥 CLEAR username too!
        staff.save(update_fields=["can_login", "username"])

        return Response({
            "message": "Login access disabled successfully"
        })


from decimal import Decimal
from staff_management.models import *
from django.db.models import Sum, Q
from datetime import datetime, timedelta


class DashboardSummaryAPIView(APIView):
    #permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Returns dashboard summary cards data.
        
        Query Parameters:
        - period: 'weekly' or 'monthly' (default)
        
        Examples:
        /api/dashboard/summary/  (defaults to monthly)
        /api/dashboard/summary/?period=weekly
        /api/dashboard/summary/?period=monthly
        
        Response:
        {
            "bookings": 25,
            "income": 250000,
            "expenses": 15000,
            "profit": 235000,
            "period": "This Week"
        }
        """
        period = request.query_params.get('period', 'monthly').lower()
        now = timezone.now()
        
        # Determine date range based on period
        if period == 'weekly':
            # Get current week (Monday to Sunday)
            current_weekday = now.weekday()
            week_start = now - timedelta(days=current_weekday)
            week_end = week_start + timedelta(days=6)
            
            start_date = week_start.date()
            end_date = week_end.date()
            period_label = "This Week"
            
        else:  # Default to monthly
            start_date = now.replace(day=1).date()
            if now.month == 12:
                end_date = now.replace(year=now.year+1, month=1, day=1).date() - timedelta(days=1)
            else:
                end_date = now.replace(month=now.month+1, day=1).date() - timedelta(days=1)
            period_label = "This Month"

        # 1️⃣ Total Bookings
        total_bookings = Booking.objects.filter(
            booking_date__range=[start_date, end_date]
        ).count()

        # 2️⃣ Total Income (SalesIncome + OtherIncome + Booking Revenue)
        sales_income = SalesIncome.objects.filter(
            date__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        other_income = OtherIncome.objects.filter(
            date__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        booking_income = Booking.objects.filter(
            booking_date__range=[start_date, end_date]
        ).aggregate(total=Sum('booking_price'))['total'] or Decimal('0.00')

        total_income = sales_income + other_income + booking_income

        # 3️⃣ Total Expenses
        expense_models = [
            LaundryExpense, CleaningExpense, MessExpense, CafeteriaExpense,
            RentalExpense, SalaryExpense, MiscellaneousExpense,
            MaintenanceExpense, CapitalExpense, OtherExpense
        ]

        total_expenses = Decimal('0.00')
        for model in expense_models:
            amount = model.objects.filter(
                date__range=[start_date, end_date]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            total_expenses += amount

        # 4️⃣ Profit = Income - Expenses
        profit = total_income - total_expenses

        return Response({
            "bookings": total_bookings,
            "income": float(total_income),
            "expenses": float(total_expenses),
            "profit": float(profit),
            "period": period_label
        }, status=status.HTTP_200_OK)


class MonthlyTrendAPIView(APIView):
    #permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Returns monthly income and expenses data for the current year (Jan to current month).
        Used for the "Income vs Expenses (Monthly Data Shown)" chart.
        
        Example response:
        {
            "data": [
                {"month": "Jan", "income": 25000, "expenses": 5000},
                {"month": "Feb", "income": 30000, "expenses": 6000},
                ...
                {"month": "Nov", "income": 200000, "expenses": 65000}
            ]
        }
        """
        now = timezone.now()
        months_data = []
        
        # Get all months from January to current month of current year
        current_year = now.year
        current_month = now.month

        for month in range(1, current_month + 1):
            # Create start and end dates for each month
            month_start = timezone.make_aware(datetime(current_year, month, 1))
            
            # Calculate month end
            if month == 12:
                month_end = timezone.make_aware(datetime(current_year + 1, 1, 1)) - timedelta(days=1)
            else:
                month_end = timezone.make_aware(datetime(current_year, month + 1, 1)) - timedelta(days=1)

            month_start_date = month_start.date()
            month_end_date = month_end.date()

            # Calculate income for this month
            sales_inc = SalesIncome.objects.filter(
                date__range=[month_start_date, month_end_date]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            other_inc = OtherIncome.objects.filter(
                date__range=[month_start_date, month_end_date]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            booking_inc = Booking.objects.filter(
                booking_date__range=[month_start_date, month_end_date]
            ).aggregate(total=Sum('booking_price'))['total'] or Decimal('0.00')

            month_income = sales_inc + other_inc + booking_inc

            # Calculate expenses for this month
            expense_models = [
                LaundryExpense, CleaningExpense, MessExpense, CafeteriaExpense,
                RentalExpense, SalaryExpense, MiscellaneousExpense,
                MaintenanceExpense, CapitalExpense, OtherExpense
            ]

            month_expenses = Decimal('0.00')
            for model in expense_models:
                exp = model.objects.filter(
                    date__range=[month_start_date, month_end_date]
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                month_expenses += exp

            months_data.append({
                "month": month_start.strftime("%b"),  # Jan, Feb, Mar, etc.
                "income": float(month_income),
                "expenses": float(month_expenses)
            })

        return Response({"data": months_data}, status=status.HTTP_200_OK)



# =============================================
# 3. BOOKING PROGRESS (Percentage)
# =============================================
class BookingProgressAPIView(APIView):
    #permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Returns booking occupancy/progress percentage.
        This is a simplified calculation - adjust logic based on your requirement.
        
        Calculation options:
        1. Percentage of rooms booked vs total rooms
        2. Percentage of booking capacity utilized
        3. Current month bookings vs target/goal
        """
        now = timezone.now()
        current_month_start = now.replace(day=1)
        
        if now.month == 12:
            current_month_end = now.replace(year=now.year+1, month=1, day=1) - timedelta(days=1)
        else:
            current_month_end = now.replace(month=now.month+1, day=1) - timedelta(days=1)

        # Get active bookings (checked in but not checked out yet)
        active_bookings = Booking.objects.filter(
            checkin_date__lte=now.date(),
            checkout_date__gte=now.date()
        ).count()

        # Example: Assuming 100 room capacity
        # Adjust TOTAL_ROOMS constant to your actual room count
        TOTAL_ROOMS = 100
        occupancy_percentage = (active_bookings / TOTAL_ROOMS) * 100

        return Response({
            "progress_percentage": min(int(occupancy_percentage), 100),
            "active_bookings": active_bookings,
            "total_capacity": TOTAL_ROOMS,
            "label": f"{min(int(occupancy_percentage), 100)}%"
        }, status=status.HTTP_200_OK)


# =============================================
# 4. MONTHLY TREND LINE CHART
# =============================================
class MonthlyTrendLineAPIView(APIView):
    #permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Returns trend data for income, expenses, and profit lines.
        Used for line chart visualization.
        """
        now = timezone.now()
        trend_data = []

        # Get last 9 months
        for i in range(8, -1, -1):
            month_date = now - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            
            if month_date.month == 12:
                month_end = month_date.replace(year=month_date.year+1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month_date.replace(month=month_date.month+1, day=1) - timedelta(days=1)

            # Income
            sales_inc = SalesIncome.objects.filter(
                date__range=[month_start, month_end]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            other_inc = OtherIncome.objects.filter(
                date__range=[month_start, month_end]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            booking_inc = Booking.objects.filter(
                booking_date__range=[month_start, month_end]
            ).aggregate(total=Sum('booking_price'))['total'] or Decimal('0.00')

            month_income = sales_inc + other_inc + booking_inc

            # Expenses
            expense_models = [
                LaundryExpense, CleaningExpense, MessExpense, CafeteriaExpense,
                RentalExpense, SalaryExpense, MiscellaneousExpense,
                MaintenanceExpense, CapitalExpense, OtherExpense
            ]

            month_expenses = Decimal('0.00')
            for model in expense_models:
                exp = model.objects.filter(
                    date__range=[month_start, month_end]
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                month_expenses += exp

            profit = month_income - month_expenses

            trend_data.append({
                "month": month_date.strftime("%b"),
                "income": float(month_income),
                "expenses": float(month_expenses),
                "profit": float(profit)
            })

        return Response({"data": trend_data}, status=status.HTTP_200_OK)



# ========================
# OTP Request API
# ========================


# class RequestOTPAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = OTPRequestSerializer(data=request.data)

#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         verification_type = serializer.validated_data['verification_type']
#         object_id = serializer.validated_data.get('object_id')

#         # --------------------------------------------------
#         # 1. Remove old unverified OTPs
#         # --------------------------------------------------
#         OTPVerification.objects.filter(
#             user=request.user,
#             verification_type=verification_type,
#             is_verified=False
#         ).delete()

#         # --------------------------------------------------
#         # 2. Generate OTP (NO EXTRA FILE)
#         # --------------------------------------------------
#         otp = ''.join(random.choices(string.digits, k=6))

#         # --------------------------------------------------
#         # 3. Send OTP via EMAIL ONLY
#         # --------------------------------------------------
#         email_service = EmailNotificationService()

#         email_result = email_service.send_otp_email(
#             otp=otp,
#             verification_type=verification_type,
#             username=request.user.username
#         )

#         if not email_result.get("success"):
#             return Response(
#                 {"error": "Failed to send OTP email"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # --------------------------------------------------
#         # 4. Save OTP
#         # --------------------------------------------------
#         OTPVerification.objects.create(
#             user=request.user,
#             otp=otp,
#             verification_type=verification_type,
#             object_id=object_id,
#             expires_at=timezone.now() + timedelta(minutes=10)
#         )

#         # --------------------------------------------------
#         # 5. Success
#         # --------------------------------------------------
#         return Response(
#             {
#                 "message": "OTP sent successfully to admin email",
#                 "expires_in_seconds": 600
#             },
#             status=status.HTTP_201_CREATED
#         )

from login.views import send_email_async  # Import at top

class RequestOTPAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from admin_management.models import OTPVerification
        from datetime import timedelta
        from django.utils import timezone
        import random
        import string
        
        serializer = OTPRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        verification_type = serializer.validated_data['verification_type']
        object_id = serializer.validated_data.get('object_id')

        # Remove old unverified OTPs
        OTPVerification.objects.filter(
            user=request.user,
            verification_type=verification_type,
            is_verified=False
        ).delete()

        # Generate OTP
        otp = ''.join(random.choices(string.digits, k=6))

        # Send OTP via email in background thread
        send_email_async(
            email_type="otp",
            otp=otp,
            verification_type=verification_type,
            username=request.user.username
        )

        # Save OTP
        OTPVerification.objects.create(
            user=request.user,
            otp=otp,
            verification_type=verification_type,
            object_id=object_id,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        return Response(
            {
                "message": "OTP sent successfully to your email",
                "expires_in_seconds": 600
            },
            status=status.HTTP_201_CREATED
        )

# ========================
# OTP Verification API
# ========================
class VerifyOTPAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        otp = serializer.validated_data['otp']
        verification_type = serializer.validated_data['verification_type']
        
        # Get latest unverified OTP for this user and type
        try:
            otp_record = OTPVerification.objects.filter(
                user=request.user,
                verification_type=verification_type,
                is_verified=False
            ).latest('created_at')
        except OTPVerification.DoesNotExist:
            return Response(
                {"error": "No OTP found. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if expired
        if not otp_record.is_valid():
            otp_record.delete()
            return Response(
                {"error": "OTP expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if OTP matches
        if otp_record.otp != otp:
            return Response(
                {"error": "Invalid OTP. Please try again."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark as verified
        otp_record.is_verified = True
        otp_record.save()
        
        return Response({
            "message": "OTP verified successfully",
            "verified": True
        }, status=status.HTTP_200_OK)


