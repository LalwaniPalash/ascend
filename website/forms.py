from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from .models import Account, Transaction, BudgetCategory, Subscription, Loan, Debt, CreditCard
from website import db

forms = Blueprint('forms', __name__)

@forms.route('/api/get_form/<form_type>')
def get_form(form_type):
    form_templates = {
        'account': 'forms/account_form.html',
        'debt': 'forms/debt_form.html',
        'loan': 'forms/loan_form.html',
        'cc': 'forms/credit_card_form.html',
        'goal': 'forms/goal_form.html',
        'transaction': 'forms/transaction_form.html'
    }
    
    if form_type in form_templates:
        return render_template(form_templates[form_type])
    else:
        return jsonify({'error': 'Form not found'}), 404

@forms.route('/add-account', methods=['POST'])
@login_required
def add_account():
    data = request.json
    accountname = data.get("account-name")
    type = data.get("account-type")
    startingBalance = data.get("starting-balance")
    customtype = data.get("custom-account-type")

    try:
        startingBalance = float(startingBalance)
    except ValueError:
        return jsonify({"success": False, "message": "Starting balance must be a valid number."})

    if not accountname or not type or startingBalance is None:
        return jsonify({"success": False, "message": "All fields are required."})
    elif type == "Select account type":
        return jsonify({"success": False, "message": "Select an account type."})
    elif startingBalance < 0.00:
        return jsonify({"success": False, "message": "Balance cannot be negative."})
    elif startingBalance > 1000000000000.00:
        return jsonify({"success": False, "message": "Balance too high. Balance cannot be more than 1 Trillion."})
    elif type == "Other":
        if customtype:
            type = customtype
        else:
            return jsonify({"success": False, "message": "Custom Account Type is a required field."})
    
    try:
        new_account = Account(
            user_id=current_user.id,
            name=accountname,
            type=type,
            starting_balance=startingBalance,
            current_balance=startingBalance,
        )
        db.session.add(new_account)
        db.session.commit()
        return jsonify({"success": True, "message": "Account Added Successfully."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"})

# Add similar routes for other forms (debt, loan, cc, goal, transaction)
# For example:

@forms.route('/add-debt', methods=['POST'])
@login_required
def add_debt():
    # Implement debt addition logic here
    pass

@forms.route('/add-loan', methods=['POST'])
@login_required
def add_loan():
    # Implement loan addition logic here
    pass

@forms.route('/add-credit-card', methods=['POST'])
@login_required
def add_credit_card():
    # Implement credit card addition logic here
    pass

@forms.route('/add-goal', methods=['POST'])
@login_required
def add_goal():
    # Implement goal addition logic here
    pass

@forms.route('/add-transaction', methods=['POST'])
@login_required
def add_transaction():
    # Implement transaction addition logic here
    pass