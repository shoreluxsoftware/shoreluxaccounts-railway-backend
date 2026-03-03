
# staff_management/signals.py

import logging
from decimal import Decimal
from django.db import transaction
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from .models import (
    LedgerEntry, SalesIncome, OtherIncome, Booking,
    LaundryExpense, CleaningExpense, MessExpense, CafeteriaExpense,
    RentalExpense, SalaryExpense, MiscellaneousExpense,
    MaintenanceExpense, CapitalExpense, OtherExpense,
)

logger = logging.getLogger(__name__)


def _delete_existing_entries(source_type, source_id):
    LedgerEntry.objects.filter(
        source_type=source_type,
        source_id=source_id
    ).delete()


@receiver(pre_save, sender=Booking)
def booking_pre_save_capture_old_paid(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_paid_amount = Decimal("0.00")
        return

    try:
        old = sender.objects.get(pk=instance.pk)
        instance._old_paid_amount = old.paid_amount or Decimal("0.00")
    except sender.DoesNotExist:
        instance._old_paid_amount = Decimal("0.00")


@receiver(post_save, sender=Booking)
def booking_post_save(sender, instance, created, **kwargs):
    source_type = "booking"

    with transaction.atomic():
        calculated_pending = (
            (instance.booking_price or Decimal("0.00")) -
            (instance.paid_amount or Decimal("0.00"))
        )

        if instance.pending_amount != calculated_pending:
            Booking.objects.filter(pk=instance.pk).update(
                pending_amount=calculated_pending
            )

        if created and instance.paid_amount:
            LedgerEntry.objects.create(
                date=instance.booking_date or instance.checkin_date,
                source_type=source_type,
                source_id=instance.id,
                description=f"Booking payment ({instance.guest_name})",
                credit=instance.paid_amount,
                debit=Decimal("0.00"),
            )

        old_paid = getattr(instance, "_old_paid_amount", Decimal("0.00"))
        diff = (instance.paid_amount or Decimal("0.00")) - old_paid

        if diff > 0:
            LedgerEntry.objects.create(
                date=instance.booking_date or instance.checkin_date,
                source_type=source_type,
                source_id=instance.id,
                description=f"Additional payment ({instance.guest_name})",
                credit=diff,
                debit=Decimal("0.00"),
            )


@receiver(pre_delete, sender=Booking)
def booking_pre_delete(sender, instance, **kwargs):
    _delete_existing_entries("booking", instance.id)


import logging
from decimal import Decimal
from django.db import transaction
from django.db.models.signals import post_save, pre_delete, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .models import (
    LedgerEntry, SalesIncome, OtherIncome, Booking,
    LaundryExpense, CleaningExpense, MessExpense, CafeteriaExpense,
    RentalExpense, SalaryExpense, MiscellaneousExpense,
    MaintenanceExpense, CapitalExpense, OtherExpense,
)
from .booking_service import BookingService

logger = logging.getLogger(__name__)


def _delete_existing_entries(source_type: str, source_id: int):
    """Helper: remove ledger rows linked to a source"""
    LedgerEntry.objects.filter(source_type=source_type, source_id=source_id).delete()


@receiver(pre_save, sender=Booking)
def booking_pre_save_capture_old_paid(sender, instance, **kwargs):
    """Capture old paid_amount before save"""
    if not instance.pk:
        instance._old_paid_amount = Decimal("0.00")
        return

    try:
        old = sender.objects.get(pk=instance.pk)
        instance._old_paid_amount = old.paid_amount or Decimal("0.00")
    except sender.DoesNotExist:
        instance._old_paid_amount = Decimal("0.00")


@receiver(post_save, sender=Booking)
def booking_post_save_cash_only(sender, instance, created, **kwargs):
    """Handle booking creation/updates and ledger entries"""
    source_type = "booking"

    with transaction.atomic():
        calculated_pending = (instance.booking_price or Decimal("0.00")) - (instance.paid_amount or Decimal("0.00"))
        if instance.pending_amount != calculated_pending:
            Booking.objects.filter(pk=instance.pk).update(pending_amount=calculated_pending)
            instance.pending_amount = calculated_pending

        if created:
            if (instance.paid_amount or Decimal("0.00")) > Decimal("0.00"):
                LedgerEntry.objects.create(
                    date=instance.booking_date or instance.checkin_date,
                    source_type=source_type,
                    source_id=instance.id,
                    description=f"Booking payment received ({instance.guest_name})",
                    credit=instance.paid_amount,
                    debit=Decimal("0.00"),
                )
            
            # ✅ Schedule check-in reminder (NO CELERY)
            logger.info(f"📌 New booking created: {instance.id}")
            BookingService.schedule_checkin_reminder(instance)
            return

        old_paid = getattr(instance, "_old_paid_amount", Decimal("0.00"))
        new_paid = instance.paid_amount or Decimal("0.00")
        try:
            difference = (Decimal(new_paid) - Decimal(old_paid))
        except Exception:
            difference = Decimal("0.00")

        if difference > Decimal("0.00"):
            LedgerEntry.objects.create(
                date=instance.booking_date or instance.checkin_date,
                source_type=source_type,
                source_id=instance.id,
                description=f"Booking payment received ({instance.guest_name})",
                credit=difference,
                debit=Decimal("0.00"),
            )


@receiver(pre_delete, sender=Booking)
def booking_pre_delete(sender, instance, **kwargs):
    """Clean up ledger entries on booking delete"""
    _delete_existing_entries("booking", instance.id)
    logger.info(f"🗑️ Booking deleted: {instance.id}")


# ===== INCOME MODELS =====
@receiver(post_save, sender=SalesIncome)
def salesincome_post_save(sender, instance, **kwargs):
    source_type = "salesincome"
    with transaction.atomic():
        _delete_existing_entries(source_type, instance.id)
        LedgerEntry.objects.create(
            date=instance.date,
            source_type=source_type,
            source_id=instance.id,
            description=instance.description or f"Sales Income",
            credit=instance.amount or Decimal("0.00"),
            debit=Decimal("0.00"),
        )


@receiver(pre_delete, sender=SalesIncome)
def salesincome_pre_delete(sender, instance, **kwargs):
    _delete_existing_entries("salesincome", instance.id)


@receiver(post_save, sender=OtherIncome)
def otherincome_post_save(sender, instance, **kwargs):
    source_type = "otherincome"
    with transaction.atomic():
        _delete_existing_entries(source_type, instance.id)
        LedgerEntry.objects.create(
            date=instance.date,
            source_type=source_type,
            source_id=instance.id,
            description=instance.description or f"Other Income",
            credit=instance.amount or Decimal("0.00"),
            debit=Decimal("0.00"),
        )


@receiver(pre_delete, sender=OtherIncome)
def otherincome_pre_delete(sender, instance, **kwargs):
    _delete_existing_entries("otherincome", instance.id)


# ===== EXPENSE MODELS =====
EXPENSE_MODELS = [
    (LaundryExpense, "laundryexpense"),
    (CleaningExpense, "cleaningexpense"),
    (MessExpense, "messexpense"),
    (CafeteriaExpense, "cafeteriaexpense"),
    (RentalExpense, "rentalexpense"),
    (SalaryExpense, "salaryexpense"),
    (MiscellaneousExpense, "miscexpense"),
    (MaintenanceExpense, "maintenanceexpense"),
    (CapitalExpense, "capitalexpense"),
    (OtherExpense, "otherexpense"),
]

for model_class, source_type in EXPENSE_MODELS:
    def make_post_save(stype):
        @receiver(post_save, sender=model_class)
        def expense_post_save(sender, instance, **kwargs):
            with transaction.atomic():
                _delete_existing_entries(stype, instance.id)
                LedgerEntry.objects.create(
                    date=instance.date,
                    source_type=stype,
                    source_id=instance.id,
                    description=instance.description or f"{stype} expense",
                    debit=instance.amount or Decimal("0.00"),
                    credit=Decimal("0.00"),
                )
        return expense_post_save

    def make_pre_delete(stype):
        @receiver(pre_delete, sender=model_class)
        def expense_pre_delete(sender, instance, **kwargs):
            _delete_existing_entries(stype, instance.id)
        return expense_pre_delete

    make_post_save(source_type)
    make_pre_delete(source_type)









# from decimal import Decimal
# from django.db import transaction
# from django.db.models.signals import post_save, pre_delete, pre_save,post_delete
# from django.dispatch import receiver
# import logging
# from django.utils import timezone
# from datetime import timedelta

# from .models import Booking
# from .tasks import schedule_booking_reminder


# logger = logging.getLogger(__name__)


# from .models import (
#     LedgerEntry,
#     SalesIncome,
#     OtherIncome,
#     Booking,
#     LaundryExpense,
#     CleaningExpense,
#     MessExpense,
#     CafeteriaExpense,
#     RentalExpense,
#     SalaryExpense,
#     MiscellaneousExpense,
#     MaintenanceExpense,
#     CapitalExpense,
#     OtherExpense,
# )

# # -------------------------
# # Helper: remove ledger rows linked to a source
# # -------------------------
# def _delete_existing_entries(source_type: str, source_id: int):
#     LedgerEntry.objects.filter(source_type=source_type, source_id=source_id).delete()


# # -------------------------
# # Capture old paid_amount BEFORE the save occurs
# # (we store it on the instance so post_save can read it)
# # -------------------------
# @receiver(pre_save, sender=Booking)
# def booking_pre_save_capture_old_paid(sender, instance, **kwargs):
#     if not instance.pk:
#         # new object — no old paid
#         instance._old_paid_amount = Decimal("0.00")
#         return

#     try:
#         old = sender.objects.get(pk=instance.pk)
#         # ensure Decimal
#         instance._old_paid_amount = old.paid_amount or Decimal("0.00")
#     except sender.DoesNotExist:
#         instance._old_paid_amount = Decimal("0.00")


# # -------------------------
# # BOOKINGS (Cash-only model)
# #
# # - On create: calculate pending, create ledger entry for initial cash (if any)
# # - On update: calculate difference (new_paid - old_paid) and create ledger entry only for positive difference
# # - On delete: remove ledger entries linked to this booking
# # -------------------------
# @receiver(post_save, sender=Booking)
# def booking_post_save_cash_only(sender, instance, created, **kwargs):
#     source_type = "booking"

#     # Use a transaction to keep DB consistent
#     with transaction.atomic():
#         # Always ensure pending_amount is correct in DB
#         calculated_pending = (instance.booking_price or Decimal("0.00")) - (instance.paid_amount or Decimal("0.00"))
#         # update only if mismatch to avoid extra writes
#         if instance.pending_amount != calculated_pending:
#             Booking.objects.filter(pk=instance.pk).update(pending_amount=calculated_pending)
#             # also sync the in-memory instance value
#             instance.pending_amount = calculated_pending

#         # CREATE: record any initial cash received
#         if created:
#             if (instance.paid_amount or Decimal("0.00")) > Decimal("0.00"):
#                 LedgerEntry.objects.create(
#                     date=instance.booking_date or instance.checkin_date,
#                     source_type=source_type,
#                     source_id=instance.id,
#                     description=f"Booking payment received ({instance.guest_name})",
#                     credit=instance.paid_amount,
#                     debit=Decimal("0.00"),
#                 )
#             return

#         # UPDATE: insert ledger entry only for additional money received
#         old_paid = getattr(instance, "_old_paid_amount", Decimal("0.00"))
#         new_paid = instance.paid_amount or Decimal("0.00")
#         try:
#             # ensure Decimal arithmetic
#             difference = (Decimal(new_paid) - Decimal(old_paid))
#         except Exception:
#             difference = Decimal("0.00")

#         if difference > Decimal("0.00"):
#             LedgerEntry.objects.create(
#                 date=instance.booking_date or instance.checkin_date,
#                 source_type=source_type,
#                 source_id=instance.id,
#                 description=f"Booking payment received ({instance.guest_name})",
#                 credit=difference,
#                 debit=Decimal("0.00"),
#             )


# @receiver(pre_delete, sender=Booking)
# def booking_pre_delete(sender, instance, **kwargs):
#     _delete_existing_entries("booking", instance.id)


# # -------------------------
# # SALES INCOME (cash-only)
# # - Recreate ledger entry on every save to keep it idempotent
# # -------------------------
# @receiver(post_save, sender=SalesIncome)
# def salesincome_post_save(sender, instance, **kwargs):
#     source_type = "salesincome"
#     with transaction.atomic():
#         _delete_existing_entries(source_type, instance.id)
#         LedgerEntry.objects.create(
#             date=instance.date,
#             source_type=source_type,
#             source_id=instance.id,
#             description=instance.description or f"Sales Income ({getattr(instance, 'category', '')})",
#             credit=instance.amount or Decimal("0.00"),
#             debit=Decimal("0.00"),
#         )


# @receiver(pre_delete, sender=SalesIncome)
# def salesincome_pre_delete(sender, instance, **kwargs):
#     _delete_existing_entries("salesincome", instance.id)


# # -------------------------
# # OTHER INCOME (cash-only)
# # -------------------------
# @receiver(post_save, sender=OtherIncome)
# def otherincome_post_save(sender, instance, **kwargs):
#     source_type = "otherincome"
#     with transaction.atomic():
#         _delete_existing_entries(source_type, instance.id)
#         LedgerEntry.objects.create(
#             date=instance.date,
#             source_type=source_type,
#             source_id=instance.id,
#             description=instance.description or f"Other Income ({getattr(instance, 'category', '')})",
#             credit=instance.amount or Decimal("0.00"),
#             debit=Decimal("0.00"),
#         )


# @receiver(pre_delete, sender=OtherIncome)
# def otherincome_pre_delete(sender, instance, **kwargs):
#     _delete_existing_entries("otherincome", instance.id)


# # -------------------------
# # EXPENSES (debits) — generic handlers
# # For each expense model we delete existing ledger rows (idempotent)
# # and insert a single debit ledger row on save.
# # -------------------------
# EXPENSE_MODELS = [
#     (LaundryExpense, "laundryexpense"),
#     (CleaningExpense, "cleaningexpense"),
#     (MessExpense, "messexpense"),
#     (CafeteriaExpense, "cafeteriaexpense"),
#     (RentalExpense, "rentalexpense"),
#     (SalaryExpense, "salaryexpense"),
#     (MiscellaneousExpense, "miscexpense"),
#     (MaintenanceExpense, "maintenanceexpense"),
#     (CapitalExpense, "capitalexpense"),
#     (OtherExpense, "otherexpense"),
# ]

# for model_class, source_type in EXPENSE_MODELS:
#     # Post-save handler factory (closure to capture model_class & source_type)
#     def make_post_save(stype):
#         @receiver(post_save, sender=model_class)
#         def expense_post_save(sender, instance, **kwargs):
#             with transaction.atomic():
#                 _delete_existing_entries(stype, instance.id)
#                 LedgerEntry.objects.create(
#                     date=instance.date,
#                     source_type=stype,
#                     source_id=instance.id,
#                     description=instance.description or f"{stype} expense",
#                     debit=instance.amount or Decimal("0.00"),
#                     credit=Decimal("0.00"),
#                 )
#         return expense_post_save

#     # Pre-delete handler factory
#     def make_pre_delete(stype):
#         @receiver(pre_delete, sender=model_class)
#         def expense_pre_delete(sender, instance, **kwargs):
#             _delete_existing_entries(stype, instance.id)
#         return expense_pre_delete

#     # attach signals
#     make_post_save(source_type)
#     make_pre_delete(source_type)


# #################### for notifications ###################
# # =============================================
# # staff_management/signals.py (Booking Signals)
# # =============================================



# @receiver(post_save, sender=Booking)
# def booking_created_signal(sender, instance, created, **kwargs):
#     """
#     Signal triggered when booking is created or updated
#     """
#     if created:
#         logger.info(f"📌 New booking created: {instance.id}")
        
#         # Schedule 6-hour before check-in reminder
#         schedule_booking_reminder.delay(instance.id)


# @receiver(post_delete, sender=Booking)
# def booking_deleted_signal(sender, instance, **kwargs):
#     """
#     Signal triggered when booking is deleted
#     """
#     logger.info(f"🗑️ Booking deleted: {instance.id}")
#     # You can add cancellation SMS here if needed


