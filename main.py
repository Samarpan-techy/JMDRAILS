from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import oracledb
import hashlib
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_USER = "SYSTEM"
DB_PASSWORD = "Maa@1415"
DB_HOST = "localhost"
DB_PORT = 1521
DB_SERVICE_NAME = "XEPDB1"

dsn = oracledb.makedsn(DB_HOST, DB_PORT, service_name=DB_SERVICE_NAME)

def get_db_connection():
    try:
        conn = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn)
        return conn
    except Exception as e:
        print(f"❌ Oracle Connection Error: {e}")
        raise Exception(str(e))

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        full_name, email, mobile, password = data.get('full_name'), data.get('email'), data.get('mobile'), data.get('password')
        if not all([full_name, email, mobile, password]):
            return jsonify({"message": "Saari details bharein!"}), 400
        hashed_pw = hash_password(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        out_status = cursor.var(oracledb.STRING, 100)
        out_message = cursor.var(oracledb.STRING, 500)
        sql = "BEGIN REGISTER_NEW_USER(:1, :2, :3, :4, :5, :6); END;"
        cursor.execute(sql, [full_name, email, mobile, hashed_pw, out_status, out_message])
        status_result, message_result = out_status.getvalue(), out_message.getvalue()
        cursor.close(); conn.close()
        if status_result == 'SUCCESS':
            return jsonify({"message": "Registration Successful!"})
        return jsonify({"message": message_result}), 400
    except Exception as e:
        return jsonify({"message": f"DB Error: {str(e)}"}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        email, password = data.get('email'), data.get('password')
        if not email or not password:
            return jsonify({"message": "Email aur Password dono daalein!"}), 400
        hashed_pw = hash_password(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT full_name FROM NEW_USERS WHERE email = :1 AND password_hash = :2", [email, hashed_pw])
        result = cursor.fetchone()
        cursor.close(); conn.close()
        if result:
            return jsonify({"status": "success", "message": "Login Successful!", "name": result[0]})
        return jsonify({"status": "error", "message": "Invalid Email or Password!"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server Error: {str(e)}"}), 500

@app.route('/search_trains', methods=['POST'])
def search_trains():
    try:
        data = request.json
        from_station, to_station = data.get('from_station', '').strip(), data.get('to_station', '').strip()
        if not from_station or not to_station:
            return jsonify({"message": "Please enter both From and To stations."}), 400
        from_code = from_station.split('(')[-1].replace(')', '').strip() if '(' in from_station else from_station
        to_code = to_station.split('(')[-1].replace(')', '').strip() if '(' in to_station else to_station
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT t.train_number, t.train_name, t.source, t.destination, t.total_seats, MAX(s.departure_time), MAX(s.arrival_time)
            FROM TRAINS t LEFT JOIN TRAIN_SCHEDULE s ON t.train_number = s.train_number
            WHERE (t.source LIKE :from_code OR :from_code LIKE '%' || t.source || '%') AND (t.destination LIKE :to_code OR :to_code LIKE '%' || t.destination || '%')
            GROUP BY t.train_number, t.train_name, t.source, t.destination, t.total_seats
        """
        cursor.execute(sql, {"from_code": from_code, "to_code": to_code})
        rows = cursor.fetchall()
        trains = [{"train_number": r[0], "train_name": r[1], "source": r[2], "destination": r[3], "total_seats": r[4], "dep_time": r[5] if r[5] else "N/A", "arr_time": r[6] if r[6] else "N/A"} for r in rows]
        cursor.close(); conn.close()
        return jsonify({"trains": trains})
    except Exception as e:
        return jsonify({"message": f"Server Error: {str(e)}"}), 500

@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    try:
        data = request.json
        train_number, passengers, total_amount = data.get('train_number'), data.get('passengers', []), data.get('total_amount')
        user_email = data.get('user_email', 'guest@jmdrails.com')
        if not passengers:
            return jsonify({"status": "error", "message": "No passengers added!"}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        pnr_number = str(random.randint(1000000000, 9999999999))
        booking_date = datetime.now()

        for p in passengers:
            sql_passenger = "INSERT INTO PASSENGERS_table (name, age, gender, berth_preference, id_proof_type, id_proof_number) VALUES (:1, :2, :3, :4, :5, :6) RETURNING passenger_id INTO :7"
            passenger_id_var = cursor.var(oracledb.NUMBER)
            cursor.execute(sql_passenger, [p['name'], p['age'], p['gender'], p['berth'], p['id_type'], p['id_number'], passenger_id_var])
            passenger_id = passenger_id_var.getvalue()[0]

            coach = random.choice(["S1", "S2", "S3", "S4", "B1", "B2"])
            seat_num = random.randint(1, 72)
            seat_str = f"{coach}-{seat_num}"

            cursor.execute("INSERT INTO BOOKINGS (pnr_number, passenger_id, train_number, booking_date, status, user_email) VALUES (:1, :2, :3, :4, 'Confirmed', :5)", [pnr_number, passenger_id, train_number, booking_date, user_email])
            cursor.execute("INSERT INTO BOOKING_DETAILS (pnr_number, passenger_id, seat_number, fare) VALUES (:1, :2, :3, :4)", [pnr_number, passenger_id, seat_str, 890])

        cursor.execute("INSERT INTO PAYMENTS (pnr_number, amount, payment_mode) VALUES (:1, :2, :3)", [pnr_number, total_amount, "UPI"])
        conn.commit(); cursor.close(); conn.close()
        return jsonify({"status": "success", "message": "Booking Confirmed!", "pnr": pnr_number})
    except Exception as e:
        return jsonify({"status": "error", "message": f"DB Error: {str(e)}"}), 500

@app.route('/check_pnr', methods=['POST'])
def check_pnr():
    try:
        data = request.json
        pnr_number = data.get('pnr_number', '').strip()
        if not pnr_number or len(pnr_number) != 10:
            return jsonify({"status": "error", "message": "Kripya 10 digit ka sahi PNR daalein!"}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        sql_booking = "SELECT b.pnr_number, t.train_number, t.train_name, t.source, t.destination, b.status, s.journey_date, s.departure_time, s.arrival_time FROM BOOKINGS b JOIN TRAINS t ON b.train_number = t.train_number LEFT JOIN TRAIN_SCHEDULE s ON t.train_number = s.train_number WHERE b.pnr_number = :pnr AND ROWNUM = 1"
        cursor.execute(sql_booking, {"pnr": pnr_number})
        booking_row = cursor.fetchone()
        if not booking_row:
            return jsonify({"status": "error", "message": "Is PNR number ki koi booking nahi mili!"}), 404

        booking_data = {
            "pnr": booking_row[0], "train_number": booking_row[1], "train_name": booking_row[2],
            "source": booking_row[3], "destination": booking_row[4], "status": booking_row[5],
            "journey_date": booking_row[6].strftime('%d %b %Y') if booking_row[6] else "N/A",
            "dep_time": booking_row[7] if booking_row[7] else "N/A",
            "arr_time": booking_row[8] if booking_row[8] else "N/A"
        }

        cursor.execute("SELECT p.name, p.age, p.gender, p.berth_preference, d.seat_number FROM BOOKINGS b JOIN PASSENGERS_table p ON b.passenger_id = p.passenger_id LEFT JOIN BOOKING_DETAILS d ON b.pnr_number = d.pnr_number AND b.passenger_id = d.passenger_id WHERE b.pnr_number = :pnr", {"pnr": pnr_number})
        rows = cursor.fetchall()

        passengers = []
        for r in rows:
            passengers.append({
                "name": r[0], "age": r[1], "gender": r[2],
                "berth": r[3] if r[3] else "No Preference",
                "seat": r[4] if r[4] else "N/A"
            })

        booking_data["passengers"] = passengers
        cursor.close(); conn.close()
        return jsonify({"status": "success", "data": booking_data})
    except Exception as e:
        return jsonify({"status": "error", "message": f"DB Error: {str(e)}"}), 500

@app.route('/my_bookings', methods=['POST'])
def my_bookings():
    try:
        data = request.json
        user_email = data.get('user_email')

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT b.pnr_number, t.train_number, t.train_name, t.source, t.destination, 
                   b.booking_date, b.status, s.journey_date, s.departure_time, s.arrival_time, 
                   p.name, p.age, p.gender
            FROM BOOKINGS b 
            JOIN TRAINS t ON b.train_number = t.train_number 
            JOIN PASSENGERS_table p ON b.passenger_id = p.passenger_id 
            LEFT JOIN TRAIN_SCHEDULE s ON t.train_number = s.train_number
            WHERE b.user_email = :email OR b.user_email IS NULL
            ORDER BY b.booking_date DESC
        """
        cursor.execute(sql, {"email": user_email})
        rows = cursor.fetchall()

        bookings_dict = {}
        for row in rows:
            pnr = row[0]
            if pnr not in bookings_dict:
                bookings_dict[pnr] = {
                    "pnr": pnr, "train_number": row[1], "train_name": row[2], 
                    "source": row[3], "destination": row[4], 
                    "booking_date": row[5].strftime('%d %b %Y') if row[5] else "N/A", 
                    "status": row[6], 
                    "journey_date": row[7].strftime('%d %b %Y') if row[7] else "N/A", 
                    "dep_time": row[8] if row[8] else "N/A", 
                    "arr_time": row[9] if row[9] else "N/A", 
                    "passengers": []
                }
            bookings_dict[pnr]["passengers"].append({
                "name": row[10], "age": row[11], "gender": row[12]
            })

        cursor.close(); conn.close()
        return jsonify({"status": "success", "bookings": list(bookings_dict.values())})
    except Exception as e:
        return jsonify({"status": "error", "message": f"DB Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)