from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import mysql.connector
from openpyxl import load_workbook
import pandas as pd
import re



app = Flask(__name__)
app.config['DEBUG'] = True
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1604008saifulcse88",
    database="newdb"
)

mycursor = mydb.cursor()
@app.route('/')


def index():
    summary = None
    return render_template('index.html', summary = summary)


@app.route('/', methods=['POST'])

def uploadFiles():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        file_extension = os.path.splitext(uploaded_file.filename)[1]

        if file_extension == '.xlsx' or file_extension == '.xls':
            file_path = os.path.join(app.config['UPLOAD_FOLDER'],uploaded_file.filename)
            uploaded_file.save(file_path)
            summary = parseXLSX(file_path)
            summary_dict = {'total_data': summary[0],
                            'total_successfully_uploaded_data': summary[1],
                            'total_duplicate_data': summary[2],
                            'total_invalid_data': summary[3],
                            'total_incomplete_data': summary[4]}
            return render_template('index.html', summary=summary_dict)
        
        else:
            message = "Unsupported File Format, Use Excel File Format Please.."
            return render_template('index.html', message=message)
        
    return redirect(url_for("index"))



phone_regex = re.compile(r'^(?:\+8801)?(3|4|5|6|7|8|9)\d{8}$')
email_regex = re.compile(r'^[a-z]+@[a-z]+\.[a-z]+$')



def validate_BD_phone_number(phone_number):
    return bool(phone_regex.match(phone_number))

def validate_email(email):
    return bool(email_regex.match(email))



def parseXLSX(filePath):
    col_names = ['Name', 'Gmail', 'PhoneNumber', 'Gender', 'Address']
    xlsxData = pd.read_excel(filePath, names=col_names, header = None, skiprows=1)

    total_data = len(xlsxData)
    total_successfully_uploaded_data = 0
    total_duplicate_data = 0
    total_invalid_data = 0
    total_incomplete_data = 0

    for i,row in xlsxData.iterrows():
        if pd.isna(row['PhoneNumber']):
            phone_number = None
        else:
            phone_number = '+880' + str(int(row['PhoneNumber']))
            if not validate_BD_phone_number(phone_number):
                total_invalid_data += 1
                continue

        email = row['Gmail']
        if not validate_email(email):
            total_invalid_data += 1
            continue
        
        sql = "SELECT * FROM new_table WHERE PhoneNumber=%s OR Gmail=%s"
        value = (phone_number, email)
        mycursor.execute(sql, value)
        result = mycursor.fetchone()

        if result:
            total_duplicate_data += 1
        else:
            if any(pd.isna(row[col]) for col in col_names):
                total_incomplete_data += 1
            else:
                sql = "INSERT INTO new_table (Name, Gmail, PhoneNumber, Gender, Address) VALUES (%s, %s, %s, %s, %s)"
                value = (row['Name'], email, phone_number, row['Gender'], row['Address'])
                mycursor.execute(sql,value)
                mydb.commit()
                total_successfully_uploaded_data += 1

    return total_data, total_successfully_uploaded_data, total_duplicate_data, total_invalid_data, total_incomplete_data


@app.route('/showData')
def showData():
    mycursor.execute("SELECT * FROM new_table")
    data = mycursor.fetchall()
    return render_template('data.html', data=data)



@app.route('/showData', methods=['GET', 'POST'])
def searchData():
    text = request.form.get("text")
    print(text)
    mycursor= mydb.cursor()
    mycursor.execute("SELECT * FROM new_table WHERE Name LIKE '{}%' ".format(text))
    results = mycursor.fetchall()
    print(results)
    mycursor.close()
    # mydb.close()

    return jsonify(results)





if __name__ == "__main__":
    app.run(port=5000)