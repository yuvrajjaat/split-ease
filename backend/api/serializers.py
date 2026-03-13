from rest_framework import serializers
from .models import User, UserDebt, Debt, OptimisedDebt, Expense, ExpenseBorrower


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'created_at']


class UserDebtSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDebt
        fields = ['id', 'username', 'net_debt']


class DebtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debt
        fields = ['id', 'from_user', 'to_user', 'amount']


class OptimisedDebtSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptimisedDebt
        fields = ['id', 'from_user', 'to_user', 'amount']


class ExpenseBorrowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseBorrower
        fields = ['username', 'amount']


class ExpenseSerializer(serializers.ModelSerializer):
    borrowers = ExpenseBorrowerSerializer(many=True, read_only=True)

    class Meta:
        model = Expense
        fields = ['id', 'title', 'author', 'lender', 'borrowers', 'amount', 'created_at']
