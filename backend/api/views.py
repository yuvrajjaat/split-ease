from django.db.models import F
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import User, UserDebt, Debt, OptimisedDebt, Expense, ExpenseBorrower
from .serializers import (
    UserSerializer, DebtSerializer, OptimisedDebtSerializer, ExpenseSerializer
)
from .helpers import process_new_debt, reverse_debt, simplify_debts


# ─── Users ────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def users_list(request):
    if request.method == 'GET':
        users = User.objects.all().order_by('created_at')
        return Response(UserSerializer(users, many=True).data)

    elif request.method == 'POST':
        username = request.data.get('username', '').lower()
        first_name = request.data.get('firstName', username)
        last_name = request.data.get('lastName', username)

        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        UserDebt.objects.create(username=username, net_debt=0)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'DELETE'])
def user_detail(request, username):
    if request.method == 'GET':
        try:
            user = User.objects.get(username=username.lower())
            return Response(UserSerializer(user).data)
        except User.DoesNotExist:
            return Response(None)

    elif request.method == 'DELETE':
        deleted, _ = User.objects.filter(username=username.lower()).delete()
        return Response({'acknowledged': True, 'deletedCount': deleted})


# ─── Expenses ─────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def expenses_list(request):
    if request.method == 'GET':
        expenses = Expense.objects.all().order_by('-created_at')
        return Response(ExpenseSerializer(expenses, many=True).data)

    elif request.method == 'POST':
        title = request.data.get('title')
        author = request.data.get('author', '').lower()
        lender = request.data.get('lender', '').lower()
        borrowers_data = request.data.get('borrowers', [])
        amount = request.data.get('amount', 0)

        # Validate borrower amounts
        total = 0
        for b in borrowers_data:
            b_amount = b[1] if isinstance(b, list) else b.get('amount', 0)
            if b_amount <= 0:
                return Response(
                    "Amount must be greater than £0.",
                    status=status.HTTP_400_BAD_REQUEST
                )
            total += b_amount

        if total != amount:
            return Response(
                "Individual amounts do not add up to the total amount.",
                status=status.HTTP_400_BAD_REQUEST
            )

        expense = Expense.objects.create(
            title=title, author=author, lender=lender, amount=amount
        )

        for b in borrowers_data:
            b_username = b[0] if isinstance(b, list) else b.get('username', '')
            b_amount = b[1] if isinstance(b, list) else b.get('amount', 0)
            ExpenseBorrower.objects.create(
                expense=expense, username=b_username.lower(), amount=b_amount
            )
            if b_username.lower() != lender:
                process_new_debt(b_username.lower(), lender, b_amount)

        simplify_debts()
        return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'DELETE', 'PUT'])
def expense_detail(request, expense_id):
    try:
        expense = Expense.objects.get(id=expense_id)
    except Expense.DoesNotExist:
        return Response("Expense not found.", status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(ExpenseSerializer(expense).data)

    elif request.method == 'DELETE':
        # Reverse all debts created by this expense
        for b in expense.borrowers.all():
            if b.username != expense.lender:
                reverse_debt(b.username, expense.lender, b.amount)
        expense.delete()
        simplify_debts()
        return Response("Expense deleted successfully.")

    elif request.method == 'PUT':
        # Step 1: Reverse old debts
        for b in expense.borrowers.all():
            if b.username != expense.lender:
                reverse_debt(b.username, expense.lender, b.amount)
        expense.borrowers.all().delete()

        # Step 2: Update expense fields
        title = request.data.get('title', expense.title)
        author = request.data.get('author', expense.author).lower()
        lender = request.data.get('lender', expense.lender).lower()
        borrowers_data = request.data.get('borrowers', [])
        amount = request.data.get('amount', expense.amount)

        # Validate borrower amounts
        total = 0
        for b in borrowers_data:
            b_amount = b[1] if isinstance(b, list) else b.get('amount', 0)
            if b_amount <= 0:
                return Response(
                    "Amount must be greater than ₹0.",
                    status=status.HTTP_400_BAD_REQUEST
                )
            total += b_amount

        if total != amount:
            return Response(
                "Individual amounts do not add up to the total amount.",
                status=status.HTTP_400_BAD_REQUEST
            )

        expense.title = title
        expense.author = author
        expense.lender = lender
        expense.amount = amount
        expense.save()

        # Step 3: Create new borrowers and process new debts
        for b in borrowers_data:
            b_username = b[0] if isinstance(b, list) else b.get('username', '')
            b_amount = b[1] if isinstance(b, list) else b.get('amount', 0)
            ExpenseBorrower.objects.create(
                expense=expense, username=b_username.lower(), amount=b_amount
            )
            if b_username.lower() != lender:
                process_new_debt(b_username.lower(), lender, b_amount)

        simplify_debts()
        return Response(ExpenseSerializer(expense).data)


@api_view(['POST'])
def expense_settlement(request):
    title = request.data.get('title')
    author = request.data.get('author', '').lower()
    lender = request.data.get('lender', '').lower()
    borrowers_data = request.data.get('borrowers', [])
    amount = request.data.get('amount', 0)

    expense = Expense.objects.create(
        title=title, author=author, lender=lender, amount=amount
    )

    for b in borrowers_data:
        b_username = b[0] if isinstance(b, list) else b.get('username', '')
        b_amount = b[1] if isinstance(b, list) else b.get('amount', 0)
        ExpenseBorrower.objects.create(
            expense=expense, username=b_username.lower(), amount=b_amount
        )

    return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)


# ─── Debts ────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def debts_list(request):
    debts = Debt.objects.all()
    return Response(DebtSerializer(debts, many=True).data)


@api_view(['GET'])
def optimised_debts_list(request):
    debts = OptimisedDebt.objects.all()
    return Response(OptimisedDebtSerializer(debts, many=True).data)


@api_view(['GET', 'DELETE'])
def debt_detail(request, from_user, to_user):
    if request.method == 'GET':
        try:
            debt = Debt.objects.get(from_user=from_user, to_user=to_user)
            return Response(DebtSerializer(debt).data)
        except Debt.DoesNotExist:
            return Response(None)

    elif request.method == 'DELETE':
        Debt.objects.filter(from_user=from_user, to_user=to_user).delete()
        simplify_debts()
        return Response(f"Debt from '{from_user}' to '{to_user}' deleted successfully.")


@api_view(['POST'])
def debt_add(request):
    from_user = request.data.get('from')
    to_user = request.data.get('to')
    amount = request.data.get('amount', 0)

    result = process_new_debt(from_user, to_user, amount)
    simplify_debts()
    return Response(result, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def debt_settle(request):
    from_user = request.data.get('from')
    to_user = request.data.get('to')
    amount = request.data.get('amount', 0)

    if amount <= 0:
        return Response(
            "Amount must be greater than £0.",
            status=status.HTTP_400_BAD_REQUEST
        )

    # Search for debt in reverse direction
    try:
        debt = Debt.objects.get(from_user=to_user, to_user=from_user)
    except Debt.DoesNotExist:
        return Response(
            "No debt found to settle.",
            status=status.HTTP_400_BAD_REQUEST
        )

    if debt.amount > amount:
        # Partial settlement
        debt.amount -= amount
        debt.save()

        UserDebt.objects.filter(username=from_user).update(
            net_debt=F('net_debt') - amount
        )
        UserDebt.objects.filter(username=to_user).update(
            net_debt=F('net_debt') + amount
        )
        simplify_debts()
        return Response(f"Debt from '{to_user}' to '{from_user}' partially settled and reduced successfully.")

    elif debt.amount == amount:
        # Full settlement
        debt.delete()

        UserDebt.objects.filter(username=from_user).update(
            net_debt=F('net_debt') - amount
        )
        UserDebt.objects.filter(username=to_user).update(
            net_debt=F('net_debt') + amount
        )
        simplify_debts()
        return Response(f"Debt from '{to_user}' to '{from_user}' fully settled and deleted successfully.")

    else:
        return Response(
            "You cannot settle more than the amount of the debt.",
            status=status.HTTP_400_BAD_REQUEST
        )
