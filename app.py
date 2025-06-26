import os
import mysql.connector
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# IMySQL Configuration for Railway compatibility
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('MYSQLHOST', 'mysql.railway.internal'),
            user=os.environ.get('MYSQLUSER', 'root'),
            password=os.environ.get('MYSQL_ROOT_PASSWORD', 'WNEVNWzxxQvrScfDJgltwUdfxYXwJaEM'),
            database=os.environ.get('MYSQLDATABASE', 'railway'),
            port=os.environ.get('MYSQLPORT', 3306)
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        raise

# Create MySQL table if not exists
def init_db():
    try:
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
        print("Database initialized successfully!")
    except mysql.connector.Error as err:
        print(f"Database initialization error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Initialize database
init_db()

# Validation function
valid_statuses = ["Applied", "Interview", "Phone Screen", "On-site", "Rejected", "Offer", "Accepted", "Withdrawn"]

def validate_job_application(data):
    errors = []
    if not data.get('company_name'):
        errors.append("Company name is required")
    if not data.get('position'):
        errors.append("Position is required")
    if not data.get('status'):
        errors.append("Status is required")
    elif data.get('status') not in valid_statuses:
        errors.append(f"Invalid status. Valid options: {', '.join(valid_statuses)}")
    return errors

# API Endpoints
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/applications', methods=['GET'])
def get_applications():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM applications')
        applications = cursor.fetchall()
        
        # Convert date objects to ISO strings
        for app in applications:
            if app['application_date']:
                app['application_date'] = app['application_date'].isoformat()
        return jsonify(applications)
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/applications/<int:app_id>', methods=['GET'])
def get_application(app_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM applications WHERE id = %s', (app_id,))
        application = cursor.fetchone()
        
        if not application:
            return jsonify({"error": "Application not found"}), 404
            
        if application['application_date']:
            application['application_date'] = application['application_date'].isoformat()
        return jsonify(application)
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/applications', methods=['POST'])
def create_application():
    try:
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
        return jsonify({
            "id": new_id, 
            "message": "Application created successfully",
            "application": {
                "id": new_id,
                "company_name": data['company_name'],
                "position": data['position'],
                "status": data['status'],
                "application_date": data.get('application_date'),
                "notes": data.get('notes', '')
            }
        }), 201
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/applications/<int:app_id>', methods=['PUT'])
def update_application(app_id):
    try:
        data = request.get_json()
        errors = validate_job_application(data)
        if errors:
            return jsonify({"errors": errors}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            UPDATE applications
            SET company_name = %s,
                position = %s,
                status = %s,
                application_date = %s,
                notes = %s
            WHERE id = %s
            ''', 
            (
                data['company_name'],
                data['position'],
                data['status'],
                data.get('application_date'),
                data.get('notes', ''),
                app_id
            )
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Application not found"}), 404
            
        return jsonify({
            "message": "Application updated successfully",
            "id": app_id
        }), 200
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/applications/<int:app_id>', methods=['DELETE'])
def delete_application(app_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM applications WHERE id = %s', (app_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Application not found"}), 404
            
        return jsonify({"message": "Application deleted successfully"}), 200
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.environ.get('FLASK_DEBUG', False))
