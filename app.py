import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
CORS(app)

# In-memory storage for job applications
job_applications = []
next_id = 1

# Valid status options
VALID_STATUSES = ["Applied", "Interview", "Phone Screen", "On-site", "Rejected", "Offer", "Accepted", "Withdrawn"]

def validate_job_application(data, is_update=False):
    """Validate job application data"""
    errors = []
    
    if not is_update or 'company_name' in data:
        if not data.get('company_name') or not data.get('company_name').strip():
            errors.append("Company name is required")
    
    if not is_update or 'position' in data:
        if not data.get('position') or not data.get('position').strip():
            errors.append("Position is required")
    
    if 'status' in data:
        if data.get('status') not in VALID_STATUSES:
            errors.append(f"Status must be one of: {', '.join(VALID_STATUSES)}")
    
    if 'application_date' in data and data.get('application_date'):
        try:
            datetime.fromisoformat(data['application_date'].replace('Z', '+00:00'))
        except ValueError:
            errors.append("Application date must be in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
    
    return errors

def find_job_application(app_id):
    """Find job application by ID"""
    for app in job_applications:
        if app['id'] == app_id:
            return app
    return None

@app.route('/')
def index():
    """Serve the API documentation page"""
    return render_template('index.html')

@app.route('/api/applications', methods=['GET'])
def get_applications():
    """Get all job applications or filter by status"""
    try:
        logger.info(f"GET /api/applications - Query params: {request.args}")
        
        status_filter = request.args.get('status')
        
        if status_filter:
            if status_filter not in VALID_STATUSES:
                return jsonify({
                    'error': f'Invalid status filter. Valid statuses: {", ".join(VALID_STATUSES)}'
                }), 400
            
            filtered_apps = [app for app in job_applications if app['status'] == status_filter]
            return jsonify({
                'applications': filtered_apps,
                'total': len(filtered_apps),
                'filtered_by': status_filter
            })
        
        return jsonify({
            'applications': job_applications,
            'total': len(job_applications)
        })
    
    except Exception as e:
        logger.error(f"Error getting applications: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/applications', methods=['POST'])
def create_application():
    """Create a new job application"""
    try:
        logger.info(f"POST /api/applications - Data: {request.json}")
        
        if not request.json:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        data = request.json
        errors = validate_job_application(data)
        
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        global next_id
        
        # Create new application
        new_app = {
            'id': next_id,
            'company_name': data['company_name'].strip(),
            'position': data['position'].strip(),
            'status': data.get('status', 'Applied'),
            'application_date': data.get('application_date', datetime.now().isoformat()),
            'notes': data.get('notes', ''),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        job_applications.append(new_app)
        next_id += 1
        
        logger.info(f"Created new application with ID: {new_app['id']}")
        return jsonify(new_app), 201
    
    except Exception as e:
        logger.error(f"Error creating application: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/applications/<int:app_id>', methods=['GET'])
def get_application(app_id):
    """Get a specific job application by ID"""
    try:
        logger.info(f"GET /api/applications/{app_id}")
        
        app = find_job_application(app_id)
        if not app:
            return jsonify({'error': 'Job application not found'}), 404
        
        return jsonify(app)
    
    except Exception as e:
        logger.error(f"Error getting application {app_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/applications/<int:app_id>', methods=['PUT'])
def update_application(app_id):
    """Update an existing job application"""
    try:
        logger.info(f"PUT /api/applications/{app_id} - Data: {request.json}")
        
        if not request.json:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        app = find_job_application(app_id)
        if not app:
            return jsonify({'error': 'Job application not found'}), 404
        
        data = request.json
        errors = validate_job_application(data, is_update=True)
        
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        # Update fields if provided
        if 'company_name' in data:
            app['company_name'] = data['company_name'].strip()
        if 'position' in data:
            app['position'] = data['position'].strip()
        if 'status' in data:
            app['status'] = data['status']
        if 'application_date' in data:
            app['application_date'] = data['application_date']
        if 'notes' in data:
            app['notes'] = data['notes']
        
        app['updated_at'] = datetime.now().isoformat()
        
        logger.info(f"Updated application with ID: {app_id}")
        return jsonify(app)
    
    except Exception as e:
        logger.error(f"Error updating application {app_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/applications/<int:app_id>', methods=['DELETE'])
def delete_application(app_id):
    """Delete a job application"""
    try:
        logger.info(f"DELETE /api/applications/{app_id}")
        
        app = find_job_application(app_id)
        if not app:
            return jsonify({'error': 'Job application not found'}), 404
        
        job_applications.remove(app)
        
        logger.info(f"Deleted application with ID: {app_id}")
        return jsonify({'message': 'Job application deleted successfully'}), 200
    
    except Exception as e:
        logger.error(f"Error deleting application {app_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/status-options', methods=['GET'])
def get_status_options():
    """Get valid status options"""
    return jsonify({'statuses': VALID_STATUSES})

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
