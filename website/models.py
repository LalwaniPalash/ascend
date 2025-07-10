from website import db
from flask_login import UserMixin
from datetime import datetime
import pytz
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name_prefix = db.Column(db.String(10))  # e.g., Mr, Ms, Mrs
    first_name = db.Column(db.String(64), nullable=False)  # First name of the user
    last_name = db.Column(db.String(64), nullable=False)  # Last name of the user
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)  # Email of the user
    password_hash = db.Column(db.String(128), nullable=False)  # Password hash of the user
    time_zone = db.Column(db.String(64), nullable=False, default='UTC')  # Default to UTC
    date_created = db.Column(db.DateTime(timezone=True), server_default=func.now())  # Date on which user registered
    currency = db.Column(db.String(8), nullable=False, default='USD')  # User's preferred currency

    # Relationships
    subscriptions = db.relationship('Subscription', backref='user', lazy='dynamic')
    accounts = db.relationship('Account', backref='user', lazy='dynamic')
    budget_categories = db.relationship('BudgetCategory', backref='user', lazy='dynamic')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')
    loans = db.relationship('Loan', backref='user', lazy='dynamic')
    debts = db.relationship('Debt', backref='user', lazy='dynamic')
    credit_cards = db.relationship('CreditCard', backref='user', lazy='dynamic')
    credit_card_payments = db.relationship('CreditCardPayment', backref='user', lazy='dynamic')
    loan_payments = db.relationship('LoanPayment', backref='user', lazy='dynamic')
    debt_payments = db.relationship('DebtPayment', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.email}>'

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(128), nullable=False)  # Name of the subscription
    amount = db.Column(db.Float, nullable=False)  # Amount of the subscription
    frequency = db.Column(db.String(32), nullable=False)  # Frequency: daily, weekly, biweekly, monthly, yearly, etc.
    auto_add_transaction = db.Column(db.Boolean, nullable=False, default=False)  # Boolean to add subscription transaction automatically. 
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))  # Account from which to charge
    last_payment_date = db.Column(db.Date, nullable=True)  # Date of the last payment
    next_payment_date = db.Column(db.Date, nullable=False)  # Date of the next payment
    currency = db.Column(db.String(8), nullable=False, default='USD')

    # Relationships
    transactions = db.relationship('Transaction', backref='subscription', lazy='dynamic')

    def __repr__(self):
        return f'<Subscription {self.name} ({self.amount} {self.currency})>'

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(128), nullable=False)  # Name of the account
    type = db.Column(db.String(64))  # Type of account: checking, savings, goal
    starting_balance = db.Column(db.Float, nullable=False)  # Initial balance of the account
    current_balance = db.Column(db.Float)  # Current balance of the account
    goal_amount = db.Column(db.Float)  # Goal amount for a savings account
    currency = db.Column(db.String(8), nullable=False, default='USD')

    # Relationships
    transactions_from = db.relationship('Transaction', foreign_keys='Transaction.account_from_id', backref='account_from', lazy='dynamic')
    transactions_to = db.relationship('Transaction', foreign_keys='Transaction.account_to_id', backref='account_to', lazy='dynamic')
    credit_card_payments = db.relationship('CreditCardPayment', backref='account', lazy='dynamic')
    subscriptions = db.relationship('Subscription', backref='account', lazy='dynamic')

    def __repr__(self):
        return f'<Account {self.name} ({self.current_balance} {self.currency})>'

class BudgetCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique id for all categories
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Connection to a user
    name = db.Column(db.String(128), nullable=False)  # Name of the budget category
    description = db.Column(db.String(256))  # Description of the budget category
    budget_amount = db.Column(db.Float, nullable=False)  # Budget amount for the category
    remaining_amount = db.Column(db.Float, nullable=False)  # Remaining Budget Amount for the catrgory
    auto_reset = db.Column(db.Boolean, default=False)  # Boolean to reset budgets automatically.
    time_period = db.Column(db.String(32), nullable=False)  # Time period for the budget (e.g., monthly, yearly)
    next_date = db.Column(db.Date, nullable=False)  # Store the date on which budget should be reseted.
    last_reset = db.Column(db.Date, nullable=False)  # Store when the budgeted amount was last reseted
    currency = db.Column(db.String(8), nullable=False, default='USD')

    # Relationships
    transactions = db.relationship('Transaction', backref='budget_category', lazy='dynamic')

    def __repr__(self):
        return f'<BudgetCategory {self.name} ({self.budget_amount} {self.currency})>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    account_from_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)
    account_to_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)
    type = db.Column(db.String(64), nullable=False)  # Type of transaction: income, expense, transfer
    amount = db.Column(db.Float, nullable=False)  # Amount of the transaction
    description = db.Column(db.String(256), nullable=True)  # Description of the transaction
    date = db.Column(db.Date, nullable=False)  # Date of the transaction
    created_on = db.Column(db.DateTime(timezone=True), default=func.now())  # Creation date of the transaction
    budget_category_id = db.Column(db.Integer, db.ForeignKey('budget_category.id'), nullable=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=True)
    currency = db.Column(db.String(8), nullable=False, default='USD')

    # Relationships
    loan_payments = db.relationship('LoanPayment', backref='transaction', lazy='dynamic')
    debt_payments = db.relationship('DebtPayment', backref='transaction', lazy='dynamic')

    def __repr__(self):
        return f'<Transaction {self.type} {self.amount} {self.currency}>'

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    counterparty_name = db.Column(db.String(128))  # Name of the loan counterparty
    amount = db.Column(db.Float, nullable=False)  # Amount of the loan
    interest_rate = db.Column(db.Float)  # Interest rate of the loan
    start_date = db.Column(db.Date)  # Start date of the loan
    end_date = db.Column(db.Date)  # End date of the loan
    type = db.Column(db.String(64))  # Type of loan: loan given, loan taken
    currency = db.Column(db.String(8), nullable=False, default='USD')

    # Relationships
    payments = db.relationship('LoanPayment', backref='loan', lazy='dynamic')

    def __repr__(self):
        return f'<Loan {self.amount} {self.currency}>'

class Debt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type = db.Column(db.String(128))  # Type of debt: student loan, home loan, etc.
    amount = db.Column(db.Float, nullable=False)  # Amount of the debt
    interest_rate = db.Column(db.Float, nullable=False)  # Interest rate of the debt
    start_date = db.Column(db.Date)  # Start date of the debt
    end_date = db.Column(db.Date)  # End date of the debt
    currency = db.Column(db.String(8), nullable=False, default='USD')

    # Relationships
    payments = db.relationship('DebtPayment', backref='debt', lazy='dynamic')

    def __repr__(self):
        return f'<Debt {self.amount} {self.currency}>'

class CreditCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(128))  # Name of the credit card
    limit = db.Column(db.Float)  # Monthly limit of the credit card
    current_balance = db.Column(db.Float)  # Current balance of the credit card
    interest_rate = db.Column(db.Float)  # APR of the card 
    statement_due_date = db.Column(db.Date)  # Due date of the credit card statement
    minimum_payment_due_date = db.Column(db.Date)  # Due date for the minimum payment
    billing_cycle_days = db.Column(db.Integer)  # Number of days in the billing cycle
    currency = db.Column(db.String(8), nullable=False, default='USD')

    # Relationships
    payments = db.relationship('CreditCardPayment', backref='credit_card', lazy='dynamic')

    def __repr__(self):
        return f'<CreditCard {self.name} ({self.current_balance} {self.currency})>'

class CreditCardPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)  # Account used for payment
    credit_card_id = db.Column(db.Integer, db.ForeignKey('credit_card.id'), nullable=False)  # Credit card being paid
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)  # Related transaction
    amount = db.Column(db.Float, nullable=False)  # Amount paid
    date = db.Column(db.Date)  # Date of the payment

    def __repr__(self):
        return f'<CreditCardPayment {self.amount}>'

class LoanPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)  # Loan being paid
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)  # Related transaction
    amount = db.Column(db.Float, nullable=False)  # Amount paid
    date = db.Column(db.Date)  # Date of the payment

    def __repr__(self):
        return f'<LoanPayment {self.amount}>'

class DebtPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    debt_id = db.Column(db.Integer, db.ForeignKey('debt.id'), nullable=False)  # Debt being paid
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)  # Related transaction
    amount = db.Column(db.Float, nullable=False)  # Amount paid
    date = db.Column(db.Date)  # Date of the payment

    def __repr__(self):
        return f'<DebtPayment {self.amount}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.String(256))
    created_on = db.Column(db.DateTime(timezone=True), default=func.now())
    read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Notification {self.message[:20]}>'
