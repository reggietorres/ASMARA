#Standard Lib
#import random
import os
from functools import wraps
from datetime import datetime
import socket


#Third Party
from pyotp import TOTP
from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory, flash, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import desc, func
from OpenSSL import crypto


def load_or_generate_secret_key(filename='secret_key.txt'):
    try:
        with open(filename, 'r') as file:
            secret_key = file.read().strip()
            # Check if the file is empty
            if not secret_key:
                raise FileNotFoundError
    except FileNotFoundError:
        # Generate a new 128-character secret key
        secret_key = os.urandom(128).hex()
        with open(filename, 'w') as file:
            file.write(secret_key)
    return secret_key



def check_certificate_expiration(cert_path):
    # Load the certificate
    with open(cert_path, 'rb') as cert_file:
        cert_data = cert_file.read()
    x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)

    # Get the expiration date
    expiration_date = x509.get_notAfter().decode('utf-8')
    expiration_date = datetime.strptime(expiration_date, '%Y%m%d%H%M%SZ')

    # Check if the certificate is about to expire
    now = datetime.utcnow()
    expires_in = expiration_date - now
    if expires_in.days <= 30: # Check if the certificate expires in 30 days or less
        print(f"The certificate is about to expire in {expires_in.days} days.")
        print(f"The certificate is about to expire in {expires_in.days} days.")
        print(f"The certificate is about to expire in {expires_in.days} days.")
        print(f"The certificate is about to expire in {expires_in.days} days.")
        print(f"The certificate is about to expire in {expires_in.days} days.")
    else:
        print("The certificate is not about to expire.")
        print("The certificate is not about to expire.")
        print("The certificate is not about to expire.")
        print("The certificate is not about to expire.")
        print("The certificate is not about to expire.")




#Define Flask and Configuration
app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/asmara' #Change this!
db = SQLAlchemy(app)
#app.config['MAX_CONTENT_LENGTH'] = 104857600 THIS IS FOR DEBUGGING PURPOSES, NOT YET USED..

# Load or generate the secret key
app.secret_key = load_or_generate_secret_key()

global password
password = "secret_password"

API_PREFIX = '/apiv1'


if app.secret_key == 'your_secret_key':
    new_secret_key = os.urandom(128)
    print(new_secret_key)


class Request(db.Model):
    __tablename__ = "request"

    reindex = db.Column(db.Integer, primary_key=True, autoincrement=True)
    response_time = db.Column(db.Float)
    date = db.Column(db.DateTime)
    method = db.Column(db.String)
    size = db.Column(db.Integer)
    status_code = db.Column(db.Integer)
    path = db.Column(db.String)
    user_agent = db.Column(db.String)
    remote_address = db.Column(db.String)
    exception = db.Column(db.String)
    referrer = db.Column(db.String)
    browser = db.Column(db.String)
    platform = db.Column(db.String)
    mimetype = db.Column(db.String)

#Make Database Model
class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(128))
    secret = db.Column(db.String(100)) # New column for the OTP secret key
    sudo = db.Column(db.Boolean, default=False) # Boolean field for sudo privileges


#Define the @ you put infront of a route if login is required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function




@app.route('/assets/<path:filename>')
def serve_public_file(filename):
    return send_from_directory('assets', filename)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('assets', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

#index.html route
@app.route('/')
@login_required
def home():
    username = request.cookies.get('username')
    return render_template('index.html', username=username)

#encode.html route
@app.route('/encode')
@login_required
def encode():
    username = request.cookies.get('username')
    return render_template('encode.html', username=username)



#login.html route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        hashed_password = request.form.get('password')
        user = users.query.filter_by(username=username).first()
        if user and user.password == hashed_password:
            # Redirect to OTP verification page
            response = make_response(redirect(url_for('verify_code')))
            response.set_cookie('username', username)
            return response
        else:
            flash('401 Invalid credentials')
            return redirect(url_for('login'))
    else:
        return render_template('login.html')
    
#extend session route, for when you go AFK on index.html
@app.route('/extend_session', methods=['POST'])
def extend_session():
    return '', 204
    
#2FA Route
@app.route('/verify_code', methods=['GET', 'POST'])
def verify_code():
    if request.method == 'POST':
        username = request.cookies.get('username')
        user_totp_code = request.form.get('code')
        user = users.query.filter_by(username=username).first()
        
        if user:
            totp = TOTP(user.secret)
            if totp.verify(user_totp_code):
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('home'))
            else:
                flash('Invalid OTP code')
                return redirect(url_for('verify_code', username=username))
        else:
            flash('User not found')
            return redirect(url_for('login'))
    else:
        return render_template('verify_code.html')
    


#Logout Route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('sudo_mode', None)
    return redirect(url_for('login'))

class Alert:
    def getJJJHHMM():
        return datetime.utcnow().strftime("%j%H%M")

@login_required
@app.route(API_PREFIX + '/alert/send', methods=['POST'])
def send_alert():
    if request.method == 'POST':
        data = request.get_json()
        alert_type = data.get('type')
        alert_org = data.get('org')
        alert_exp = data.get('dur')
        alert_areas = data.get('areas')
        alert_station = data.get('station')
        alert_jjjhhmm = Alert.getJJJHHMM()

        print(data)

        # Validate the data and call the appropriate function to send the alert
        if not all([alert_type, alert_org, alert_exp, alert_areas, alert_station]):
            return jsonify({'error': 'Missing required fields'}),  400

        # If for some bullshit reason, Alert.getJJJHHMM fails, then return 412 Precondition Failed
        if not alert_jjjhhmm:
            return jsonify({'error': 'Precondition Failed'}), 412

        # Call the function to send the alert (this is a placeholder)
        result = send_alert_function(alert_type, alert_org, alert_exp, alert_areas,alert_jjjhhmm, alert_station)

        if result:
            return jsonify({'message': 'Alert sent successfully'}),  201
        else:
            return jsonify({'error': 'Failed to send alert'}),  500
def send_alert_function(type,org,exp,areas,JJJHHMM,station):
    msg = f"sendAlert {org} {type} {areas} {exp} {JJJHHMM} {station}"
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = "127.0.0.1"
    server_port =  6765
    client.connect((server_ip, server_port))

    # Receive and decode the initial password request message
    response = client.recv(1024)
    response = response.decode("utf-8")

    # Send the password
    client.send(password.encode("utf-8"))

    # Receive and decode the authentication confirmation message
    response = client.recv(1024)
    response = response.decode("utf-8")

    # Send the sendAlert message only once
    client.send(msg.encode("utf-8"))

    # Receive and decode the server's response
    response = client.recv(1024)
    response = response.decode("utf-8")

    client.close()

    if response == "Failed to Send Alert":
        return False
    elif response == "Sent!":
        return True
    else:
        return False

if __name__ == '__main__':
    key_file = "ssl_key.key"
    cert_file = "ssl_cert.pem"
    cert_dir = "."

    # Check if the key and certificate files exist
    if not os.path.exists(os.path.join(cert_dir, key_file)) or not os.path.exists(os.path.join(cert_dir, cert_file)):
        print("WARNING: Server Is Not Running in HTTPS/SSL Mode! This is very insecure and could expose your credentials to packetsniffers on your network!")
        app.run(debug=True)
    else:
        check_certificate_expiration(cert_file)
        app.run(debug=True, ssl_context=(cert_file,key_file))
