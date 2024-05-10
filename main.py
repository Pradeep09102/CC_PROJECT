import json
import re
import datetime
from datetime import timedelta
from bson import ObjectId
from flask import Flask, render_template, request, session, redirect
import pymongo
import os
import boto3


APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = APP_ROOT + "/static"

myClient = pymongo.MongoClient('mongodb+srv://DB1:DB1@cluster0.o4gp7hf.mongodb.net/test')
mydb = myClient["DB1"]
Booking_col = mydb["Booking"]
Courts_col = mydb["Courts"]
Timeslot_col = mydb["Timeslot"]
Member_col = mydb["Member"]
Schedule_col = mydb['Schedule']
Sports_col = mydb['Sports']
admin_col = mydb['Admin']
Payment_col=mydb['Payment']
app = Flask(__name__)
app.secret_key = "aaaaaa"

##AWS
user_access_key = 'AKIA4JIMZG7UREVPEP4W'
user_secret_key = '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'

sts_client = boto3.client('sts',
                           aws_access_key_id=user_access_key,
                           aws_secret_access_key=user_secret_key)

role_arn = 'arn:aws:iam::844524763113:role/sportz_ec2_user'
response = sts_client.assume_role(RoleArn=role_arn,
                                   RoleSessionName='my-session')
credentials = response['Credentials']

if admin_col.count_documents({}) == 0:
    admin_col.insert_one({"username": "admin", "password": "12345", "role": "admin"})

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/alogin")
def alogin():
    return render_template("alogin.html")


@app.route('/alogin1', methods=['post'])
def alogin1():
    Username = request.form.get("Username")
    Password = request.form.get("Password")
    query ={"username":Username,"password":Password}
    admin = admin_col.find_one(query)
    if admin!=None:
        session['role'] = 'admin'
        return render_template("ahome.html")
    else:
        return render_template("msg.html", msg='Invalid Login Details', color='bg-danger')


@app.route("/ahome")
def ahome():
    return render_template("ahome.html")


@app.route("/customerlogin1", methods=['post'])
def customerlogin1():
    username = request.form.get("username")
    password = request.form.get("password")
    mycol = mydb["Member"]
    myquery = {"username": username, "password": password}
    total_count = mycol.count_documents(myquery)
    if total_count > 0:
        results = mycol.find(myquery)
        for result in results:
            current_date = datetime.date.today().isoformat()
            if result['expiry_date']<=current_date:
                query={'$set':{'membership_status':'Inactive'}}
                mycol.update_one(myquery,query)
                return render_template("payMembership.html",member_id=result)
            if result['membership_status'] == 'Active':
                session['Member_id'] = str(result['_id'])
                session['role'] = 'Member'
                return redirect('/chome')
            else:
                return render_template("payMembership.html",member_id=result)
    else:
        return render_template("msg.html", msg="Invalid login details", color='bg-danger')

@app.route("/chome")
def chome():
    Member_id = session['Member_id']
    query = {"_id": ObjectId(Member_id)}
    Member = Member_col.find_one(query)
    return render_template("chome.html", Member=Member)


@app.route("/customerReg")
def customerReg():
    return render_template("customerReg.html")

@app.route("/customerReg1", methods=['post'])
def customerReg1():
    name = request.form.get("name")
    lname = request.form.get("lname")
    username = request.form.get("username")
    gender = request.form.get("gender")
    password = request.form.get("password")
    mobile_no=request.form.get("mobile_no")
    dob=request.form.get("dob")
    emergency_contact = request.form.get("emergency_contact")
    address = request.form.get("address")
    email = request.form.get("email")
    current_date = datetime.date.today()
    one_year_from_now = current_date + datetime.timedelta(days=365)
    mycol = mydb["Member"]
    total_count = mycol.count_documents({'$or': [{"username": username}]})
    if total_count > 0:
        return render_template("msg.html", msg='Details Already exists', color='bg-danger')
    else:
        query={"name": name,"lname": lname, "username": username, "password": password, 'email':email, 'gender':gender, 'mobile_no':mobile_no,'emergency_contact': emergency_contact,'address':address,'dob':dob, 'start_date':current_date.isoformat(),'expiry_date':one_year_from_now.isoformat(),'membership_status': 'Inactive', 'role':'Member'}
        Member_col.insert_one(query)
        member_id = Member_col.find_one({"username":username},{"_id":1})
        return render_template('paymembership.html',member_id=member_id)

@app.route("/courtReg")
def courtReg():
    Courts = Courts_col.find()
    sports=Sports_col.find()
    return render_template("courtReg.html", Courts=Courts,sports=sports)


@app.route("/courtReg1", methods=['post'])
def courtReg1():
    name = request.form.get("name")
    sport_id = request.form.get("sport_id")
    price = request.form.get("price")
    total_count = Courts_col.count_documents({'$or': [{"name": name}]})
    if total_count > 0:
        return render_template("msg.html", msg='Details Already exists', color='bg-danger')
    else:
        query = {"sport_id": ObjectId(sport_id), "name": name, "price": price+" USD", 'status': 'Inactive'}
        Courts_col.insert_one(query)
        return render_template('msg.html', msg=' Court Registered successfully', color='bg-success')

@app.route("/viewcustomer")
def viewcustomer():
    mycol = mydb["Member"]
    query={}
    customers = mycol.find(query)
    return render_template("viewcustomer.html", customers=customers)

@app.route("/viewsport")
def viewsport():
    mycol = mydb["Sports"]
    query = {}
    sports = mycol.find(query)
    sports = Sports_col.find(query)
    courts = Courts_col.find(query)
    return render_template("viewsport.html", sports=sports, courts=courts)


@app.route("/tstatus1")
def tstatus1():
    court_id = ObjectId(request.args.get("Courts_id"))
    mycol = mydb["Courts"]
    query = {'$set': {"status": 'Inactive'}}
    result = mycol.update_one({'_id': court_id}, query)
    return viewcourt()


@app.route("/tstatus")
def tstatus():
    court_id = ObjectId(request.args.get("Courts_id"))
    mycol = mydb["Courts"]
    query2 = {'$set': {"status": 'Active'}}
    result = mycol.update_one({'_id': court_id}, query2)
    return viewcourt()

@app.route("/checkinstatus1")
def checkinstatus1():
    schedule_id = ObjectId(request.args.get("schedule_id"))
    query = {'$set': {"check-in status": 'Waiting for CheckIn'}}
    result = Schedule_col.update_one({'_id': schedule_id}, query)
    schedule=Schedule_col.find_one({'_id':schedule_id})
    court_id=str(schedule['court_id'])
    return redirect('viewbookings?court_id='+court_id)


@app.route("/checkinstatus")
def checkinstatus():
    schedule_id = ObjectId(request.args.get("schedule_id"))
    query2 = {'$set': {"check-in status": 'Checked IN'}}
    result = Schedule_col.update_one({'_id': schedule_id}, query2)
    schedule=Schedule_col.find_one({'_id':schedule_id})
    court_id=str(schedule['court_id'])
    return redirect('viewbookings?court_id='+court_id)

@app.route("/addsport")
def addsport():
    return render_template("addsport.html")


@app.route("/addsport1", methods=['post'])
def addsport1():
    name = request.form.get("sport_name")
    type = request.form.get("type")
    category = request.form.get("category")
    poster = request.files['poster']
    path = APP_ROOT + "/pictures/" + poster.filename
    poster.save(path)

    total_count = Sports_col.count_documents({"name": name})
    if total_count > 0:
        return render_template("msg.html", msg='Details Already Exists', color='bg-danger')
    else:
        query = {"name": name, "type": type, "category": category, "poster": poster.filename}
        Sports_col.insert_one(query)
        return render_template('msg.html', msg='Sport Added  successfully', color='bg-success')


@app.route("/viewcourt")
def viewcourt():
    sport_name = request.args.get('Sport_id')
    if sport_name == None or sport_name == '':
        query = {}
    else:
        query = {"sport_id": ObjectId(sport_name)}
    courts = Courts_col.find(query)
    sports = Sports_col.find()
    return render_template("viewcourt.html", courts=courts, sports=sports, sport_name=sport_name)


def get_schedule(schedule_id):
    schedule_col = mydb["Schedule"]
    schedules = schedule_col.find({"_id": ObjectId(schedule_id)})
    return schedules

def get_member(member_id):
    Member_col = mydb["Member"]
    members = Member_col.find_one({"_id": ObjectId(member_id)})
    return members

def get_court(court_id):
    Courts_col = mydb["Courts"]
    courts = Courts_col.find_one({"_id": ObjectId(court_id)})
    return courts

def get_sport(sport_id):
    sports_col = mydb["Sports"]
    sports = sports_col.find_one({"_id": ObjectId(sport_id)})
    return sports

def get_payment(schedule_id):
    payments = Payment_col.find_one({"schedule_id": ObjectId(schedule_id)})
    return payments

def can_flag(time_str,diff):
    now = int(str(datetime.datetime.now().hour))
    time_difference = int(time_str)-now
    print(now,time_str)
    return time_difference <= diff

def pen_flag(time_str,diff):
    now = datetime.datetime.now()
    time_difference = now-time_str
    print(now,time_str)
    return time_difference >= timedelta(hours=diff)

@app.route("/bookcourt")
def bookcourt():
    court_id = request.args.get('court_id')
    today = datetime.datetime.now().date()
    date_range = [(today + timedelta(days=x)).strftime('%Y-%m-%d') for x in range(7)]
    return render_template("bookcourt.html", court_id=court_id,date_range=date_range)


@app.route("/bookcourt1", methods=['post'])

def bookcourt1():
    court_id = request.form.get('court_id')
    date = request.form.get('Date')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    start_hour = int(start_time.split(":")[0])
    end_hour = int(end_time.split(":")[0])
    slots = end_hour - start_hour

    today = datetime.datetime.now().date()
    current_hour = datetime.datetime.now().hour

    if (end_hour <= start_hour) or ( today == date and start_hour <= current_hour <end_hour):
        return render_template("msg.html", msg="Invalid Timings", color="bg-danger text-white")

    status = "Payment Pending"
    price_per_slot = float(Courts_col.find_one({'_id': ObjectId(court_id)}, {'price': 1})['price'].split(" ")[0])

    def check_schedule_availability(query):
        schedules = Schedule_col.find(query)
        if schedules is not None:
            schedules = list(schedules)
            if schedules:
                for schedule in schedules:
                    schedule_start = int(schedule['start_time'].split(":")[0])
                    schedule_end = int(schedule['end_time'].split(":")[0])
                    if (schedule_start >= start_hour and schedule_start < end_hour) or \
                       (schedule_end <= end_hour and schedule_end > start_hour):
                        return render_template("msg.html", msg="Booking Not available for this Schedule",
                                               color="bg-danger text-white")
        return None

    query_1 = {
        "court_id": ObjectId(court_id),
        "date": date,
        "status": {"$nin": ["Booking Cancelled"]}
    }
    result_1 = check_schedule_availability(query_1)

    query_2 = {
        "member_id": ObjectId(session['Member_id']),
        "date": date,
        "status": {"$nin": ["Booking Cancelled"]}
    }
    result_2 = check_schedule_availability(query_2)

    if result_1 or result_2:
        return result_1 or result_2

    booking_amount = str(price_per_slot * slots)+" USD"
    query_3 = {
        "court_id": ObjectId(court_id),
        "member_id": ObjectId(session['Member_id']),
        "Amount": booking_amount,
        "start_time": start_time,
        "end_time": end_time,
        "date": date,
        'c_flag': 1,
        'p_flag': 1,
        'Booking_timestamp': datetime.datetime.now(),
        "status": status
    }
    sport_id = Courts_col.find_one({'_id':ObjectId(court_id)})['sport_id']
    sport_type=Sports_col.find_one({'_id':ObjectId(sport_id)})['category']
    if sport_type == 'Team':
        query_3["check-in status"]="Waiting for CheckIn"
    Schedule_col.insert_one(query_3)
    schedule_id = str(Schedule_col.find_one(
        {'member_id': ObjectId(session['Member_id']), 'court_id': ObjectId(court_id), 'date': date},
        {'_id': 1}
    )['_id'])

    return redirect('payAmount?schedule_id=' + schedule_id)

@app.route("/viewbookings")
def viewbookings():
    court_id = request.form.get('court_id')
    now = datetime.datetime.now()
    if session['role'] == 'Member':
        query = {'member_id':ObjectId(session['Member_id'])}
        schedules = Schedule_col.find(query)
        for schedule in list(schedules):
            if schedule['status']=='Payment Pending' and now.date()>schedule['Booking_timestamp'].date():
                Schedule_col.update_one({'_id':schedule['_id']},{'$set':{"status":"Booking Cancelled","c_flag":0,"p_flag":0}})
                continue
            elif schedule['status']=='Payment Pending' and now.date()==schedule['Booking_timestamp'].date() and pen_flag(schedule['Booking_timestamp'],2):
                Schedule_col.update_one({'_id':schedule['_id']},{'$set':{"status":"Booking Cancelled","c_flag":0,"p_flag":0}})
                continue
            payment=get_payment(schedule['_id'])
            if schedule['status']=='Booking Done' and now.date()>datetime.datetime.strptime(schedule['date'],'%Y-%m-%d').date():
                Schedule_col.update_one({'_id':schedule['_id']},{'$set':{"c_flag":0}})
                continue
            elif schedule['status']=='Booking Done' and now.date()==datetime.datetime.strptime(schedule['date'],'%Y-%m-%d').date() and can_flag(schedule['start_time'].split(":")[0],12):
                Schedule_col.update_one({'_id':schedule['_id']},{'$set':{"c_flag":0}})
                continue
    elif session['role'] == 'admin':
        court_id = request.args.get('court_id')
        query = {"court_id": ObjectId(court_id)}
    schedules = Schedule_col.find(query)
    schedules=list(schedules)
    if len(schedules)==0:
        return render_template("msg.html", msg="No Bookings Available", color="bg-danger")
    return render_template("viewbookings.html", schedules=schedules, get_member=get_member,
                           get_sport=get_sport, get_court=get_court, get_payment=get_payment,now=now)


@app.route("/payAmount")
def payAmount():
    schedule_id = request.args.get('schedule_id')
    schedule = Schedule_col.find_one({"_id" : ObjectId(schedule_id)})
    license_amount = schedule['Amount']
    return render_template("payAmount.html", schedule_id=schedule_id, member_id=schedule['member_id'], license_amount=license_amount)

@app.route("/payAmount1", methods=['post'])
def payAmount1():
    if session['role']=="Member":
            schedule_id = request.form.get('schedule_id')
            schedule=Schedule_col.find_one({'_id':ObjectId(schedule_id)})
            query = {"_id": ObjectId(schedule_id)}
            query2 = {"$set": {"status": "Booking Done","p_flag":0}}
            record=Schedule_col.update_one(query, query2)
            Payment_col.insert_one({'schedule_id':ObjectId(schedule_id),'member_id':schedule['member_id'],'Amount_paid':schedule['Amount'],'purchase_timestamp':datetime.datetime.now(),'purchase_type':'Court Booking'})
            Timeslot_col.insert_one({'schedule_id':ObjectId(record.upserted_id),'member_id':ObjectId(session['Member_id']),'court_id':schedule['court_id']})
            member=Member_col.find_one({'_id':schedule['member_id']})
            court=Courts_col.find_one({'_id':schedule['court_id']})
            sport=Sports_col.find_one({'_id':court['sport_id']})
            schedule=Schedule_col.find_one({'_id':ObjectId(schedule_id)})
            booking_details = {"Name" : member['name'], 'username' : member['username'], 'mobile_no':member['mobile_no'], 'sport':sport['name'], 'court_type':sport['type'],'court' : court['name'], 'email':member['email'], 'price':schedule['Amount'], 
                               'status':schedule['status'], 'date':schedule['date'], 'start_time':schedule['start_time'], 'end_time':schedule['end_time'],'Booking_time': schedule['Booking_timestamp'] }
            booking(booking_details)
            return render_template("msg.html", msg="Court Booked Successfully", color="bg-success")
    else:
        return render_template("msg.html", msg="Something went wrong", color="bg-danger")

@app.route("/payAmount2", methods=['post'])
def payAmount2():
    try: 
        member_id = request.form.get('member_id')
        current_date = datetime.date.today()
        one_year_from_now = current_date + datetime.timedelta(days=365)
        query1 = {"_id": ObjectId(member_id)}
        query2 = {"$set":{"membership_status":"Active",'start_date':current_date.isoformat(),'expiry_date':one_year_from_now.isoformat()}}
        Member_col.update_one(query1,query2)
        member = Member_col.find_one(query1)
        customerreg(member)
        Payment_col.insert_one({'member_id':ObjectId(member_id),'Amount_paid':"5.00 USD",'purchase_timestamp':datetime.datetime.now(),'purchase_type':'Membership Purchase'})
        return render_template("msg.html", msg="Membership Purchase Succesful", color="bg-warning")
    except:
        return render_template("msg.html", msg="Something went wrong", color="bg-danger")

@app.route("/cancelled")
def cancelled():
    schedule_id = request.args.get('schedule_id')
    query = {'_id': ObjectId(schedule_id)}
    schedule=Schedule_col.find_one(query)
    query1 = {"$set": {"status": "Booking Cancelled"}}
    Schedule_col.update_one(query, query1)
    if schedule['status']!="Payment pending":
        now= datetime.datetime.now()
        Payment_col.update_one({'schedule_id':ObjectId(schedule_id)},{'$set':{'cancellation_timestamp':now,'purchase_type':"Court Booking Cancelled"}})
        Timeslot_col.delete_one({'schedule_id':ObjectId(schedule_id)})
    return redirect("/viewbookings")


@app.route("/logout")
def logout():
    session.clear()
    return render_template("index.html")

#######

def customerreg(user_details):
    details=user_details
    details['bucket']='sportz-userreg'
    details['file_name']=user_details['username']
    details['_id'] = str(details['_id'])
    write_to_s3(details)
    return

def booking(booking_details):
    details=booking_details
    details['bucket']='sportz-courtbooking'
    details['Booking_time'] = str(details['Booking_time'])
    bt= details['Booking_time']
    details['Booking_time'] = ''.join(x for x in details['Booking_time'] if x.isalnum())
    details['file_name']=booking_details['Name']+booking_details['Booking_time']
    details['Booking_time'] = bt
    write_to_s3(details)
    return

def write_to_s3(details):
    s3 = boto3.client('s3',
                   aws_access_key_id=credentials['AccessKeyId'],
                   aws_secret_access_key=credentials['SecretAccessKey'],
                   aws_session_token=credentials['SessionToken'])
    file_name = f"{details['file_name']}.json"
    s3.put_object(
        Body=json.dumps(details),
        Bucket=details['bucket'],
        Key=file_name
    )
    print('file placed successfully')
    return

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0")