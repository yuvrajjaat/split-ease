import heapq
from .models import Debt, UserDebt, OptimisedDebt


def reverse_debt(from_user, to_user, amount):
    """
    Reverse a previously processed debt (used when deleting/editing expenses).
    This is the inverse of process_new_debt.
    """
    # Step 1: Reverse the aggregate net debts
    from_ud, _ = UserDebt.objects.get_or_create(username=from_user, defaults={'net_debt': 0})
    to_ud, _ = UserDebt.objects.get_or_create(username=to_user, defaults={'net_debt': 0})

    from_ud.net_debt -= amount
    from_ud.save()
    to_ud.net_debt += amount
    to_ud.save()

    # Step 2: Reverse the pairwise debt
    # The original process_new_debt created debt from_user -> to_user
    # So we need to reduce/remove that, or create reverse
    debt_amount = amount
    try:
        existing = Debt.objects.get(from_user=from_user, to_user=to_user)
        if existing.amount > debt_amount:
            existing.amount -= debt_amount
            existing.save()
            return "Debt reduced"
        else:
            debt_amount -= existing.amount
            existing.delete()
    except Debt.DoesNotExist:
        pass

    # If there's remaining amount, create reverse debt
    if debt_amount > 0:
        try:
            reverse = Debt.objects.get(from_user=to_user, to_user=from_user)
            reverse.amount += debt_amount
            reverse.save()
            return "Reverse debt increased"
        except Debt.DoesNotExist:
            Debt.objects.create(from_user=to_user, to_user=from_user, amount=debt_amount)
            return "Reverse debt created"

    return "Debt reversed"


def process_new_debt(from_user, to_user, amount):
    """
    Process a new debt with automatic reverse debt netting.
    """
    # Step 1: Update aggregate net debts
    from_ud, _ = UserDebt.objects.get_or_create(username=from_user, defaults={'net_debt': 0})
    to_ud, _ = UserDebt.objects.get_or_create(username=to_user, defaults={'net_debt': 0})

    from_ud.net_debt += amount
    from_ud.save()
    to_ud.net_debt -= amount
    to_ud.save()

    # Step 2: Check for reverse debt
    debt_amount = amount
    try:
        reverse_debt = Debt.objects.get(from_user=to_user, to_user=from_user)
        if reverse_debt.amount > debt_amount:
            # Reverse debt absorbs new debt entirely
            reverse_debt.amount -= debt_amount
            reverse_debt.save()
            return "Cancelled by reverse debt"
        else:
            # New debt absorbs reverse debt (partially or fully)
            debt_amount -= reverse_debt.amount
            reverse_debt.delete()
    except Debt.DoesNotExist:
        pass

    # Step 3: Create or update remaining debt
    if debt_amount > 0:
        try:
            existing = Debt.objects.get(from_user=from_user, to_user=to_user)
            existing.amount += debt_amount
            existing.save()
            return "Debt updated"
        except Debt.DoesNotExist:
            Debt.objects.create(from_user=from_user, to_user=to_user, amount=debt_amount)
            return "Debt created"

    return "No new debt needed"


def simplify_debts():
    """
    Use greedy algorithm with min-heaps to minimize number of transactions.
    """
    all_user_debts = UserDebt.objects.all()

    debtors = []  # Users who owe money (net_debt > 0)
    creditors = []  # Users who are owed money (net_debt < 0)

    for ud in all_user_debts:
        if ud.net_debt > 0:
            heapq.heappush(debtors, (ud.net_debt, ud.username))
        elif ud.net_debt < 0:
            heapq.heappush(creditors, (-ud.net_debt, ud.username))

    # Clear existing optimised debts
    OptimisedDebt.objects.all().delete()

    # Match debtors with creditors greedily
    while debtors and creditors:
        debt_amount, debtor = heapq.heappop(debtors)
        credit_amount, creditor = heapq.heappop(creditors)

        transaction = min(debt_amount, credit_amount)

        OptimisedDebt.objects.create(
            from_user=debtor,
            to_user=creditor,
            amount=transaction
        )

        debtor_remainder = debt_amount - transaction
        creditor_remainder = credit_amount - transaction

        if debtor_remainder > 0:
            heapq.heappush(debtors, (debtor_remainder, debtor))
        if creditor_remainder > 0:
            heapq.heappush(creditors, (creditor_remainder, creditor))
