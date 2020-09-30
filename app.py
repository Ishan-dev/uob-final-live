import random
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import pickle
from flask import Flask, request, render_template, jsonify, make_response, redirect, url_for, session, logging
from functions_only_save import make_face_df_save, find_face_shape
from recommender import process_rec_pics, run_recommender_face_shape
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
import MySQLdb.cursors
import re
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__, static_url_path="")
app.secret_key = 'admin123'

df = pd.DataFrame(
    columns=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17',
             '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29',
             '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41',
             '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53',
             '54', '55', '56', '57', '58', '59', '60', '61', '62', '63', '64', '65',
             '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77',
             '78', '79', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89',
             '90', '91', '92', '93', '94', '95', '96', '97', '98', '99', '100', '101',
             '102', '103', '104', '105', '106', '107', '108', '109', '110', '111', '112', '113',
             '114', '115', '116', '117', '118', '119', '120', '121', '122', '123', '124', '125',
             '126', '127', '128', '129', '130', '131', '132', '133', '134', '135', '136', '137',
             '138', '139', '140', '141', '142', '143', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9',
             'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16', 'Width', 'Height', 'H_W_Ratio', 'Jaw_width', 'J_F_Ratio',
             'MJ_width', 'MJ_J_width'])


@app.route('/')
def index():
    """Return the main page."""
    return render_template('index.html')


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345'
app.config['MYSQL_DB'] = 'appointment'

mysql = MySQL(app)


@app.route('/appointment', methods=['POST', 'GET'])
def appo():
    if request.method == "POST":
        userDetails = request.form
        name = userDetails['Name']
        email = userDetails['email']
        number = userDetails['Number']
        Date = userDetails['Date']
        Time = userDetails['Time']
        service = userDetails['service']
        stylist = userDetails['stylist']
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO appo(name, email, number, Date, Time, Service, Stylist) VALUES(%s, %s, %s, %s, %s, %s, %s)",
            (name, email, number, Date, Time, service, stylist))
        mysql.connection.commit()
        cur.close()

    return render_template('appointment.html')


@app.route('/algo')
def algo():
    return render_template("algo.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/services')
def services():
    return render_template("services.html")


@app.route('/gallery')
def gallery():
    return render_template("gallery.html")


@app.route('/contact')
def contact():
    return render_template("contact.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('table'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)


@app.route('/table', methods=['POST', 'GET'])
def table():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("SELECT * FROM appo")
    if resultValue > 0:
        userDetails = cur.fetchall()
    else:
        return redirect(url_for('appointment'))
    return render_template('table.html', userDetails=userDetails)


@app.route('/table/delete/<string:id_data>', methods=['GET', 'POST'])
def delete(id_data):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM appo WHERE id=%s", id_data)
    mysql.connection.commit()
    return redirect(url_for('table'))


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    """Return a random prediction."""
    data = request.json
    test_photo = 'data/pics/recommendation_pics/' + data['file_name']
    file_num = 2035
    style_df = pd.DataFrame()
    style_df = pd.DataFrame(columns=['face_shape', 'hair_length', 'location', 'filename', 'score'])
    hair_length_input = 'Updo'
    updo_input = data['person_see_up_dos']
    if updo_input in ['n', 'no', 'N', 'No', 'NO']:
        hair_length_input = data['person_hair_length']
        if hair_length_input in ['short', 'Short', 's', 'S']:
            hair_length_input = 'Short'
        if hair_length_input in ['long', 'longer', 'l', 'L']:
            hair_length_input = 'Long'

    make_face_df_save(test_photo, file_num, df)
    face_shape = find_face_shape(df, file_num)
    process_rec_pics(style_df)
    img_filename = run_recommender_face_shape(face_shape[0], style_df, hair_length_input)
    return jsonify({'Face Shape': face_shape[0], 'img_filename': img_filename})


@app.route('/predict_user_face_shape', methods=['GET', 'POST'])
def predict_user_face_shape():
    """Return a user face shape."""
    data = request.json
    test_photo = 'data/pics/recommendation_pics/' + data['file_name']
    file_num = 2035

    make_face_df_save(test_photo, file_num, df)
    face_shape = find_face_shape(df, file_num)
    return jsonify({'face_shape': face_shape[0]})


@app.route('/output/<img_filename>')
def output_image(img_filename):
    """Send the output image."""
    with open(f"output/{img_filename}", 'rb') as f:
        img_data = f.read()
    response = make_response(img_data)
    response.headers['Content-Type'] = 'image/png'
    return response


if __name__ == '__main__':
    app.debug = True
    app.run()
