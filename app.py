from flask import Flask, render_template, request, jsonify, redirect
import MySQLdb
import random

app = Flask(__name__, template_folder='template')

# MySQL Configuration
db = MySQLdb.connect(host="localhost", user="root", password="Rajnandini@123", database="railway_db")
cursor = db.cursor()

# Home Page
@app.route('/')
def home():
    cursor.execute("SELECT train_id, train_name, from_place, to_place, seat_no FROM trains")
    trains = cursor.fetchall()
    return render_template('index.html', trains=trains)

# Book Ticket
@app.route('/book_ticket', methods=['POST'])
def book_ticket():
    train_id = request.form['train_id']
    passenger_name = request.form['passenger_name']
    age = request.form['age']

    # Check if seats are available
    cursor.execute("SELECT seat_no FROM trains WHERE train_id = %s", (train_id,))
    seat_data = cursor.fetchone()

    if seat_data and seat_data[0] > 0:
        seat_no = seat_data[0]
        pnr_no = random.randint(100000, 999999)
        
        # Insert Booking
        cursor.execute(
            "INSERT INTO bookings (pnr, train_id, passenger_name, age, seat_no) VALUES (%s, %s, %s, %s, %s)", 
            (pnr_no, train_id, passenger_name, age, seat_no)
        )
        
        # Reduce seat count instead of deleting the train row
        cursor.execute("UPDATE trains SET seat_no = seat_no - 1 WHERE train_id = %s", (train_id,))
        
        db.commit()
        return f"Ticket Booked! PNR: {pnr_no}, Seat No: {seat_no}"
    
    else:
        cursor.execute(
            "INSERT INTO waiting_list (train_id, passenger_name, age) VALUES (%s, %s, %s)", 
            (train_id, passenger_name, age)
        )
        db.commit()
        return "No seats available. Added to waiting list."

# Cancel Ticket
@app.route('/cancel_ticket', methods=['POST'])
def cancel_ticket():
    pnr = request.form['pnr']
    
    cursor.execute("SELECT train_id, seat_no FROM bookings WHERE pnr = %s", (pnr,))
    booking = cursor.fetchone()

    if booking:
        train_id, seat_no = booking

        # Remove the booking
        cursor.execute("DELETE FROM bookings WHERE pnr = %s", (pnr,))
        
        # Restore seat count in the trains table
        cursor.execute("UPDATE trains SET seat_no = seat_no + 1 WHERE train_id = %s", (train_id,))

        # Assign seat to waiting list person
        cursor.execute("SELECT id, passenger_name, age FROM waiting_list WHERE train_id = %s ORDER BY id LIMIT 1", (train_id,))
        waitlist = cursor.fetchone()

        if waitlist:
            waitlist_id, passenger_name, age = waitlist
            new_pnr = random.randint(100000, 999999)
            
            cursor.execute(
                "INSERT INTO bookings (pnr, train_id, passenger_name, age, seat_no) VALUES (%s, %s, %s, %s, %s)", 
                (new_pnr, train_id, passenger_name, age, seat_no)
            )
            
            cursor.execute("DELETE FROM waiting_list WHERE id = %s", (waitlist_id,))

        db.commit()
        return "Ticket Cancelled. THANK YOU FOR PURCHASE."
    
    else:
        return "PNR Not Found!"

# Check Booking Details
@app.route('/check_ticket', methods=['GET'])
def check_ticket():
    pnr = request.args.get('pnr')
    
    cursor.execute("SELECT * FROM bookings WHERE pnr = %s", (pnr,))
    ticket = cursor.fetchone()
    
    if ticket:
        return jsonify({
            "PNR": ticket[0],
            "Train ID": ticket[1],
            "Passenger Name": ticket[2],
            "Age": ticket[3],
            "Seat No": ticket[4],
            "Status": "Confirmed"
        })
    else:
        return "PNR Not Found!"

# Show Chart for Train
@app.route('/chart', methods=['GET'])
def train_chart():
    cursor.execute("SELECT * FROM bookings ")
    bookings = cursor.fetchall()
    return render_template('/chart.html', bookings=bookings)

if __name__ == '__main__':
    app.run(debug=True)
