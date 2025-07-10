from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from website import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, login_user, logout_user, current_user
import pytz

auth = Blueprint('auth', __name__)

# Register Route
@auth.route('/register', methods=['GET', 'POST'])
def register():
    # Getting Data for signup
    if request.method == "POST":
        nameprefix = request.form.get("name-prefix") 
        firstname = request.form.get("first-name")
        lastname = request.form.get("last-name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmpass = request.form.get("confirmpass")
        timezone = request.form.get('timezone')

        database_email = User.query.filter_by(email=email).first()
        
        if not email or not firstname or not lastname or not password or not confirmpass:
            flash("All fields must be filled.", category="error")
        elif len(email) < 6:
            flash("Email Invalid.", category="error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", category="error")
        elif password != confirmpass:
            flash("Passwords do not match. Try again.", category="error")
        elif database_email: 
            flash("Email already exists.", category='error')
        else:
            new_user = User(
                name_prefix=nameprefix, 
                first_name=firstname, 
                last_name=lastname, 
                email=email, 
                password_hash=generate_password_hash(password),
                time_zone=timezone
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Account Created.", category="success")
            return redirect(url_for("auth.login"))

    timezones = pytz.all_timezones
    return render_template("register.html", timezones=timezones)

# Login Route
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("All fields must be filled.", category="error")

        user = User.query.filter_by(email=email).first()
        if user:
            if user.password_hash is None:
                flash("User account is invalid. Please contact support.", category='error')
            else:
                try:
                    if check_password_hash(user.password_hash, password):
                        flash("Logged in Successfully!", category='success')
                        login_user(user, remember=True)
                        return redirect(url_for('views.dashboard'))
                    else:
                        flash("Password Incorrect, Try Again.", category='error')
                except AttributeError as e:
                    flash(f"An error occurred: {str(e)}", category='error')
                    print(f"Debug - user.password: {user.password_hash}, password: {password}")
        else: 
            flash("Email does not exist.", category='error')

    return render_template("login.html")

# Logout route
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

# Change User Password, only POST requests allowed
@auth.route('/changepass', methods=['POST'])
@login_required
def changepass():
    oldpass = request.form.get("current_password")
    newpass = request.form.get("new_password")
    confirmpass = request.form.get("confirm_password")

    if not oldpass or not newpass or not confirmpass:
        flash("All fields are required.", category='error')
    elif oldpass == newpass:
        flash("New password cannot be same as old password.", category='error')
    elif newpass != confirmpass:
        flash("New Password and Confirm Password are different. Try Again.", category='error')
    else:
        user = User.query.filter_by(id=current_user.id).first()
        if not user:
            flash("User not found.", category='error')
        elif user.password_hash is None:
            flash("User account is invalid. Please contact support.", category='error')
        elif len(newpass) < 8 or len(confirmpass) < 0:
            flash("Password must be at least 8 characters.", category="error")
        else: 
            try:
                if check_password_hash(user.password_hash, oldpass):
                    user.password_hash = generate_password_hash(newpass)
                    db.session.commit()
                    flash("Password changed successfully!", category='success')
                    return redirect(url_for('views.usersettings'))
                else:
                    flash("Incorrect old password.", category='error')
            except Exception as e:
                flash(f"An error occurred: {str(e)}", category='error')
    return redirect(url_for('views.usersettings'))
