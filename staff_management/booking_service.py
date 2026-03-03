# staff_management/booking_service.py

import logging
import requests
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from staff_management.models import Booking

logger = logging.getLogger(__name__)


class BookingService:
    """Fetch bookings from external website"""

    @staticmethod
    def fetch_website_bookings():
        try:
            response = requests.get(
                settings.WEBSITE_BOOKING_API_URL,
                params={"api_key": settings.WEBSITE_API_KEY},
                timeout=30
            )
            response.raise_for_status()

            payload = response.json()
            bookings = payload.get("bookings", [])
            count = 0

            for b in bookings:
                website_item_id = str(b["item_id"])

                if Booking.objects.filter(website_item_id=website_item_id).exists():
                    continue

                checkin = timezone.make_aware(
                    datetime.strptime(b["Checkin_Date"], "%d/%m/%Y")
                )

                checkout = timezone.make_aware(
                    datetime.strptime(b["Checkout_Date"], "%d/%m/%Y")
                )

                total_cost = Decimal(b["Total_Cost"])

                Booking.objects.create(
                    website_item_id=website_item_id,
                    source=1,  # WEBSITE
                    booking_date=checkin.date(),
                    guest_name=b.get("Customer_Name"),
                    phone_number=b.get("Customer_Phone"),
                    checkin_date=checkin,
                    checkout_date=checkout,
                    booking_price=total_cost,
                    paid_amount=Decimal("0.00"),
                    pending_amount=total_cost,
                )

                count += 1

            return True, f"✅ {count} website bookings fetched"

        except Exception as e:
            logger.error(f"Fetch failed: {str(e)}")
            return False, str(e)

# staff_management/booking_service.py

class BookingService:
    """Fetch bookings from external website"""

    @staticmethod
    def fetch_website_bookings():
        # ... (keep your existing code here) ...
        pass

    # 🟢 ADD THIS METHOD TO STOP THE CRASH
    @staticmethod
    def schedule_checkin_reminder(instance):
        """
        Placeholder for scheduling reminders.
        This stops the 500 error in signals.py.
        """
        logger.info(f"⏰ Reminder logic triggered for Booking ID: {instance.id}")
        # Later, you can add SMS or Email logic here
        return True

# import logging
# import requests
# from datetime import datetime
# from decimal import Decimal
# from django.conf import settings
# from staff_management.models import Booking

# logger = logging.getLogger(__name__)


# class BookingService:
#     """Service for fetching and storing website bookings"""

#     @staticmethod
#     def fetch_website_bookings():
#         """
#         Fetch bookings from website API and store them in DB.
#         Returns: tuple (success: bool, message: str)
#         """
#         try:
#             url = settings.WEBSITE_BOOKING_API_URL
#             params = {"api_key": settings.WEBSITE_API_KEY}

#             response = requests.get(url, params=params, timeout=30)
#             response.raise_for_status()

#             payload = response.json()
#             bookings = payload.get("bookings", [])
#             count = 0

#             for b in bookings:
#                 website_item_id = str(b["item_id"])

#                 # Skip if booking already exists
#                 if Booking.objects.filter(website_item_id=website_item_id).exists():
#                     continue

#                 # Website sends DATE only → default time = 12:00 PM
#                 checkin = datetime.strptime(
#                     b["Checkin_Date"], "%d/%m/%Y"
#                 ).replace(hour=12, minute=0)

#                 checkout = datetime.strptime(
#                     b["Checkout_Date"], "%d/%m/%Y"
#                 ).replace(hour=11, minute=0)

#                 total_cost = Decimal(b["Total_Cost"])

#                 Booking.objects.create(
#                     website_item_id=website_item_id,
#                     source=1,  # WEBSITE
#                     booking_date=checkin.date(),
#                     guest_name=b.get("Customer_Name"),
#                     room_no=None,
#                     phone_number=b.get("Customer_Phone"),
#                     booking_type=None,
#                     checkin_date=checkin,
#                     checkout_date=checkout,
#                     booking_price=total_cost,
#                     paid_amount=Decimal("0.00"),
#                     pending_amount=total_cost,
#                 )

#                 count += 1

#             message = f"✅ Fetched and created {count} website bookings"
#             logger.info(message)
#             return True, message

#         except requests.exceptions.RequestException as e:
#             message = f"Website API error: {str(e)}"
#             logger.error(message)
#             return False, message

#         except Exception as e:
#             message = f"Booking fetch failed: {str(e)}"
#             logger.error(message)
#             return False, message
