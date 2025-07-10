from .models import User, Account, Transaction, Subscription, BudgetCategory
import pytz
from datetime import datetime
from website import db
from dateutil.relativedelta import relativedelta

def get_next_date(current_date, frequency):
    """
    Calculate the next date based on the given frequency.

    Args:
        current_date (datetime.date): The current date.
        frequency (str): The reset frequency (e.g., 'Monthly', 'Quarterly', etc.).
        reset_day (int, optional): The day of the month to reset on.

    Returns:
        datetime.date: The next reset date.
    """

    if frequency == 'Daily':
        next_date = current_date + relativedelta(days=1)
    elif frequency == 'Weekly':
        next_date = current_date + relativedelta(weeks=1)
    elif frequency == 'Biweekly':
        next_date = current_date + relativedelta(weeks=1)
    elif frequency == 'Monthly':
        next_date = current_date + relativedelta(months=1)
    elif frequency == 'Quarterly':
        next_date = current_date + relativedelta(months=3)
    elif frequency == 'Biannual':
        next_date = current_date + relativedelta(months=6)
    elif frequency == 'Annual':
        next_date = current_date + relativedelta(years=1)
    else:
        print("Error getting next date.")

    return next_date

def reset_budgets(app):
    """
    Reset budgets for all users where the reset is due.

    Args:
        app: The Flask application instance.
    """
    with app.app_context():
        now_utc = datetime.now(pytz.utc)
        categories = BudgetCategory.query.filter_by(auto_reset=True).all()
        
        for category in categories:
            user = User.query.get(category.user_id)
            user_timezone = pytz.timezone(user.time_zone)
            user_now = user_timezone.localize(now_utc.replace(tzinfo=None))
            
            if category.next_date <= user_now.date():
                category.remaining_amount = category.budget_amount
                category.last_reset = category.next_date
                category.next_date = get_next_date(category.next_date, category.time_period)
        
        db.session.commit()

def add_auto_transactions(app):
    """
    Add automatic transactions for all subscriptions with auto_add_transaction enabled.

    Args:
        app: The Flask application instance.
    """
    with app.app_context():
        now_utc = datetime.now(pytz.utc)
        subscriptions = Subscription.query.filter_by(auto_add_transaction=True).all()
        
        for subscription in subscriptions:
            user = User.query.get(subscription.user_id)
            user_timezone = pytz.timezone(user.time_zone)
            user_now = user_timezone.localize(now_utc.replace(tzinfo=None))
            
            if subscription.next_payment_date <= user_now.date():
                new_transaction = Transaction(
                    user_id=subscription.user_id,
                    account_from_id=subscription.account_id,
                    type='Expense',
                    amount=subscription.amount,
                    description=f"Automatic payment for {subscription.name}",
                    date=subscription.next_payment_date,
                    subscription_id=subscription.id
                )
                db.session.add(new_transaction)
                account_from = Account.query.get(subscription.account_id)
                if account_from:
                    account_from.current_balance -= subscription.amount
                subscription.last_payment_date = subscription.next_payment_date
                subscription.next_payment_date = get_next_date(subscription.next_payment_date, subscription.frequency)

        db.session.commit()
