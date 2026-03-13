from django.db import models


class User(models.Model):
    username = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.username = self.username.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class UserDebt(models.Model):
    username = models.CharField(max_length=30, unique=True)
    net_debt = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.username}: {self.net_debt}"


class Debt(models.Model):
    from_user = models.CharField(max_length=30)
    to_user = models.CharField(max_length=30)
    amount = models.IntegerField()

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user} -> {self.to_user}: {self.amount}"


class OptimisedDebt(models.Model):
    from_user = models.CharField(max_length=30)
    to_user = models.CharField(max_length=30)
    amount = models.IntegerField()

    def __str__(self):
        return f"{self.from_user} -> {self.to_user}: {self.amount}"


class Expense(models.Model):
    title = models.CharField(max_length=50)
    author = models.CharField(max_length=30)
    lender = models.CharField(max_length=30)
    amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.author = self.author.lower()
        self.lender = self.lender.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.amount}"


class ExpenseBorrower(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='borrowers')
    username = models.CharField(max_length=30)
    amount = models.IntegerField()

    def __str__(self):
        return f"{self.username}: {self.amount}"
