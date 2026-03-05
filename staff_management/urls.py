from django.urls import path
from .views import *

urlpatterns = [

    path('log-cleaning', LogRoomCleaningAPIView.as_view(), name="log-cleaning"),
    path('list-room-cleanings', GetRoomCleaningItemsAPIView.as_view(), name="list-room-cleanings"),
    path('list-cleaning',ListRoomCleaningItemsAPIView.as_view(), name="list-cleaning-items"),
    
    
    # CategoryMaster URLs
    path('add-category', AddCategoryAPIView.as_view(), name="add-category"),
    path('list-categories', ListCategoryAPIView.as_view(), name="list-categories"),
    path('delete-category/<int:pk>', DeleteCategoryAPIView.as_view(), name="delete-category"),
    
    # stock item URLs
    path('add-item', AddStockItemAPIView.as_view(), name="add-item"),
    path('list-items', ListStockItemAPIView.as_view(), name="list-items"),
    path('update-item/<int:pk>', UpdateStockItemAPIView.as_view(), name="update-item"),
    path('delete-item/<int:pk>', DeleteStockItemAPIView.as_view(), name="delete-item"),



    #laundry log URLs
    path('log-laundry', CreateLaundryLogAPIView.as_view(), name="log-laundry"),
    path('list-laundry-logs', ListLaundryLogAPIView.as_view(), name="list-laundry-logs"),
    path('list-laundry-items', GetLaundryItemsAPIView.as_view(), name="list-laundry-items"),
    path('update-laundry-received/<int:pk>/<int:item_id>', UpdateLaundryReceivedAPIView.as_view(), name="update-laundry-received"),



    ########################### urls.py ##########################
# other income URLs
    path('other-income', CreateOtherIncomeAPIView.as_view(), name="other-income"),
    path('list-other-income', ListOtherIncomeAPIView.as_view(), name="list-other-income"),
    path('update-other-income/<int:pk>', UpdateOtherIncomeAPIView.as_view(), name="update-other-income"),
    path('delete-other-income/<int:pk>', DeleteOtherIncomeAPIView.as_view(), name="delete-other-income"),
    
# sales income URLs
    path('sales-income', CreateSalesIncomeAPIView.as_view(), name="sales-income"),
    path('list-sales-income', ListSalesIncomeAPIView.as_view(), name="list-sales-income"),
    path('update-sales-income/<int:pk>', UpdateSalesIncomeAPIView.as_view(), name="update-sales-income"),
    path('delete-sales-income/<int:pk>', DeleteSalesIncomeAPIView.as_view(), name="delete-sales-income"),

   #################### urls.py ################

# payment voucher URLs
    path('generate-payment-voucher', NextVoucherNumberAPIView.as_view(), name="create-payment-voucher"),
    path('create-payment-voucher',CreatePaymentVoucherAPIView.as_view(), name="create-payment-voucher"),
    path('list-payment-vouchers',ListPaymentVouchersAPIView.as_view(), name="list-payment-vouchers"),
# Add this to your existing payment voucher URLs
path('delete-payment-voucher/<int:pk>/', DeletePaymentVoucherAPIView.as_view(), name="delete-payment-voucher"),




# expense URLs
    path('add-expense', CreateExpenseAPIView.as_view(), name="add-expense"),
    path('list-expenses', ExpenseListAPIView.as_view(), name="list-expenses"),
    path('update-expense/<int:pk>', UpdateExpenseAPIView.as_view(), name="update-expense"),
    path('delete-expense/<int:pk>', DeleteExpenseAPIView.as_view(), name="delete-expense"),




    ####################### urls.py #########################
# booking URLs
    path('create-booking-type', CreateBookingTypeAPIView.as_view(), name="create-booking-type"),
    path('list-booking-types', BookingTypeListAPIView.as_view(), name="list-booking-types"),
    path('update-booking-type/<int:pk>', UpdateBookingTypeAPIView.as_view(), name="update-booking-type"),
    path('delete-booking-type/<int:pk>', DeleteBookingTypeAPIView.as_view(), name="delete-booking-type"),
    
    path('create-booking', CreateBookingAPIView.as_view(), name="create-booking"),
    path('list-bookings', BookingListAPIView.as_view(), name="list-bookings"),
    path('update-booking/<int:pk>', UpdateBookingAPIView.as_view(), name="update-booking"),
    path('delete-booking/<int:pk>', DeleteBookingAPIView.as_view(), name="delete-booking"),

    path('website-booking', WebsiteBookingAPIView.as_view(), name="website-booking"),
    path('list-website-bookings', WebsiteBookingListAPIView.as_view(), name="list-website-bookings"),



################### urls.py #################

# ledger entries
    path('ledger-entries', LedgerAPIView.as_view(), name="ledger-entries"),
    path('daybook-entries', DaybookAPIView.as_view(), name="daybook-entries"),
    path('backfill-ledger',BackfillLedgerAPIView.as_view(), name="backfill-ledger"),


##################### urls.py ####################
    path('unified-income',UnifiedIncomeListAPIView.as_view(), name="unified-income-list"),


    ################## urls.py ##################
    path('generate-invoice-number', NextInvoiceNumberAPIView.as_view(), name="generate-invoice-number"),





    # cafeteria expense URLs
    path('create-cafeteria-expense', CreateCafeteriaExpenseAPIView.as_view(), name="create-cafeteria-expense"),
    path('list-cafeteria-expenses', CafeteriaExpenseListAPIView.as_view(), name="list-cafeteria-expenses"),
    path('update-cafeteria-expense/<int:pk>', UpdateCafeteriaExpenseAPIView.as_view(), name="update-cafeteria-expense"),
    path('delete-cafeteria-expense/<int:pk>', DeleteCafeteriaExpenseAPIView.as_view(), name="delete-cafeteria-expense"),





    ################## urls.py #######################
# salary expense URLs
    path('create-salary-expense', CreateSalaryExpenseAPIView.as_view(), name="create-salary-expense"),
    path('list-salary-expenses', SalaryExpenseListAPIView.as_view(), name="list-salary-expenses"),
    path('update-salary-expense/<int:pk>', UpdateSalaryExpenseAPIView.as_view(), name="update-salary-expense"),


    path('monthly-ledger-summary',MonthlyLedgerSummaryAPIView.as_view(), name="monthly-ledger-summary"),

]





