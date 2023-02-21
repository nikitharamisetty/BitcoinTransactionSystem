# NIKITHA RAMISETTY                         nxr210008
# KANAKARATNA KALYAN KUMAR SINGAMSETTY      kxs200019
# SAAKSHARA KANYADARA                       sxk210041
# SRAVANI PEDDAGORLA                        sxp200188
from flask import Flask
from flask import render_template, redirect, url_for,request,session
import mysql.connector as sql
import urllib.request
import json
import datetime

    
app = Flask(__name__,template_folder="/Users/nkitharamisetty/Documents/Database_Project/app/templates")
app.secret_key = 'super secret key'
@app.route('/login.html',methods=['GET', 'POST'])
def login():
    msg = ''
    print('outside loop')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['acc_password']

        mydb = sql.connect(
            host = "localhost",
            user = "root",
            password = "4c68pyqg"
        )
        mycursor = mydb.cursor()
        mycursor.execute("Use BTSDatabase")
  
        mycursor.execute('SELECT * FROM client WHERE username = %s AND acc_password = %s', (username, password,))
        account = mycursor.fetchone()
        session['account_details']=account
        if account:
            if account[11]=='Client':
                return render_template('client_home.html')
            if account[11]=='Trader':
                return redirect('traderhome')
            if account[11]=='Manager':
                return redirect("/manager-home")

        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
            print('Incorrect username/password!')
    #print(msg, file=sys.stderr)
    print('msg: ' + msg)
    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)

@app.route('/payments',methods=['GET', 'POST'])
def payments():
    msg = ''
    #print('outside loop')
    if request.method == 'POST':

        clientID = session['account_details'][0]
        fiat_balance = session['account_details'][10]
        amount = float(request.form['amount'])
        print(fiat_balance)
        print(amount)

        mydb = sql.connect(
            host = "localhost",
            user = "root",
            password = "4c68pyqg"
        )
        mycursor = mydb.cursor()
        mycursor.execute("Use BTSDatabase")
        # fiat_balance = fiat_balance+amount
        # print(fiat_balance)

        # update_qry = 'UPDATE CLIENT SET fiat_balance = %s WHERE client_id = %s'
        # mycursor.execute(update_qry,(fiat_balance,clientID,))
        # msg="Transaction Successful!!"
        # mydb.commit()
        # qr = 'SELECT * FROM CLIENT WHERE client_id = %s'
        # mycursor.execute(qr,(clientID,))
        # account = mycursor.fetchone()
        # session['account_details']=account
        # Inserting into the payments table below
        row_qr = "SELECT COUNT(*) FROM PAYMENTS"
        mycursor.execute(row_qr)
        count = mycursor.fetchone()[0] + 1
        print(count)
        qr_payment = "Insert Into payments(payment_id, client_id, trader_id, payment_status, payment_amount, timestamp) Values (%s, %s, %s, %s, %s, %s)"
        status = 'pending'
        mycursor.execute(qr_payment,(count,clientID,100000012,status,amount,datetime.datetime.now(),))
        mydb.commit()
        return render_template('client_home.html')

    return render_template('client_payments.html', msg=msg)

@app.route('/order_transaction',methods=['GET', 'POST'])
def order():

    if request.method=="POST":
        mydb = sql.connect(
            host = "localhost",
            user = "root",
            password = "4c68pyqg"
        )
        mycursor = mydb.cursor()
        mycursor.execute("Use BTSDatabase")
        trans_type = request.form['trans_type']
        value = float(request.form['value'])
        comm_type = request.form['comm_type']
        qry_comm_value = 0
        print(trans_type)
        print(value)
        print(comm_type)


        url = urllib.request.urlopen("https://api.coindesk.com/v1/bpi/currentprice.json")
        data = json.load(url)
        current_btc_rate = float(data['bpi']['USD']['rate_float'])
        print(current_btc_rate)

        if trans_type=="Buy":
            clientID = session['account_details'][0]
            fiat_balance = session['account_details'][10]
            bitcoin_balance = session['account_details'][9]
            exc_value = value*current_btc_rate
            if exc_value<=fiat_balance:
                fiat_balance= fiat_balance-exc_value
                bitcoin_balance = bitcoin_balance+value
                update_qry = 'UPDATE CLIENT SET fiat_balance = %s WHERE client_id = %s'
                btc_update_qry = 'UPDATE CLIENT SET bitcoin_balance = %s WHERE client_id = %s'
                mycursor.execute(update_qry,(fiat_balance,clientID,))
                mycursor.execute(btc_update_qry,(bitcoin_balance,clientID,))
                msg="Transaction Successful!!"
                mydb.commit()
                qr = 'SELECT * FROM CLIENT WHERE client_id = %s'
                mycursor.execute(qr,(clientID,))
                account = mycursor.fetchone()
                session['account_details']=account

        if trans_type=="Sell":
            clientID = session['account_details'][0]
            fiat_balance = session['account_details'][10]
            bitcoin_balance = session['account_details'][9]
            account_status = session['account_details'][6]
            #exc_value = value*current_btc_rate
            if account_status=="Gold":
                if value<bitcoin_balance:
                #fiat_balance= fiat_balance+exc_value
                #bitcoin_balance = bitcoin_balance-value
                    comm_rate = 0.05
                    if comm_type== "Bitcoin":
                        comm_value = comm_rate*value
                        qry_comm_value = comm_value
                        value = value+comm_value
                        bitcoin_balance = bitcoin_balance-value
                        fiat_balance = fiat_balance+(current_btc_rate*value)
                    else:
                        comm_value = comm_rate*value
                        fiat_comm_value = comm_value*current_btc_rate
                        qry_comm_value = comm_value
                        if fiat_comm_value<=fiat_balance:
                            fiat_balance=fiat_balance-fiat_comm_value
                            bitcoin_balance = bitcoin_balance-value
                            fiat_balance = fiat_balance + (value*current_btc_rate)
                        else:
                            msg = 'Could not sell because of insufficient fiat balance'
                            return render_template('order_transaction.html',msg=msg)
            else:
                if value<bitcoin_balance:
                    comm_rate = 0.07
                    if comm_type== "Bitcoin":
                        comm_value = comm_rate*value
                        qry_comm_value = comm_value
                        value = value-comm_value
                        bitcoin_balance = bitcoin_balance-value
                        fiat_balance = fiat_balance+(current_btc_rate*value)
                    else:
                        comm_value = comm_rate*value
                        fiat_comm_value = comm_value*current_btc_rate
                        qry_comm_value = comm_value
                        if fiat_comm_value<=fiat_balance:
                            fiat_balance=fiat_balance-fiat_comm_value
                            bitcoin_balance = bitcoin_balance-value
                            fiat_balance = fiat_balance + (value*current_btc_rate)
                        else:
                            msg = 'Could not sell because of insufficient fiat balance'
                            return render_template('order_transaction.html',msg=msg)
                
                    update_qry = 'UPDATE CLIENT SET fiat_balance = %s WHERE client_id = %s'
                    btc_update_qry = 'UPDATE CLIENT SET bitcoin_balance = %s WHERE client_id = %s'
                    mycursor.execute(update_qry,(fiat_balance,clientID,))
                    mycursor.execute(btc_update_qry,(bitcoin_balance,clientID,))


                    mydb.commit()
                    qr = 'SELECT * FROM CLIENT WHERE client_id = %s'
                    mycursor.execute(qr,(clientID,))
                    account = mycursor.fetchone()
                    session['account_details']=account

        #Insert into OrderTransaction table
        row_qr = "SELECT COUNT(*) FROM ORDER_TRANSACTION"
        mycursor.execute(row_qr)
        count = mycursor.fetchone()[0] + 1
        #print(count)
        qr_payment = "Insert Into order_transaction(trans_id, trans_type, trans_value, comm_type, comm_amount, client_id, trader_id, timestamp) Values (%s, %s, %s, %s, %s, %s, %s, %s)"
        mycursor.execute(qr_payment, (count, trans_type, value, comm_type, qry_comm_value, session['account_details'][0], 100000012, datetime.datetime.now(),))
        mydb.commit()
        # Insert into OrderTransaction table
        return render_template("client_home.html")
    return render_template("order_transaction.html")

@app.route('/manager-home',methods=['GET', 'POST'])
def managerhome():
    msg = 'oops! Something went wrong!'
    if request.method == "POST":
        start = request.form['start']
        end = request.form['end']
        print(start)
        print(end)

        mydb = sql.connect(
            host="localhost",
            user="root",
            password="4c68pyqg"
        )
        mycursor = mydb.cursor()
        mycursor.execute("Use BTSDatabase")

        details_query = "SELECT * FROM order_transaction WHERE cast(timestamp as date) between %s AND %s"
        mycursor.execute(details_query,(start,end))
        transactions = mycursor.fetchall()

        pay_query = "SELECT * FROM payments WHERE cast(timestamp as date) between %s AND %s"
        mycursor.execute(pay_query,(start,end))
        payment = mycursor.fetchall()
       

        return render_template("manager_home.html",r=transactions,p=payment)
    return render_template('manager_home_new.html',msg=msg)
@app.route('/traderhome',methods=['GET', 'POST'])
def traderhome():
    msg = 'oops! Something went wrong!'
    if request.method == "POST":
        username = request.form['search']
        print(username)
        mydb = sql.connect(
            host="localhost",
            user="root",
            password="4c68pyqg"
        )
        mycursor = mydb.cursor()
        mycursor.execute("Use BTSDatabase")

        query = "SELECT * FROM client WHERE username = %s "
        mycursor.execute(query,(username,))
        search_results = mycursor.fetchall()
        print(search_results)

        return render_template("trader_search_results.html",s=search_results[0])
    return render_template('trader_home.html')


#This portion is for pendingpayments and page to accept payments

@app.route('/Pending-Payments', methods=['GET', 'POST'])
def pendingPayments_list():
    # pendingOrders = Order.query.filter_by(status='pending').order_by(desc(Order.timestamp))
    # if pendingOrders.count() == 0:
    #     pendingOrders= None
    mydb = sql.connect(
        host="localhost",
        user="root",
        password="4c68pyqg"
    )
    mycursor = mydb.cursor()
    mycursor.execute("Use BTSDatabase")
    fetchpending_qry = "SELECT * FROM PAYMENTS WHERE payment_status = 'pending' "
    mycursor.execute(fetchpending_qry)
    pendingDepostits = mycursor.fetchall()
    return render_template('/pendingPayments.html', title="Pending orders", pendingDeposits=pendingDepostits)

#This is for Accepting/cancelling payments
@app.route('/TraderAction_Deposit/<string:action>/<int:pid>', methods=['GET', 'POST'])
def traderAction_deposit(action, pid):
    mydb = sql.connect(
        host="localhost",
        user="root",
        password="4c68pyqg"
    )
    mycursor = mydb.cursor()
    mycursor.execute("Use BTSDatabase")
    qry = "SELECT * FROM PAYMENTS WHERE payment_id = %s"
    mycursor.execute(qry,(pid,))
    payment = mycursor.fetchone()

    if action == 'Approve':
        clientID = payment[1]
        amount = payment[4]
        fetchclient_qry = "SELECT * FROM CLIENT WHERE client_id = %s"
        mycursor.execute(fetchclient_qry,(clientID,))
        client_details = mycursor.fetchone()
        fiat_balance = client_details[10] + float(amount)
        print(fiat_balance)

        update_qry = 'UPDATE CLIENT SET fiat_balance = %s WHERE client_id = %s'
        mycursor.execute(update_qry, (fiat_balance, clientID,))

        update_qry = "UPDATE PAYMENTS SET payment_status = 'Approved', trader_id = %s WHERE payment_id = %s"
        mycursor.execute(update_qry, (session['account_details'][0],pid,))
        mydb.commit()
        # payment.status = 'approved'
        # client = User.query.get_or_404(payment.clientId)
        # client.fiat_balance += payment.fiatAmount
        # flashMessage = 'You have approved the deposit ID:' + str(xid)
    elif action == 'Cancel':
        update_qry = "UPDATE PAYMENTS SET payment_status = 'Cancelled' WHERE payment_id = %s"
        mycursor.execute(update_qry, (session['account_details'][0],pid,))
        mydb.commit()
        # payment.status = 'cancelled'
        # flashMessage = 'You have cancelled the deposit ID:' + str(xid)
        # Just checking

    return redirect(url_for('pendingPayments_list'))



@app.route('/')
def welcome():
     return render_template('welcome.html') 
@app.route('/welcome.html')
def welcomehome():
    return render_template('welcome.html') 
@app.route('/client-home')
def home():
    return render_template("client_home.html")

@app.route('/account-details')
def acount_details():
    account = session['account_details']
    return render_template("client_home_account.html",r=account)

if __name__ == '__main__':
    app.debug = True
    app.run()






