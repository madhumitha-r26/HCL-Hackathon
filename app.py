from flask import *
from flask_mysqldb import MySQL   
from MySQLdb.cursors import DictCursor                               
import os     
import mysql.connector

app=Flask(__name__)

# XAMPP MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'       # Default XAMPP username
app.config['MYSQL_PASSWORD'] = ''       # Empty password by default
app.config['MYSQL_DB'] = 'smartbank'    # Replace with your actual database name
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
app.secret_key = 'abcde12345'  


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/customer")
def customer():
    if not session.get('loggedin') or session.get('role') != 'customer':
        flash('Please login to access this page', 'warning')
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor(cursorclass=DictCursor)
    cur.execute('SELECT * FROM customers WHERE email = %s', (session['email'],))
    user = cur.fetchone()
    cur.close()
    
    return render_template("customer.html", user=user)

    
    cur = mysql.connection.cursor(cursorclass=DictCursor)
    
    try:
        # Get sender's account details
        cur.execute('''
            SELECT account_number, balance, password 
            FROM customers 
            WHERE email = %s
        ''', (session['email'],))
        sender = cur.fetchone()
        
        if request.method == 'POST':
            recipient_account = request.form.get('recipient_account')
            amount = float(request.form.get('amount'))
            description = request.form.get('description', '')
            password = request.form.get('password')
            
            # Validate inputs
            if not all([recipient_account, amount, password]):
                flash('Please fill in all required fields', 'danger')
                return render_template('transfer_amount.html', balance=sender['balance'])
            
            # Verify password
            if password != sender['password']:
                flash('Invalid password', 'danger')
                return render_template('transfer_amount.html', balance=sender['balance'])
            
            # Check if recipient exists
            cur.execute('SELECT * FROM customers WHERE account_number = %s', (recipient_account,))
            recipient = cur.fetchone()
            
            if not recipient:
                flash('Recipient account not found', 'danger')
                return render_template('transfer_amount.html', balance=sender['balance'])
            
            # Check if sender has sufficient balance
            if float(sender['balance']) < amount:
                flash('Insufficient balance', 'danger')
                return render_template('transfer_amount.html', balance=sender['balance'])
            
            # Perform transfer
            try:
                # Deduct from sender
                cur.execute('''
                    UPDATE customers 
                    SET balance = balance - %s 
                    WHERE account_number = %s
                ''', (amount, sender['account_number']))
                
                # Add to recipient
                cur.execute('''
                    UPDATE customers 
                    SET balance = balance + %s 
                    WHERE account_number = %s
                ''', (amount, recipient_account))
                
                # Record transaction
                cur.execute('''
                    INSERT INTO transactions 
                    (sender_account, recipient_account, amount, description, transaction_date) 
                    VALUES (%s, %s, %s, %s, NOW())
                ''', (sender['account_number'], recipient_account, amount, description))
                
                mysql.connection.commit()
                flash('Transfer completed successfully!', 'success')
                return redirect(url_for('customer'))
                
            except Exception as e:
                mysql.connection.rollback()
                flash('An error occurred during transfer. Please try again.', 'danger')
        
        return render_template('transfer_amount.html', balance=sender['balance'])
        
    except Exception as e:
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('customer'))
        
    finally:
        cur.close()

@app.route("/admin")
def admin():
    if not session.get('loggedin') or session.get('role') != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    cur2=mysql.connection.cursor()
    cur2.execute("SELECT * FROM customers")
    data2=cur2.fetchall()
    cur2.close()
    return render_template('admin.html',user_data=data2)

@app.route('/register', methods=['GET', 'POST'])
def register():
     if (request.method == 'POST'):
        # Get form data
        account_number = request.form.get('account_number')
        username = request.form.get('username')
        dob = request.form.get('dob')
        aadhar_number = request.form.get('aadhar_number')
        pan_number = request.form.get('pan_number')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        password = request.form.get('password')
        amount = request.form.get('amount')

        # Validate required fields
        if not all([account_number, username, dob, aadhar_number, pan_number, phone_number, email, password, amount]):
            flash("All fields are required!", "danger")
            return render_template('register.html')

        cur1 = mysql.connection.cursor()
        cur1.execute('SELECT email FROM customers WHERE email = %s OR account_number = %s', (email, account_number))
        existing = cur1.fetchone()

        if existing:
            flash("An account with this email or account number already exists.", "danger")
            return render_template('register.html')
        
        else:
            cur1.execute(
                    "INSERT INTO customers (account_number, username, dob, aadhar_number, pan_number, phone_number, email, password, amount) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (account_number, username, dob, aadhar_number, pan_number, phone_number, email, password, amount)
                )
            mysql.connection.commit()
            cur1.close()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
       
     return render_template('register.html') 

        
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        

        # Check for admin login
        if email == "admin@gmail.com" and password == "admin123":
            session['loggedin'] = True
            session['role'] = 'admin'
            session['email'] = email
            session['username'] = 'Admin'
            flash('Welcome Admin!', 'success')
            return redirect(url_for('admin'))
    
        # Check customer login
        cur = mysql.connection.cursor(cursorclass=DictCursor)
        cur.execute("SELECT * FROM customers WHERE email=%s AND password=%s", (email, password))
        data = cur.fetchone()
        cur.close()

        if data:
            session['loggedin'] = True
            session['role'] = 'customer'
            session['username'] = data['username']
            session['email'] = data['email']
            flash('Login successful!', 'success')
            return redirect(url_for('customer'))
        else:
            flash("Invalid Email or Password", "danger")
            return render_template('login.html')
    
    return render_template('login.html')



@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not all([email, new_password, confirm_password]):
            flash('Please fill in all fields', 'danger')
            return render_template('forgot_password.html')
            
        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('forgot_password.html')
            
        # Check if email exists
        cur = mysql.connection.cursor(cursorclass=DictCursor)
        cur.execute('SELECT * FROM customers WHERE email = %s', (email,))
        user = cur.fetchone()
        
        if not user:
            flash('No account found with that email address', 'danger')
            return render_template('forgot_password.html')
            
        try:
            # Update password
            cur.execute('UPDATE customers SET password = %s WHERE email = %s', 
                       (new_password, email))
            mysql.connection.commit()
            flash('Password has been updated successfully! You can now login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash('An error occurred while updating the password', 'danger')
            return render_template('forgot_password.html')
            
        finally:
            cur.close()
            
    return render_template('forgot_password.html')


@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    if not session.get('loggedin'):
        flash('Please login to update your profile', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        cur = mysql.connection.cursor(cursorclass=DictCursor)
        cur.execute('SELECT * FROM customers WHERE email = %s', (session['email'],))
        user = cur.fetchone()
        cur.close()
        return render_template('update_profile.html', user=user)
    
    if request.method == 'POST':
        username = request.form.get('username')
        dob = request.form.get('dob')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        
        # Validate required fields
        if not all([username, dob, phone_number, email]):
            flash('Please fill all required fields', 'danger')
            return redirect(url_for('update_profile'))
        
        cur = mysql.connection.cursor()
        try:
            # Check if email exists for other users
            if email != session['email']:
                cur.execute('SELECT * FROM customers WHERE email = %s AND email != %s', 
                          (email, session['email']))
                if cur.fetchone():
                    flash('Email already exists', 'danger')
                    return redirect(url_for('update_profile'))
            
            # Update user information
            cur.execute('''
                UPDATE customers 
                SET username = %s, dob = %s, phone_number = %s, email = %s 
                WHERE email = %s
            ''', (username, dob, phone_number, email, session['email']))
            
            mysql.connection.commit()
            session['username'] = username
            session['email'] = email
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('customer'))
            
        except Exception as e:
            flash('An error occurred while updating your profile', 'danger')
            return redirect(url_for('update_profile'))
            
        finally:
            cur.close()

@app.route('/delete_account', methods=['GET', 'POST'])
def delete_account():
    if not session.get('loggedin'):
        flash('Please login to delete your account', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        
        # Verify password before deletion
        cur = mysql.connection.cursor(cursorclass=DictCursor)
        try:
            cur.execute('SELECT * FROM customers WHERE email = %s AND password = %s', 
                       (session['email'], password))
            user = cur.fetchone()
            
            if not user:
                flash('Invalid password. Account deletion failed.', 'danger')
                return redirect(url_for('customer'))
            
            # Delete the account
            cur.execute('DELETE FROM customers WHERE email = %s', (session['email'],))
            mysql.connection.commit()
            
            # Clear session and redirect to home
            session.clear()
            flash('Your account has been successfully deleted.', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash('An error occurred while deleting your account.', 'danger')
            return redirect(url_for('customer'))
            
        finally:
            cur.close()
    
    return render_template('delete_account.html')


    if not session.get('loggedin'):
        flash('Please login to transfer amount', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        recipient_account = request.form.get('recipient_account')
        amount = request.form.get('amount')
        
        # Validate inputs
        if not all([recipient_account, amount]):
            flash('Please fill in all fields', 'danger')
            return render_template('transfer_amount.html')
        
        try:
            amount = float(amount)
            if amount <= 0:
                flash('Amount must be positive', 'danger')
                return render_template('transfer_amount.html')
        except ValueError:
            flash('Invalid amount format', 'danger')
            return render_template('transfer_amount.html')
        
        cur = mysql.connection.cursor(cursorclass=DictCursor)
        try:
            # Check if recipient exists
            cur.execute('SELECT * FROM customers WHERE account_number = %s', 
                       (recipient_account,))
            recipient = cur.fetchone()
            
            if not recipient:
                flash('Recipient account not found', 'danger')
                return render_template('transfer_amount.html')
            
            # Here you would typically check the sender's balance and perform the transfer
            # For simplicity, we will skip those steps
            
            flash(f'Successfully transferred {amount} to account {recipient_account}', 'success')
            return redirect(url_for('customer'))
            
        except Exception as e:
            flash('An error occurred during the transfer', 'danger')
            return render_template('transfer_amount.html')
            
        finally:
            cur.close()
    
    return render_template('transfer_amount.html')



@app.route('/logout')
def logout():
    # Clear all session data
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))


if __name__=="__main__":
    app.run(debug = True)