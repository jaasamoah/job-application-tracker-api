import os
import psycopg2
from psycopg2 import sql
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
from urllib.parse import urlparse
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# PostgreSQL Configuration
def get_db_connection():
    try:
        db_url = os.environ.get('DATABASE_URL')
        
        if db_url:
            # Parse Render-style DATABASE_URL
            url = urlparse(db_url)
            conn = psycopg2.connect(
                database=url.path[1:],
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port
            )
        else:
            # Fallback to local development
            conn = psycopg2.connect(
                database=os.environ.get('DB_NAME', 'job_tracker'),
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', ''),
                host=os.environ.get('DB_HOST', 'localhost'),
                port=os.environ.get('DB_PORT', 5432)
            )
        return conn
    except psycopg2.Error as err:
        app.logger.error(f"Database connection error: {err}")
        raise

# Create PostgreSQL table if not exists
def init_db():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id SERIAL PRIMARY KEY,
                company_name VARCHAR(100) NOT NULL,
                position VARCHAR(100) NOT NULL,
                status VARCHAR(50) NOT NULL,
                application_date DATE,
                notes TEXT
            )
        ''')
        conn.commit()
        app.logger.info("Database initialized successfully!")
    except psycopg2.Error as err:
        app.logger.error(f"Database initialization error: {err}")
    finally:
        if conn:
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
    
    # Validate date format
    if data.get('application_date'):
        try:
            datetime.strptime(data['application_date'], '%Y-%m-%d')
        except ValueError:
            errors.append("Invalid date format. Use YYYY-MM-DD")
            
    return errors

# API Endpoints
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/applications', methods=['GET'])
def get_applications():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, company_name, position, status, application_date, notes FROM applications')
        columns = [desc[0] for desc in cursor.description]
        applications = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Convert date objects to ISO strings
        for app in applications:
            if app['application_date']:
                app['application_date'] = app['application_date'].isoformat()
        return jsonify(applications)
    except psycopg2.Error as err:
        app.logger.error(f"Database error: {err}")
        return jsonify({"error": "Database operation failed"}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

@app.route('/applications/<int:app_id>', methods=['GET'])
def get_application(app_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, company_name, position, status, application_date, notes FROM applications WHERE id = %s', 
            (app_id,)
        )
        columns = [desc[0] for desc in cursor.description]
        application = cursor.fetchone()
        
        if not application:
            return jsonify({"error": "Application not found"}), 404
            
        application = dict(zip(columns, application))
        if application['application_date']:
            application['application_date'] = application['application_date'].isoformat()
        return jsonify(application)
    except psycopg2.Error as err:
        app.logger.error(f"Database error: {err}")
        return jsonify({"error": "Database operation failed"}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

@app.route('/applications', methods=['POST'])
def create_application():
    conn = None
    try:
        data = request.get_json()
        errors = validate_job_application(data)
        if errors:
            return jsonify({"errors": errors}), 400
        
        # Convert date string to Python date object
        app_date = None
        if data.get('application_date'):
            app_date = datetime.strptime(data['application_date'], '%Y-%m-%d').date()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO applications 
            (company_name, position, status, application_date, notes) 
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            ''', 
            (
                data['company_name'],
                data['position'],
                data['status'],
                app_date,  # Use converted date
                data.get('notes', '')
            )
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        
        # Return created application
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
    except psycopg2.Error as err:
        app.logger.error(f"Database error: {err}")
        return jsonify({"error": "Database operation failed"}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

@app.route('/applications/<int:app_id>', methods=['PUT'])
def update_application(app_id):
    conn = None
    try:
        data = request.get_json()
        errors = validate_job_application(data)
        if errors:
            return jsonify({"errors": errors}), 400
        
        # Convert date string to Python date object
        app_date = None
        if data.get('application_date'):
            app_date = datetime.strptime(data['application_date'], '%Y-%m-%d').date()
        
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
                app_date,  # Use converted date
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
    except psycopg2.Error as err:
        app.logger.error(f"Database error: {err}")
        return jsonify({"error": "Database operation failed"}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

@app.route('/applications/<int:app_id>', methods=['DELETE'])
def delete_application(app_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM applications WHERE id = %s', (app_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Application not found"}), 404
            
        return jsonify({"message": "Application deleted successfully"}), 200
    except psycopg2.Error as err:
        app.logger.error(f"Database error: {err}")
        return jsonify({"error": "Database operation failed"}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    # Only run directly in development mode
    if os.environ.get('FLASK_ENV') == 'development':
        app.run(host='0.0.0.0', port=5000, debug=True)
