# HCL-Hackathon
SmartBank - Modular Banking Backend System is a simple banking web application built with Flask and MySQL. This app allows customer registration, login, profile management, password reset, admin management, and basic money transfer simulation between accounts.

# Features
- Customer and Admin Login: Supports user authentication for customers and administrators.

- Registration: Customers can register with essential details, with uniqueness enforced for account number and email.

- Profile Management: Customers can update their profile and delete their account.

- Password Reset: Allows users to securely reset forgotten passwords.

- Admin Dashboard: Admins can view all customer records.

- Session Management: Uses Flask session for login persistence.

- Flash Messages: Display important notifications to users.

# Technologies Used
- Backend: Python, Flask

- Database: MySQL (with flask-mysqldb)

- Frontend: HTML (Jinja templates)

- Session: Flask session

# Setup & Installation Prerequisites
- Python 3.x
- MySQL server (Recommended: XAMPP)
- pip

# Python Dependencies
bash
pip install Flask flask-mysqldb mysql-connector-python
