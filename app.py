import os
import mysql.connector
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# MySQL Configuration
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'job_tracker')
    )

# Create MySQL table if not exists
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            company_name VARCHAR(100) NOT NULL,
            position VARCHAR(100) NOT NULL,
            status VARCHAR(50) NOT NULL,
            application_date DATE,
            notes TEXT
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

# Initialize database
init_db()

# Validation function (same as before)
valid_statuses = ["Applied", "Interview", "Phone Screen", "On-site", "Rejected", "Offer", "Accepted", "Withdrawn"]

def validate_job_application(data):
    errors = []
    # ... (your existing validation code) ...
    return errors

# API Endpoints
@app.route('/applications', methods=['GET'])
def get_applications():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM applications')
    applications = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Convert date objects to ISO strings
    for app in applications:
        if app['application_date']:
            app['application_date'] = app['application_date'].isoformat()
    return jsonify(applications)

@app.route('/applications/<int:app_id>', methods=['GET'])
def get_application(app_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM applications WHERE id = %s', (app_id,))
    application = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not application:
        return jsonify({"error": "Application not found"}), 404
    
    if application['application_date']:
        application['application_date'] = application['application_date'].isoformat()
    return jsonify(application)

@app.route('/applications', methods=['POST'])
def create_application():
    data = request.get_json()
    errors = validate_job_application(data)
    if errors:
        return jsonify({"errors": errors}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO applications 
        (company_name, position, status, application_date, notes) 
        VALUES (%s, %s, %s, %s, %s)
        ''', 
        (
            data['company_name'],
            data['position'],
            data['status'],
            data.get('application_date'),
            data.get('notes', '')
        )
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    
    return jsonify({"id": new_id, "message": "Application created"}), 201

# Similarly update PUT and DELETE endpoints to use MySQL

@app.route('/applications/<int:app_id>', methods=['PUT'])
def update_application(app_id):
    # ... similar MySQL implementation ...

@app.route('/applications/<int:app_id>', methods=['DELETE'])
def delete_application(app_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM applications WHERE id = %s', (app_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    
    if not deleted:
        return jsonify({"error": "Application not found"}), 404
    return jsonify({"message": "Application deleted"}), 200

# ... rest of your endpoints ...

if __name__ == '__main__':
    app.run(debug=True)
