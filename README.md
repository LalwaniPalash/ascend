# Ascend: Personal Finance Web App

## Overview
Ascend is a comprehensive personal finance management web application. It enables users to track and manage accounts, transactions, budgets, debts, loans, credit cards, subscriptions, and financial goals. The app features a minimal, modern dashboard with a white theme and meaningful color accents for clarity and accessibility.

## Features
- **User Registration and Secure Authentication**: Register, log in, and manage your profile securely, including password management and email uniqueness.
- **Timezone and Multi-Currency Support**: Each user can set their preferred time zone and currency. All financial data, summaries, and forms respect these preferences. Currency symbols are handled via a shared macro for consistency.
- **Accounts and Goals**: Add, update, and delete accounts of various types (checking, savings, goals). Set and track savings goals with progress.
- **Budgets with Automation**: Create budget categories with custom time periods (daily, weekly, monthly, etc.). Budgets can auto-reset at the end of each period, and the system tracks remaining and total budget amounts. Visualize budgets as charts or lists with a toggle.
- **Transactions**: Record income, expenses, and transfers. Transactions can be linked to accounts, budgets, and subscriptions. Recent transactions are summarized in the dashboard.
- **Debts, Loans, and Credit Cards**: Manage debts, loans, and credit cards with detailed forms. Track interest rates, balances, due dates, and payment schedules. All financial products are accessible from the dashboard with edit/delete actions.
- **Subscriptions and Recurring Payments**: Add subscriptions with custom frequencies. Enable automatic recurring transactions for subscriptions, which deduct from the correct account and update payment dates automatically.
- **Notifications**: The backend supports a notification model for future in-app alerts and reminders (e.g., payment due, budget exceeded).
- **Interactive Dashboard**: The dashboard features summary cards (total balance, income, expenses, net balance), interactive tables, and a chart/list toggle for budget categories. All actions (add, edit, delete) are accessible from the dashboard.
- **Profile Customization**: Users can update their name, email, time zone, and currency. Name prefix and other personal details are supported.
- **Modular, Macro-Based UI**: The UI uses Jinja2 macros for currency and other repeated elements, ensuring consistency and easy customization.
- **Automation and Scheduling**: Automatic budget resets and recurring transactions are handled by background jobs using APScheduler, respecting user time zones.
- **Analytics Ready**: The structure supports future analytics, trends, and reporting features.
- **Responsive, Minimal UI**: Built with Bootstrap 5 and Remixicon, the interface is clean, modern, and mobile-friendly.

## Technology Stack
- Python 3.12
- Flask (backend, routing, authentication)
- Flask-SQLAlchemy (ORM)
- Flask-Migrate (database migrations)
- SQLite (default database)
- Bootstrap 5 (UI framework)
- Jinja2 (templating)
- APScheduler (background jobs)
- python-dateutil, pytz (date/time handling)

## Setup
1. Clone the repository:
   ```
   git clone <repo-url>
   cd ascend
   ```
2. Create and activate a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run database migrations:
   ```
   flask db upgrade
   ```
5. Start the development server:
   ```
   flask run
   ```
6. Access the app at `http://localhost:5000`

## Usage
- Register a new user and log in.
- Add accounts, set budgets, and record transactions.
- Manage debts, loans, credit cards, subscriptions, and goals from the dashboard.
- Use the dashboard to view summaries, charts, and recent activity.
- Update your profile, change password, set your preferred currency and time zone in user settings.

## Directory Structure
- `website/` - Main application code (routes, models, forms, templates, static files)
- `instance/` - Database file
- `migrations/` - Alembic migration scripts
- `requirements.txt` - Python dependencies

## Future Plans
- Advanced analytics and financial reporting (charts, trends, insights)
- In-app and email notifications for reminders and alerts
- More automation (e.g., bill reminders, smart suggestions)
- Mobile-friendly UI and PWA support
- More granular permissions and multi-user support
- Integration with external APIs (banks, currency rates)
- Profile picture and icon library for user avatars

## Contributing
Note: This project is backend-focused — frontend development isn’t my strong suit.
If you're a frontend developer and would like to collaborate on turning this into a full-fledged app, feel free to reach out via email!

## Email
[plshlalwani@gmail.com](mailto:plshlalwani@gmail.com)