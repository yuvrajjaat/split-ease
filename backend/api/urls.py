from django.urls import path
from . import views

urlpatterns = [
    # Users
    path('users', views.users_list),
    path('users/<str:username>', views.user_detail),

    # Expenses
    path('expenses', views.expenses_list),
    path('expenses/settlement', views.expense_settlement),
    path('expenses/<int:expense_id>', views.expense_detail),

    # Debts
    path('debts', views.debts_list),
    path('optimisedDebts', views.optimised_debts_list),
    path('debts/add', views.debt_add),
    path('debts/settle', views.debt_settle),
    path('debts/<str:from_user>/<str:to_user>', views.debt_detail),
]
