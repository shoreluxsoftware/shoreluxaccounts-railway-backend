import logging
from decimal import Decimal
from django.db import transaction
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import (
    LedgerEntry, SalesIncome, OtherIncome, Booking,
    LaundryExpense, CleaningExpense, MessExpense, CafeteriaExpense,
    RentalExpense, SalaryExpense, MiscellaneousExpense,
    MaintenanceExpense, CapitalExpense, OtherExpense,
)
from .booking_service import BookingService  # Remove if missing/causing import error

logger = logging.getLogger(__name__)

def _delete_existing_entries(source_type: str, source_id: int):
    """Helper: remove ledger rows linked to a source"""
    LedgerEntry.objects.filter(source_type=source_type, source_id=source_id).delete()
    logger.debug(f"Deleted ledger entries for {source_type}/{source_id}")

# Booking signals (unchanged, working per your description)
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
            logger.info(f"📌 New booking created: {instance.id}")
            try:
                BookingService.schedule_checkin_reminder(instance)
            except Exception as e:
                logger.error(f"BookingService failed for {instance.id}: {e}")
            return

        old_paid = getattr(instance, "_old_paid_amount", Decimal("0.00"))
        difference = (instance.paid_amount or Decimal("0.00")) - old_paid
        if difference > Decimal("0.00"):
            LedgerEntry.objects.create(
                date=instance.booking_date or instance.checkin_date,
                source_type=source_type,
                source_id=instance.id,
                description=f"Additional payment ({instance.guest_name})",
                credit=difference,
                debit=Decimal("0.00"),
            )

@receiver(pre_delete, sender=Booking)
def booking_pre_delete(sender, instance, **kwargs):
    _delete_existing_entries("booking", instance.id)
    logger.info(f"🗑️ Booking deleted: {instance.id}")

# Income signals (explicit, no loop)
@receiver(post_save, sender=SalesIncome)
def salesincome_post_save(sender, instance, **kwargs):
    source_type = "salesincome"
    with transaction.atomic():
        _delete_existing_entries(source_type, instance.id)
        LedgerEntry.objects.create(
            date=instance.date,
            source_type=source_type,
            source_id=instance.id,
            description=instance.description or "Sales Income",
            credit=instance.amount or Decimal("0.00"),
            debit=Decimal("0.00"),
        )
    logger.debug(f"SalesIncome ledger created: {instance.id}")

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
            description=instance.description or "Other Income",
            credit=instance.amount or Decimal("0.00"),
            debit=Decimal("0.00"),
        )
    logger.debug(f"OtherIncome ledger created: {instance.id}")

@receiver(pre_delete, sender=OtherIncome)
def otherincome_pre_delete(sender, instance, **kwargs):
    _delete_existing_entries("otherincome", instance.id)

# Expense signals (EXPLICIT handlers - fixes loop closure bug)
@receiver(post_save, sender=LaundryExpense)
def laundry_post_save(sender, instance, **kwargs):
    _handle_expense_save("laundryexpense", instance)

@receiver(pre_delete, sender=LaundryExpense)
def laundry_pre_delete(sender, instance, **kwargs):
    _delete_existing_entries("laundryexpense", instance.id)

@receiver(post_save, sender=CleaningExpense)
def cleaning_post_save(sender, instance, **kwargs):
    _handle_expense_save("cleaningexpense", instance)

@receiver(pre_delete, sender=CleaningExpense)
def cleaning_pre_delete(sender, instance, **kwargs):
    _delete_existing_entries("cleaningexpense", instance.id)

@receiver(post_save, sender=SalaryExpense)
def salary_post_save(sender, instance, **kwargs):
    _handle_expense_save("salaryexpense", instance)  # ✅ Creates ledger entry

@receiver(pre_delete, sender=SalaryExpense)
def salary_pre_delete(sender, instance, **kwargs):
    _delete_existing_entries("salaryexpense", instance.id)

    # 🔥 ADD THESE MISSING SIGNALS (after your existing ones):

@receiver(post_save, sender=MessExpense)
def mess_post_save(sender, instance, **kwargs):
    _handle_expense_save("mess", instance)

@receiver(pre_delete, sender=MessExpense)
def mess_pre_delete(sender, instance, **kwargs):
    _delete_existing_entries("mess", instance.id)

@receiver(post_save, sender=CafeteriaExpense)
def cafeteria_post_save(sender, instance, **kwargs):
    _handle_expense_save("cafeteria", instance)

@receiver(pre_delete, sender=CafeteriaExpense)
def cafeteria_pre_delete(sender, instance, **kwargs):
    _delete_existing_entries("cafeteria", instance.id)

@receiver(post_save, sender=RentalExpense)
def rental_post_save(sender, instance, **kwargs):
    _handle_expense_save("rental", instance)

@receiver(pre_delete, sender=RentalExpense)
def rental_pre_delete(sender, instance, **kwargs):
    _delete_existing_entries("rental", instance.id)

@receiver(post_save, sender=MiscellaneousExpense)
def miscellaneous_post_save(sender, instance, **kwargs):
    _handle_expense_save("miscellaneous", instance)

@receiver(pre_delete, sender=MiscellaneousExpense)
def miscellaneous_pre_delete(sender, instance, **kwargs):
    _delete_existing_entries("miscellaneous", instance.id)

@receiver(post_save, sender=MaintenanceExpense)
def maintenance_post_save(sender, instance, **kwargs):
    _handle_expense_save("maintenance", instance)

@receiver(pre_delete, sender=MaintenanceExpense)
def maintenance_pre_delete(sender, instance, **kwargs):
    _delete_existing_entries("maintenance", instance.id)

@receiver(post_save, sender=CapitalExpense)
def capital_post_save(sender, instance, **kwargs):
    _handle_expense_save("capital", instance)

@receiver(pre_delete, sender=CapitalExpense)
def capital_pre_delete(sender, instance, **kwargs):
    _delete_existing_entries("capital", instance.id)

@receiver(post_save, sender=OtherExpense)
def other_post_save(sender, instance, **kwargs):
    _handle_expense_save("other", instance)

@receiver(pre_delete, sender=OtherExpense)
def other_pre_delete(sender, instance, **kwargs):
    _delete_existing_entries("other", instance.id)


# ... Repeat pattern for all: MessExpense, CafeteriaExpense, RentalExpense, SalaryExpense, 
# MiscellaneousExpense, MaintenanceExpense, CapitalExpense, OtherExpense

def _handle_expense_save(source_type: str, instance, **kwargs):
    """Generic expense ledger creator"""
    with transaction.atomic():
        _delete_existing_entries(source_type, instance.id)
        LedgerEntry.objects.create(
            date=instance.date,
            source_type=source_type,
            source_id=instance.id,
            description=instance.description or f"{source_type.replace('expense', ' expense')}",
            debit=instance.amount or Decimal("0.00"),
            credit=Decimal("0.00"),
        )
    logger.debug(f"{source_type} ledger created: {instance.id}")
