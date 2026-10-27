CREATE TABLE PASSENGERS_table (
    passenger_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR2(100) NOT NULL,
    age NUMBER NOT NULL,
    gender VARCHAR2(10),
    contact VARCHAR2(15)
);
CREATE TABLE TRAINS (
    train_number VARCHAR2(10) PRIMARY KEY,
    train_name VARCHAR2(100) NOT NULL,
    source VARCHAR2(100) NOT NULL,
    destination VARCHAR2(100) NOT NULL,
    total_seats NUMBER NOT NULL
);
CREATE TABLE TRAIN_SCHEDULE (
    schedule_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    train_number VARCHAR2(10),
    journey_date DATE NOT NULL,
    departure_time VARCHAR2(10) NOT NULL,
    arrival_time VARCHAR2(10) NOT NULL,
    CONSTRAINT fk_schedule_train FOREIGN KEY (train_number) REFERENCES TRAINS(train_number) ON DELETE CASCADE
);
CREATE TABLE BOOKINGS (
    pnr_number VARCHAR2(15) PRIMARY KEY,
    passenger_id NUMBER,
    train_number VARCHAR2(10),
    booking_date DATE NOT NULL,
    status VARCHAR2(20) DEFAULT 'Confirmed',
    CONSTRAINT fk_booking_passenger FOREIGN KEY (passenger_id) REFERENCES PASSENGERS_table(passenger_id),
    CONSTRAINT fk_booking_train FOREIGN KEY (train_number) REFERENCES TRAINS(train_number)
);
CREATE TABLE BOOKING_DETAILS (
    detail_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pnr_number VARCHAR2(15),
    passenger_id NUMBER,
    seat_number VARCHAR2(10),
    fare NUMBER(10, 2) NOT NULL,
    CONSTRAINT fk_details_booking FOREIGN KEY (pnr_number) REFERENCES BOOKINGS(pnr_number) ON DELETE CASCADE,
    CONSTRAINT fk_details_passenger FOREIGN KEY (passenger_id) REFERENCES PASSENGERS_table(passenger_id)
);
CREATE TABLE PAYMENTS (
    payment_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pnr_number VARCHAR2(15),
    amount NUMBER(10, 2) NOT NULL,
    payment_mode VARCHAR2(50),
    refund_status VARCHAR2(50) DEFAULT 'No Refund',
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_payment_booking FOREIGN KEY (pnr_number) REFERENCES BOOKINGS(pnr_number) ON DELETE CASCADE
);
CREATE TABLE AUDIT_LOG (
    log_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pnr_number VARCHAR2(15),
    action_type VARCHAR2(50) NOT NULL,
    change_description CLOB,
    change_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_booking FOREIGN KEY (pnr_number) REFERENCES BOOKINGS(pnr_number) ON DELETE CASCADE
);
CREATE TABLE NEW_USERS (
    user_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name VARCHAR2(100) NOT NULL,
    email VARCHAR2(100) UNIQUE NOT NULL,
    mobile VARCHAR2(15) NOT NULL,
    password_hash VARCHAR2(255) NOT NULL,
    role VARCHAR2(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
CREATE OR REPLACE PROCEDURE REGISTER_NEW_USER (
    p_full_name IN VARCHAR2,
    p_email IN VARCHAR2,
    p_mobile IN VARCHAR2,
    p_password IN VARCHAR2,
    p_status OUT VARCHAR2,
    p_message OUT VARCHAR2
) AS
BEGIN
    INSERT INTO NEW_USERS (full_name, email, mobile, password_hash)
    VALUES (p_full_name, p_email, p_mobile, p_password);
    COMMIT;
    p_status := 'SUCCESS';
    p_message := 'Registration Successful!';
EXCEPTION
    WHEN DUP_VAL_ON_INDEX THEN
        ROLLBACK;
        p_status := 'ERROR';
        p_message := 'Yeh Email pehle se registered hai!';
    WHEN OTHERS THEN
        ROLLBACK;
        p_status := 'ERROR';
        p_message := 'Database Error: ' || SQLERRM;
END;
/
select * from NEW_USERS;
INSERT INTO TRAINS VALUES ('12001', 'New Delhi - Chandigarh Shatabdi', 'NDLS', 'CDG', 500);
INSERT INTO TRAINS VALUES ('12011', 'Kalka Shatabdi Express', 'NDLS', 'CDG', 450);
INSERT INTO TRAINS VALUES ('14095', 'Himalayan Queen', 'NDLS', 'CDG', 300);
INSERT INTO TRAINS VALUES ('12445', 'Uttar Sampark Kranti', 'NDLS', 'SVDK', 600);
INSERT INTO TRAINS VALUES ('12002', 'Bhopal Shatabdi', 'NDLS', 'HBJ', 400);
COMMIT;
INSERT INTO TRAIN_SCHEDULE (train_number, journey_date, departure_time, arrival_time) VALUES ('12001', TO_DATE('25-10-2026', 'DD-MM-YYYY'), '07:40 AM', '11:05 AM');
INSERT INTO TRAIN_SCHEDULE (train_number, journey_date, departure_time, arrival_time) VALUES ('12011', TO_DATE('25-10-2026', 'DD-MM-YYYY'), '07:20 AM', '10:45 AM');
INSERT INTO TRAIN_SCHEDULE (train_number, journey_date, departure_time, arrival_time) VALUES ('12445', TO_DATE('25-10-2026', 'DD-MM-YYYY'), '08:15 PM', '05:30 AM');
INSERT INTO TRAIN_SCHEDULE (train_number, journey_date, departure_time, arrival_time) VALUES ('14095', TO_DATE('25-10-2026', 'DD-MM-YYYY'), '05:30 AM', '11:45 AM');
INSERT INTO TRAIN_SCHEDULE (train_number, journey_date, departure_time, arrival_time) VALUES ('12002', TO_DATE('25-10-2026', 'DD-MM-YYYY'), '06:00 AM', '02:00 PM');
COMMIT;
ALTER TABLE PASSENGERS_table ADD (
    berth_preference VARCHAR2(50),
    id_proof_type VARCHAR2(50),
    id_proof_number VARCHAR2(50)
);
COMMIT;
SELECT * FROM PASSENGERS_table WHERE id_proof_number = '362663722';
SELECT * FROM BOOKINGS WHERE pnr_number = '5879409425';
SELECT * FROM PAYMENTS WHERE pnr_number = '5879409425';
SELECT * FROM BOOKING_DETAILS WHERE pnr_number = '5879409425';
ALTER TABLE BOOKINGS ADD (user_email VARCHAR2(100));
COMMIT;