from flask import render_template, Flask, request, jsonify
import hashlib # for hashing of password to store in database
import pandas as pd

app = Flask(__name__)

# A route for home page display
@app.route('/')
def Home():
    return render_template('Home.html')

# A route for registration page display
@app.route('/registration')
def Registration():
    return render_template('Registration.html')

# A route for About us page display
@app.route('/about')
def About():
    return render_template('AboutUs.html')

# A route for FD calculator page display
@app.route('/fd')
def FD():
    return render_template('FD-calculator.html')

# A route for loan calculator page display
@app.route('/loan')
def Loan():
    return render_template('Loan-Calculator.html')

# A route for FAQ page display
@app.route('/faq')
def Faq():
    return render_template('FAQ.html')

# a route to submit account registration
@app.route('/registration/submit', methods=['POST'])
def submitRegistrationForm():
    # Extract form data
    name = request.form.get('name')
    mobile = request.form.get('mobile')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    # Encode the mobile and password for hashing
    mobile_encoding = str(mobile).encode()
    password_encoding = str(password).encode()

    # Hash the mobile and password
    hashed_mobile = hashlib.sha256(mobile_encoding).hexdigest()
    hashed_password = hashlib.sha256(password_encoding).hexdigest()

    # Read the existing data from the CSV file
    df = pd.read_csv('Customers.csv')

    # Generate a new account number (increment from the last account number)
    if df.empty:
        new_account_no = 1
    else:
        new_account_no = df['accountNo'].max() + 1

    # Create a new entry as a dictionary
    new_entry = {
        'accountNo': new_account_no,
        'name': name,
        'mobile': mobile,
        'hashed_mobile': hashed_mobile,
        'password': password,
        'hashed_password': hashed_password,
        'balance': 0.0,  # Initial balance is set to zero
        'active': True   # Set account status as active by default
    }

    # Append the new entry to the DataFrame
    df = df._append(new_entry, ignore_index=True)

    # Save the updated DataFrame back to the CSV
    df.to_csv('Customers.csv', index=False)

    return render_template('Home.html')
    
# a route to login form
@app.route('/login',methods=['GET'])
def loginForm():
    return render_template('LoginForm.html')

# a route to submit the login form
@app.route('/login/submit', methods=['POST'])
def submitLoginForm():
    # Extract form data
    mobile = request.json.get('mobile')
    password = request.json.get('password')

    # Encode the mobile and password for hashing
    mobile_encoding = str(mobile).encode()
    password_encoding = str(password).encode()

    # Hash the mobile and password
    hashed_mobile = hashlib.sha256(mobile_encoding).hexdigest()
    hashed_password = hashlib.sha256(password_encoding).hexdigest()

    # Read the existing data from the CSV file
    df = pd.read_csv('Customers.csv')

    # Retrieve the user data with the matching hashed_mobile
    user_data = df[df['hashed_mobile'] == hashed_mobile]

    # Print out the values for debugging
    print(f"Input Mobile: {mobile}")
    print(f"Input Hashed Mobile: {hashed_mobile}")
    print(f"Input Password: {password}")
    print(f"Input Hashed Password: {hashed_password}")
    print(f"User data found: {user_data}")

    # Check if user exists and the hashed passwords match
    if not user_data.empty and user_data.iloc[0]['hashed_password'] == hashed_password:
        return {"status": "success", "accountNo": int(user_data.iloc[0]['accountNo']),"Name":str(user_data.iloc[0]['name'])}
    else:
        return {"status": "error", "message": "Incorrect mobile or password"}

# a route for dashboard for logged in users
@app.route('/dashboard')
def Dashboard():
    return render_template('Dashboard.html')

# a route to get balance of account
@app.route('/get-balance', methods=['POST'])
def get_balance():
    data = request.get_json()
    account_no = data.get('accountNo')

    # Load customer data from CSV
    df = pd.read_csv('Customers.csv')

    # Search for the account number in the DataFrame
    customer = df[df['accountNo'] == int(account_no)]

    if not customer.empty:
        # Extract the balance for the matched account
        balance = customer.iloc[0]['balance']
        return jsonify({
            "success": True,
            "balance": balance
        })
    else:
        return jsonify({
            "success": False,
            "message": "Account number not found."
        }), 404

# Define the route to handle deposit requests
@app.route('/deposit', methods=['POST'])
def deposit():
    try:
        # Get the JSON data from the request
        data = request.get_json()
        account_no = data.get('accountNo')
        deposit_amount = data.get('amount')

        # Load the customer data from the CSV file
        customers_df = pd.read_csv('Customers.csv')

        # Find the row corresponding to the account number
        customer = customers_df[customers_df['accountNo'] == int(account_no)]

        if customer.empty:
            return jsonify({'status': 'error', 'message': 'Account not found'}), 404

        # Update the balance
        current_balance = customer.iloc[0]['balance']
        new_balance = current_balance + deposit_amount

        # Update the dataframe
        customers_df.loc[customers_df['accountNo'] == int(account_no), 'balance'] = new_balance

        # Save the updated dataframe back to the CSV
        customers_df.to_csv('Customers.csv', index=False)

        # Respond with the new balance
        return jsonify({'status': 'success', 'newBalance': new_balance})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Define the route to handle transfer requests
@app.route('/transfer', methods=['POST'])
def transfer():
    try:
        # Get the JSON data from the request
        data = request.get_json()
        sender_account_no = data.get('senderAccountNo')
        recipient_account_no = data.get('recipientAccountNo')
        transfer_amount = data.get('amount')

        # Load the customer data from the CSV file
        customers_df = pd.read_csv('Customers.csv')

        # Find the rows for the sender and recipient accounts
        sender = customers_df[customers_df['accountNo'] == int(sender_account_no)]
        recipient = customers_df[customers_df['accountNo'] == int(recipient_account_no)]

        # Check if the sender or recipient accounts are invalid
        if sender.empty:
            return jsonify({'status': 'error', 'message': 'Sender account not found'}), 404
        if recipient.empty:
            return jsonify({'status': 'error', 'message': 'Recipient account not found'}), 404

        # Check if the sender has enough balance
        sender_balance = sender.iloc[0]['balance']
        if sender_balance < transfer_amount:
            return jsonify({'status': 'error', 'message': 'Insufficient balance'}), 400

        # Update balances
        new_sender_balance = sender_balance - transfer_amount
        recipient_balance = recipient.iloc[0]['balance'] + transfer_amount

        # Update the dataframe with the new balances
        customers_df.loc[customers_df['accountNo'] == int(sender_account_no), 'balance'] = new_sender_balance
        customers_df.loc[customers_df['accountNo'] == int(recipient_account_no), 'balance'] = recipient_balance

        # Save the updated dataframe back to the CSV
        customers_df.to_csv('Customers.csv', index=False)

        # Respond with the new balance of the sender
        return jsonify({'status': 'success', 'newBalance': new_sender_balance})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
# Define the route to handle withdrawal requests
@app.route('/withdraw', methods=['POST'])
def withdraw():
    try:
        # Get the JSON data from the request
        data = request.get_json()
        account_no = data.get('accountNo')
        withdrawal_amount = data.get('amount')

        # Load the customer data from the CSV file
        customers_df = pd.read_csv('Customers.csv')

        # Find the row for the account
        customer = customers_df[customers_df['accountNo'] == int(account_no)]

        # Check if the account exists
        if customer.empty:
            return jsonify({'status': 'error', 'message': 'Account not found'}), 404

        # Get the current balance of the customer
        current_balance = customer.iloc[0]['balance']

        # Check if the customer has enough balance
        if current_balance < withdrawal_amount:
            return jsonify({'status': 'error', 'message': 'Insufficient balance'}), 400

        # Update the balance
        new_balance = current_balance - withdrawal_amount
        customers_df.loc[customers_df['accountNo'] == int(account_no), 'balance'] = new_balance

        # Save the updated dataframe back to the CSV
        customers_df.to_csv('Customers.csv', index=False)

        # Respond with the new balance
        return jsonify({'status': 'success', 'newBalance': new_balance})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/update-password', methods=['POST'])
def update_password():
    try:
        # Get the JSON data from the request
        data = request.get_json()
        account_no = data.get('accountNo')
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')

        # Hash the current password for comparison
        hashed_current_password = hashlib.sha256(current_password.encode()).hexdigest()

        # Load the customer data from the CSV file
        customers_df = pd.read_csv('Customers.csv')

        # Find the row for the account
        customer = customers_df[customers_df['accountNo'] == int(account_no)]

        # Check if the account exists
        if customer.empty:
            return jsonify({'status': 'error', 'message': 'Account not found'}), 404

        # Get the stored hashed password
        stored_hashed_password = customer.iloc[0]['hashed_password']

        # Check if the current password is correct
        if stored_hashed_password != hashed_current_password:
            return jsonify({'status': 'error', 'message': 'Current password is incorrect'}), 400

        # Hash the new password and update it
        hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()
        customers_df.loc[customers_df['accountNo'] == int(account_no), 'hashed_password'] = hashed_new_password
        customers_df.loc[customers_df['accountNo'] == int(account_no), 'password'] = new_password

        # Save the updated dataframe back to the CSV
        customers_df.to_csv('Customers.csv', index=False)

        # Respond with success
        return jsonify({'status': 'success', 'message': 'Password updated successfully'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__=='__main__':
    app.run(debug=True,host='0.0.0.0')