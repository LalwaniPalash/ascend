from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from dateutil.relativedelta import relativedelta
from .models import User, Account, Transaction, BudgetCategory, Subscription, Loan, Debt, CreditCard
from website import db
import pytz

views = Blueprint('views', __name__)

# Helper functions
def get_user_data():
    user_id = current_user.id
    data = {
        'accounts': Account.query.filter_by(user_id=user_id).all(),
        'transactions': Transaction.query.filter_by(user_id=user_id).order_by(Transaction.date.desc()).limit(5).all(),
        'budget_categories': BudgetCategory.query.filter_by(user_id=user_id).all(),
        'subscriptions': Subscription.query.filter_by(user_id=user_id).all(),
        'loans': Loan.query.filter_by(user_id=user_id).all(),
        'debts': Debt.query.filter_by(user_id=user_id).all(),
        'credit_cards': CreditCard.query.filter_by(user_id=user_id).all(),
    }
    return data

def calculate_total_balance(accounts):
    return sum(account.current_balance or 0 for account in accounts)

def parse_float(value, field_name):
    try:
        return float(value)
    except (ValueError, TypeError):
        flash(f"{field_name} must be a valid number.", category='error')
        return None

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    except ValueError:
        flash(f"Date {date_str} is not valid.", category='error')
        return None

# Routes
@views.route('/', methods=['GET'])
@login_required
def dashboard():
    data = get_user_data()
    total_balance = calculate_total_balance(data['accounts'])
    labels = [category.name for category in data['budget_categories']]
    remaining_amounts = [category.remaining_amount for category in data['budget_categories']]
    budget_amounts = [category.budget_amount for category in data['budget_categories']]

    # Calculate summary
    total_income = sum(t.amount for t in data['transactions'] if t.type == 'Income')
    total_expenses = sum(t.amount for t in data['transactions'] if t.type == 'Expense')
    net_balance = total_income - total_expenses
    summary = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_balance': net_balance
    }

    return render_template(
        "dashboard.html", 
        total_balance=total_balance, 
        labels=labels, 
        remaining_amounts=remaining_amounts, 
        budget_amounts=budget_amounts, 
        summary=summary,
        **data
    )

@views.route('/user-settings', methods=['GET'])
@login_required
def user_settings():
    timezones = pytz.all_timezones
    return render_template("user-settings.html", current_user=current_user, timezones=timezones)

@views.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        name_prefix = request.form.get('name-prefix')
        first_name = request.form.get('first-name')
        last_name = request.form.get('last-name')
        email = request.form.get('email')
        timezone = request.form.get('time-zone')
        currency = request.form.get('currency')

        try:
            current_user.name_prefix = name_prefix
            current_user.first_name = first_name
            current_user.last_name = last_name
            current_user.email = email
            current_user.time_zone = timezone
            current_user.currency = currency
            db.session.commit()
            flash("Profile updated successfully!", category='success')
        except Exception as e:
            flash(f"An error occurred: {str(e)}", category='error')

    return redirect(url_for('views.user_settings'))

@views.route('/add-account', methods=['GET', 'POST'])
@login_required
def add_account():
    if request.method == 'POST':
        accountname = request.form.get("account-name")
        type = request.form.get("account-type")
        starting_balance = parse_float(request.form.get("starting-balance"), "Starting balance")
        customtype = request.form.get("custom-account-type")

        if not accountname or not type or starting_balance is None:
            flash("All fields are required.", category='error')
        elif type == "Select account type":
            flash("Select an account type.", category='error')
        elif starting_balance < 0.00:
            flash("Balance cannot be negative.", category='error')
        elif starting_balance > 1000000000000.00:
            flash("Balance too high. Balance cannot be more than 1 Trillion.", category='error')
        elif type == "Other":
            if customtype:
                type = customtype
            else:
                flash("Custom Account Type is a required field.", category='error')
        else:
            new_account = Account(
                user_id=current_user.id,
                name=accountname,
                type=type,
                starting_balance=starting_balance,
                current_balance=starting_balance,
            )
            db.session.add(new_account)
            db.session.commit()
            flash("Account Added Successfully.", category='success')
            return redirect(url_for('views.dashboard'))
        
    return render_template("add-account.html")

@views.route('/add-goal', methods=['GET', 'POST'])
@login_required
def add_goal():
    if request.method == 'POST':
        goalname = request.form.get("goal-name")
        starting_balance = parse_float(request.form.get("starting-balance"), "Starting balance")
        goal_amount = parse_float(request.form.get("goal-amount"), "Goal Amount")

        if not goalname or starting_balance is None or goal_amount is None:
            flash("All fields are required.", category='error')
        elif starting_balance < 0.00:
            flash("Balance cannot be negative.", category='error')
        elif starting_balance > 1000000000000.00:
            flash("Balance too high. Balance cannot be more than 1 Trillion.", category='error')
        elif goal_amount < 1.00:
            flash("Goal Amount must be greater than 1.", category='error')
        elif goal_amount > 1000000000000.00:
            flash("Goal too high. Goal cannot be more than 1 Trillion.", category='error')
        else:
            new_goal = Account(
                user_id=current_user.id,
                name=goalname,
                type="Goal",
                starting_balance=starting_balance,
                current_balance=starting_balance,
                goal_amount=goal_amount
            )
            db.session.add(new_goal)
            db.session.commit()
            flash("Account Added Successfully.", category='success')
            return redirect(url_for('views.dashboard'))
        
    return render_template("add-goal.html")

@views.route('/add-budget-category', methods=['GET', 'POST'])
@login_required
def add_budget_category():
    if request.method == 'POST':
        name = request.form.get("budget-name")
        description = request.form.get("description")
        budgeted = parse_float(request.form.get("amount"), "Budget Amount")
        auto_reset = request.form.get("auto-reset") == 'on'
        time_period = request.form.get("frequency")
        next_reset_date = parse_date(request.form.get('next-reset-date'))

        if not name or budgeted is None:
            flash("Name and Budget Amount are required fields.", category='error')
        elif not 0.00 <= budgeted <= 1000000000000.00:
            flash("Invalid Budget Amount.", category='error')
        elif auto_reset and (not time_period or not next_reset_date):
            flash("Time Period and Reset Date are required for auto-reset budgets.", category='error')
        else:
            if auto_reset:
                last_date = None
                if time_period == "Daily":
                    last_date = next_reset_date - relativedelta(days=1)
                elif time_period == "Weekly":
                    last_date = next_reset_date - relativedelta(weeks=1)
                elif time_period == "Biweekly":
                    last_date = next_reset_date - relativedelta(weeks=2)
                elif time_period == "Monthly":
                    last_date = next_reset_date - relativedelta(months=1)
                elif time_period == "Quarterly":
                    last_date = next_reset_date - relativedelta(months=3)
                elif time_period == "Biannual":
                    last_date = next_reset_date - relativedelta(months=6)
                elif time_period == "Annual":
                    last_date = next_reset_date - relativedelta(years=1)

            new_budget_category = BudgetCategory(
                user_id=current_user.id,
                name=name,
                description=description,
                budget_amount=budgeted,
                remaining_amount=budgeted,
                auto_reset=auto_reset,
                time_period=time_period if auto_reset else None,
                next_date=next_reset_date if auto_reset else None,
                last_reset=last_date if auto_reset else None
            )
            db.session.add(new_budget_category)
            db.session.commit()

            flash("Budget Category added successfully.", category='success')
            return redirect(url_for('views.dashboard'))

    user_data = get_user_data()
    total_balance = calculate_total_balance(user_data['accounts'])
    
    return render_template("add-budget-category.html", user_data=user_data, total_balance=total_balance)

@views.route('/update-budget-category/<int:id>', methods=['GET', 'POST'])
@login_required
def update_budget_category(id):
    budget_category = BudgetCategory.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('budget-name')
        description = request.form.get('description')
        budgeted = parse_float(request.form.get("amount"), "Budget Amount")
        auto_reset = request.form.get("auto-reset") == 'on'
        time_period = request.form.get("frequency")
        next_reset_date = parse_date(request.form.get('next-reset-date'))

        if not name or budgeted is None:
            flash("Name and Budget Amount are required fields.", category='error')
        elif not 0.00 <= budgeted <= 1000000000000.00:
            flash("Invalid Budget Amount.", category='error')
        elif auto_reset and (not time_period or not next_reset_date):
            flash("Time Period and Reset Date are required for auto-reset budgets.", category='error')
        else:
            last_date = None
            if auto_reset:
                if time_period == "Daily":
                    last_date = next_reset_date - relativedelta(days=1)
                elif time_period == "Weekly":
                    last_date = next_reset_date - relativedelta(weeks=1)
                elif time_period == "Biweekly":
                    last_date = next_reset_date - relativedelta(weeks=2)
                elif time_period == "Monthly":
                    last_date = next_reset_date - relativedelta(months=1)
                elif time_period == "Quarterly":
                    last_date = next_reset_date - relativedelta(months=3)
                elif time_period == "Biannual":
                    last_date = next_reset_date - relativedelta(months=6)
                elif time_period == "Annual":
                    last_date = next_reset_date - relativedelta(years=1)

            budget_category.name = name
            budget_category.description = description
            budget_category.budget_amount = budgeted
            budget_category.auto_reset = auto_reset
            budget_category.time_period = time_period if auto_reset else None
            budget_category.next_date = next_reset_date if auto_reset else None
            budget_category.last_reset = last_date if auto_reset else None

            db.session.commit()
            flash("Budget Category updated successfully.", category='success')
            return redirect(url_for('views.dashboard'))

    user_data = get_user_data()
    total_balance = calculate_total_balance(user_data['accounts'])
    
    return render_template("update-budget-category.html", budget_category=budget_category, user_data=user_data, total_balance=total_balance)

@views.route('/delete-budget-category/<int:id>', methods=['POST'])
@login_required
def delete_budget_category(id):
    budget_category = BudgetCategory.query.get_or_404(id)

    # Optional: check if there are any transactions linked to this budget category
    if budget_category.transactions.count() > 0:
        flash("Cannot delete budget category with existing transactions.", category='error')
        return redirect(url_for('views.dashboard'))

    db.session.delete(budget_category)
    db.session.commit()
    flash("Budget Category deleted successfully.", category='success')
    return redirect(url_for('views.dashboard'))

@views.route('/add-transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        type = request.form.get('transaction-type')
        amount = parse_float(request.form.get('amount'), "Amount")
        description = request.form.get('description')
        date = request.form.get('date')
        account_from_id = request.form.get('account_from_id')
        account_to_id = request.form.get('account_to_id')
        budget_category_id = request.form.get('budget_category_id')
        subscription_id = request.form.get('subscription_id')

        if not type or amount is None or not date:
            flash("Type, amount, and date are required fields.", category='error')
        elif amount < 0 or amount > 1000000000000.00:
            flash("Invalid Amount, try again.", category='error')
        elif type == "Income" and not account_to_id:
            flash("'Account To' is a required field for Income transactions.", category='error')
        elif type == "Expense" and not account_from_id:
            flash("'Account From' is a required field for Expense transactions.", category='error')
        elif type == "Transfer" and (not account_from_id or not account_to_id):
            flash("'Account From' and 'Account To' are required fields for Transfer transactions.", category='error')
        else:
            account_from = Account.query.get(account_from_id) if account_from_id else None
            account_to = Account.query.get(account_to_id) if account_to_id else None
            budget_category = BudgetCategory.query.get(budget_category_id) if budget_category_id else None

            if type == "Income":
                account_to.current_balance += amount
            elif type == "Expense":
                account_from.current_balance -= amount
                if budget_category:
                    budget_category.remaining_amount -= amount
            elif type == "Transfer":
                account_from.current_balance -= amount
                account_to.current_balance += amount

            new_transaction = Transaction(
                user_id=current_user.id,
                type=type,
                amount=amount,
                description=description,
                date=datetime.strptime(date, '%Y-%m-%d'),
                account_from_id=account_from_id if account_from_id else None,
                account_to_id=account_to_id if account_to_id else None,
                budget_category_id=budget_category_id if budget_category_id else None,
                subscription_id=subscription_id if subscription_id else None
            )
            db.session.add(new_transaction)
            db.session.commit()
            flash("Transaction added successfully.", category='success')
            return redirect(url_for('views.dashboard'))

    accounts = Account.query.filter_by(user_id=current_user.id).all()
    budget_categories = BudgetCategory.query.filter_by(user_id=current_user.id).all()
    subscriptions = Subscription.query.filter_by(user_id=current_user.id).all()
    
    return render_template('add-transaction.html', accounts=accounts, budget_categories=budget_categories, subscriptions=subscriptions)

@views.route('/update-transaction/<int:id>', methods=['GET', 'POST'])
@login_required
def update_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    
    if request.method == 'POST':
        old_data = {
            'type': transaction.type,
            'amount': transaction.amount,
            'account_from_id': transaction.account_from_id,
            'account_to_id': transaction.account_to_id,
            'budget_category_id': transaction.budget_category_id,
        }

        # Get the new data entered by the user
        new_type = request.form.get('type')
        new_amount = parse_float(request.form.get('amount'), "Amount")
        new_description = request.form.get('description')
        new_date = parse_date(request.form.get('date'))
        new_account_from_id = request.form.get('account_from_id')
        new_account_to_id = request.form.get('account_to_id')
        new_budget_category_id = request.form.get('budget_category_id')

        if new_amount is None:
            return redirect(url_for('views.update_transaction', id=id))
        elif new_type not in ['Income', 'Expense', 'Transfer']:
            flash("Transaction has to be one of these: Income, Expense, Transfer.", category='error')

        # Fetch accounts and budget categories involved
        old_account_from = Account.query.get(old_data['account_from_id']) if old_data['account_from_id'] else None
        old_account_to = Account.query.get(old_data['account_to_id']) if old_data['account_to_id'] else None
        old_budget_category = BudgetCategory.query.get(old_data['budget_category_id']) if old_data['budget_category_id'] else None
        new_account_from = Account.query.get(new_account_from_id) if new_account_from_id else None
        new_account_to = Account.query.get(new_account_to_id) if new_account_to_id else None
        new_budget_category = BudgetCategory.query.get(new_budget_category_id) if new_budget_category_id else None

        if new_type == "Income" and not new_account_to_id:
            flash("'Account To' is a required field for Income transactions.", category='error')
        elif new_type == "Expense" and not new_account_from_id:
            flash("'Account From' is a required field for Expense transactions.", category='error')
        elif new_type == "Transfer" and (not new_account_from_id or not new_account_to_id):
            flash("'Account From' and 'Account To' are required fields for Transfer transactions.", category='error')
        else:
            # Revert the changes made to the accounts and budget category
            if old_data['type'] == "Income":
                old_account_to.current_balance -= old_data['amount']
            elif old_data['type'] == "Expense":
                old_account_from.current_balance += old_data['amount']
                if old_budget_category:
                    old_budget_category.remaining_amount += old_data['amount']
            elif old_data['type'] == "Transfer":
                old_account_from.current_balance += old_data['amount']
                old_account_to.current_balance -= old_data['amount']

            # Apply the new changes to the accounts and budget category
            if new_type == "Income":
                new_account_to.current_balance += new_amount
            elif new_type == "Expense":
                new_account_from.current_balance -= new_amount
                if new_budget_category:
                    new_budget_category.remaining_amount -= new_amount
            elif new_type == "Transfer":
                new_account_from.current_balance -= new_amount
                new_account_to.current_balance += new_amount

            # Update the transaction with the new data
            transaction.type = new_type
            transaction.amount = new_amount
            transaction.description = new_description
            transaction.date = new_date
            transaction.account_from_id = new_account_from_id if new_account_from_id else None
            transaction.account_to_id = new_account_to_id if new_account_to_id else None
            transaction.budget_category_id = new_budget_category_id if new_budget_category_id else None

            try:
                db.session.commit()
                flash("Transaction updated successfully.", category='success')
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred: {str(e)}", category='error')
                print(f"Error: {str(e)}")

            return redirect(url_for('views.dashboard'))

    # Fetch all accounts and budget categories belonging to the current user
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    budget_categories = BudgetCategory.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'update-transaction.html', 
        transaction=transaction,
        accounts=accounts,
        budget_categories=budget_categories
    )

@views.route('/delete-transaction/int:id', methods=['POST'])
@login_required
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    type = transaction.type
    amount = transaction.amount
    account_from_id = transaction.account_from_id
    account_to_id = transaction.account_to_id
    budget_category_id = transaction.budget_category_id

    if type == "Income":
        account_to = Account.query.get(account_to_id)
        account_to.current_balance -= amount
    elif type == "Expense":
        account_from = Account.query.get(account_from_id)
        account_from.current_balance += amount
        if budget_category_id:
            budget_category = BudgetCategory.query.get(budget_category_id)
            budget_category.remaining_amount += amount
    elif type == "Transfer":
        account_from = Account.query.get(account_from_id)
        account_to = Account.query.get(account_to_id)
        account_from.current_balance += amount
        account_to.current_balance -= amount
    try:
        db.session.delete(transaction)
        db.session.commit()
        flash("Transaction deleted successfully.", category='success')
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", category='error')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('views.dashboard'))

@views.route('/add-subscription', methods=['GET', 'POST'])
@login_required
def add_subscription():
    if request.method == 'POST':
        name = request.form.get('name')
        amount = parse_float(request.form.get('amount'), "Amount")
        start_date = parse_date(request.form.get('start-date'))
        end_date = parse_date(request.form.get('end-date'))
        interval = request.form.get('interval')
        account_id = request.form.get('account_id')

        if not name or amount is None or start_date is None or end_date is None or not interval or not account_id:
            flash("All fields are required.", category='error')
        elif amount < 0.01 or amount > 1000000000000.00:
            flash("Amount must be between 0.01 and 1 Trillion.", category='error')
        elif end_date < start_date:
            flash("End date must be after the start date.", category='error')
        else:
            new_subscription = Subscription(
                user_id=current_user.id,
                name=name,
                amount=amount,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                account_id=account_id
            )
            db.session.add(new_subscription)
            db.session.commit()
            flash("Subscription added successfully.", category='success')
            return redirect(url_for('views.dashboard'))
    
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('add-subscription.html', accounts=accounts)

@views.route('/update-subscription/<int:id>', methods=['GET', 'POST'])
@login_required
def update_subscription(id):
    subscription = Subscription.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form.get('name')
        amount = parse_float(request.form.get('amount'), "Amount")
        start_date = parse_date(request.form.get('start-date'))
        end_date = parse_date(request.form.get('end-date'))
        interval = request.form.get('interval')
        account_id = request.form.get('account_id')

        if not name or amount is None or start_date is None or end_date is None or not interval or not account_id:
            flash("All fields are required.", category='error')
        elif amount < 0.01 or amount > 1000000000000.00:
            flash("Amount must be between 0.01 and 1 Trillion.", category='error')
        elif end_date < start_date:
            flash("End date must be after the start date.", category='error')
        else:
            subscription.name = name
            subscription.amount = amount
            subscription.start_date = start_date
            subscription.end_date = end_date
            subscription.interval = interval
            subscription.account_id = account_id
            
            db.session.commit()
            flash("Subscription updated successfully.", category='success')
            return redirect(url_for('views.dashboard'))
    
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('update-subscription.html', subscription=subscription, accounts=accounts)

@views.route('/delete-subscription/<int:id>', methods=['POST'])
@login_required
def delete_subscription(id):
    subscription = Subscription.query.get_or_404(id)
    db.session.delete(subscription)
    db.session.commit()
    flash("Subscription deleted successfully.", category='success')
    return redirect(url_for('views.dashboard'))

@views.route('/add-loan', methods=['GET', 'POST'])
@login_required
def add_loan():
    if request.method == 'POST':
        name = request.form.get('name')
        amount = parse_float(request.form.get('amount'), "Amount")
        interest_rate = parse_float(request.form.get('interest-rate'), "Interest Rate")
        start_date = parse_date(request.form.get('start-date'))
        end_date = parse_date(request.form.get('end-date'))
        account_id = request.form.get('account_id')

        if not name or amount is None or interest_rate is None or start_date is None or end_date is None or not account_id:
            flash("All fields are required.", category='error')
        elif amount <= 0 or amount > 1000000000000.00:
            flash("Amount must be positive and less than 1 Trillion.", category='error')
        elif interest_rate < 0 or interest_rate > 100:
            flash("Interest rate must be between 0 and 100.", category='error')
        elif end_date < start_date:
            flash("End date must be after the start date.", category='error')
        else:
            new_loan = Loan(
                user_id=current_user.id,
                name=name,
                amount=amount,
                interest_rate=interest_rate,
                start_date=start_date,
                end_date=end_date,
                account_id=account_id
            )
            db.session.add(new_loan)
            db.session.commit()
            flash("Loan added successfully.", category='success')
            return redirect(url_for('views.dashboard'))
    
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('add-loan.html', accounts=accounts)

@views.route('/update-loan/<int:id>', methods=['GET', 'POST'])
@login_required
def update_loan(id):
    loan = Loan.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form.get('name')
        amount = parse_float(request.form.get('amount'), "Amount")
        interest_rate = parse_float(request.form.get('interest-rate'), "Interest Rate")
        start_date = parse_date(request.form.get('start-date'))
        end_date = parse_date(request.form.get('end-date'))
        account_id = request.form.get('account_id')

        if not name or amount is None or interest_rate is None or start_date is None or end_date is None or not account_id:
            flash("All fields are required.", category='error')
        elif amount <= 0 or amount > 1000000000000.00:
            flash("Amount must be positive and less than 1 Trillion.", category='error')
        elif interest_rate < 0 or interest_rate > 100:
            flash("Interest rate must be between 0 and 100.", category='error')
        elif end_date < start_date:
            flash("End date must be after the start date.", category='error')
        else:
            loan.name = name
            loan.amount = amount
            loan.interest_rate = interest_rate
            loan.start_date = start_date
            loan.end_date = end_date
            loan.account_id = account_id
            
            db.session.commit()
            flash("Loan updated successfully.", category='success')
            return redirect(url_for('views.dashboard'))
    
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('update-loan.html', loan=loan, accounts=accounts)

@views.route('/delete-loan/<int:id>', methods=['POST'])
@login_required
def delete_loan(id):
    loan = Loan.query.get_or_404(id)
    db.session.delete(loan)
    db.session.commit()
    flash("Loan deleted successfully.", category='success')
    return redirect(url_for('views.dashboard'))

@views.route('/add-debt', methods=['GET', 'POST'])
@login_required
def add_debt():
    if request.method == 'POST':
        type = request.form.get('type')
        amount = parse_float(request.form.get('amount'), "Amount")
        interest_rate = parse_float(request.form.get('interest_rate'), "Interest Rate")
        start_date = parse_date(request.form.get('start_date'))
        end_date = parse_date(request.form.get('end_date'))

        if not type or amount is None or interest_rate is None:
            flash("Type, amount, and interest rate are required fields.", category='error')
        elif amount <= 0 or amount > 1000000000000.00:
            flash("Amount must be positive and less than 1 Trillion.", category='error')
        elif interest_rate < 0 or interest_rate > 100:
            flash("Interest rate must be between 0 and 100.", category='error')
        elif end_date and start_date and end_date < start_date:
            flash("End date must be after the start date.", category='error')
        else:
            new_debt = Debt(
                user_id=current_user.id,
                type=type,
                amount=amount,
                interest_rate=interest_rate,
                start_date=start_date,
                end_date=end_date,
            )
            db.session.add(new_debt)
            db.session.commit()
            flash("Debt added successfully.", category='success')
            return redirect(url_for('views.dashboard'))
    
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('add-debt.html', accounts=accounts)

@views.route('/update-debt/<int:id>', methods=['GET', 'POST'])
@login_required
def update_debt(id):
    debt = Debt.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form.get('name')
        amount = parse_float(request.form.get('amount'), "Amount")
        interest_rate = parse_float(request.form.get('interest-rate'), "Interest Rate")
        start_date = parse_date(request.form.get('start-date'))
        end_date = parse_date(request.form.get('end-date'))
        account_id = request.form.get('account_id')

        if not name or amount is None or interest_rate is None or start_date is None or end_date is None or not account_id:
            flash("All fields are required.", category='error')
        elif amount <= 0 or amount > 1000000000000.00:
            flash("Amount must be positive and less than 1 Trillion.", category='error')
        elif interest_rate < 0 or interest_rate > 100:
            flash("Interest rate must be between 0 and 100.", category='error')
        elif end_date < start_date:
            flash("End date must be after the start date.", category='error')
        else:
            debt.name = name
            debt.amount = amount
            debt.interest_rate = interest_rate
            debt.start_date = start_date
            debt.end_date = end_date
            debt.account_id = account_id
            
            db.session.commit()
            flash("Debt updated successfully.", category='success')
            return redirect(url_for('views.dashboard'))
    
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('update-debt.html', debt=debt, accounts=accounts)

@views.route('/delete-debt/<int:id>', methods=['POST'])
@login_required
def delete_debt(id):
    debt = Debt.query.get_or_404(id)
    db.session.delete(debt)
    db.session.commit()
    flash("Debt deleted successfully.", category='success')
    return redirect(url_for('views.dashboard'))

@views.route('/add-credit-card', methods=['GET', 'POST'])
@login_required
def add_credit_card():
    if request.method == 'POST':
        name = request.form.get('name')
        limit = parse_float(request.form.get('limit'), "Limit")
        current_balance = parse_float(request.form.get('current-balance'), "Current Balance")
        interest_rate = parse_float(request.form.get('interest-rate'), "Interest Rate")
        next_statement_due_date = parse_date(request.form.get('statement-due-date'))
        next_min_payment_due_date = parse_date(request.form.get('min-payment-due-date'))
        billing_days = request.form.get('billing-cycle-days')

        if not name or limit is None or current_balance is None or interest_rate is None or next_statement_due_date is None or next_min_payment_due_date is None or billing_days is None:
            flash("All fields are required.", category='error')
        elif limit <= 0 or limit > 1000000000000.00:
            flash("Credit card limit must be positive and less than 1 Trillion.", category='error')
        elif current_balance < 0 or current_balance > limit:
            flash("Current balance cannot be negative or exceed the credit card limit.", category='error')
        elif interest_rate < 0 or interest_rate > 100:
            flash("Interest rate must be between 0 and 100.", category='error')
        elif next_statement_due_date < datetime.now().date():
            flash("Next statement due date must be in the future.", category='error')
        elif next_min_payment_due_date < datetime.now().date():
            flash("Next minimum payment due date must be in the future.", category='error')
        elif billing_days < 25 or billing_days > 32:
            flash("Billing days must be between 25 and 32.", category='error')
        else:
            new_credit_card = CreditCard(
                user_id=current_user.id,
                name=name,
                limit=limit,
                current_balance=current_balance,
                interest_rate=interest_rate,
                statement_due_date=next_statement_due_date,
                minimum_payment_due_date=next_min_payment_due_date,
                billing_cycle_days=billing_days
            )
            db.session.add(new_credit_card)
            db.session.commit()
            flash("Credit Card added successfully.", category='success')
            return redirect(url_for('views.dashboard'))
    
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('add-credit-card.html', accounts=accounts)

@views.route('/update-credit-card/<int:id>', methods=['GET', 'POST'])
@login_required
def update_credit_card(id):
    credit_card = CreditCard.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form.get('name')
        limit = parse_float(request.form.get('limit'), "Limit")
        current_balance = parse_float(request.form.get('current-balance'), "Current Balance")
        interest_rate = parse_float(request.form.get('interest-rate'), "Interest Rate")
        due_date = parse_date(request.form.get('due-date'))
        account_id = request.form.get('account_id')

        if not name or limit is None or current_balance is None or interest_rate is None or due_date is None or not account_id:
            flash("All fields are required.", category='error')
        elif limit <= 0 or limit > 1000000000000.00:
            flash("Credit card limit must be positive and less than 1 Trillion.", category='error')
        elif current_balance < 0 or current_balance > limit:
            flash("Current balance cannot be negative or exceed the credit card limit.", category='error')
        elif interest_rate < 0 or interest_rate > 100:
            flash("Interest rate must be between 0 and 100.", category='error')
        elif due_date < datetime.now().date():
            flash("Due date must be in the future.", category='error')
        else:
            credit_card.name = name
            credit_card.limit = limit
            credit_card.current_balance = current_balance
            credit_card.interest_rate = interest_rate
            credit_card.due_date = due_date
            credit_card.account_id = account_id
            
            db.session.commit()
            flash("Credit Card updated successfully.", category='success')
            return redirect(url_for('views.dashboard'))
    
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('update-credit-card.html', credit_card=credit_card, accounts=accounts)

@views.route('/delete-credit-card/<int:id>', methods=['POST'])
@login_required
def delete_credit_card(id):
    credit_card = CreditCard.query.get_or_404(id)
    db.session.delete(credit_card)
    db.session.commit()
    flash("Credit Card deleted successfully.", category='success')
    return redirect(url_for('views.dashboard'))