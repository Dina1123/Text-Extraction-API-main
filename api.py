import random
from flask import Flask, request, jsonify , render_template, send_from_directory
from flask_cors import CORS
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import os

def create_app(test_config=None):
    # Create and configure the app
    template_dir = os.path.abspath('templates')

    # Initialize the app
    app = Flask(__name__, template_folder=template_dir)
    
    # Load default config from settings.py
    app.config.from_pyfile('settings.py')  # Load database environment variables

    # Initialize Plugins
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Config MySQL
    app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
    app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
    app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
    app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')
    app.config['MYSQL_PORT'] = 3306  # If the port is constant, you don't need to set it from environment variables.
    # app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

    # Initialize MySQL
    mysql = MySQL(app)
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    UPLOAD_FOLDER = 'upload'
    ALLOWED_EXTENSIONS = {'jpg', 'png'}
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


    @app.route('/upload_image', methods=['POST'])
    def upload_image():
        if 'images' not in request.files:
            return jsonify({'status': 'failure', 'message': 'No file part'})

        file = request.files['images']

        if file.filename == '':
            return jsonify({'status': 'failure', 'message': 'No selected file'})

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                return jsonify({'status': 'failure', 'message': 'Image with the same name already exists'})
           
            file.save(file_path)

            # Insert image and text data into the database
            cursor = mysql.connection.cursor()
            data = {
                'images': filename,
                'texts': request.form.get('texts', '')
            }
            cursor.execute("INSERT INTO users (images, texts) VALUES (%(images)s, %(texts)s)", data)
            mysql.connection.commit()
            cursor.close()

            return jsonify({'status': 'success', 'message': 'Image uploaded and data inserted into the database'})

        return jsonify({'status': 'failure', 'message': 'Invalid file format'})

    @app.route('/upload', methods=['GET'])
    def list_uploaded_files():
        upload_folder = app.config['UPLOAD_FOLDER']
        files = [f for f in os.listdir(upload_folder) if os.path.isfile(os.path.join(upload_folder, f))]
        return jsonify({'files': files})

    @app.route('/upload/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


    @app.route('/') 
    def index():
         return render_template('index.html')

    def delete_data(table, where, values=None, json=True):
        cursor = mysql.connection.cursor()
        cursor.execute(f"DELETE FROM {table} WHERE {where}", values)
        count = cursor.rowcount
        mysql.connection.commit()
        cursor.close()

        if json:
            if count > 0:
                return jsonify({'status': 'success'})
            else:
                return jsonify({'status': 'failure'})

        return count

    @app.route('/delete_image', methods=['POST'])
    def delete_image():
        image_id = request.form.get('id')
        
        if image_id is None:
            return jsonify({'status': 'failure', 'message': 'Image ID is required'})

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT images FROM users WHERE id = %s", (image_id,))
        result = cursor.fetchone()

        if result:
            image_name = result[0]

            # Delete the image file from the upload folder
            upload_folder = app.config['UPLOAD_FOLDER']
            image_path = os.path.join(upload_folder, image_name)
            
            try:
                os.remove(image_path)
            except OSError as e:
                return jsonify({'status': 'failure', 'message': f'Error deleting image file: {str(e)}'})

            # Delete the image record from the database
            delete_data('users', 'id = %s', (image_id,), json=True)

            return jsonify({'status': 'success', 'message': 'Image and associated data deleted successfully'})
        else:
            mysql.connection.commit()
            return jsonify({'status': 'failure', 'message': 'Image not found'})

    # Define a route to list all images and their details
    @app.route('/list_images', methods=['GET'])
    def list_images():
        cursor = mysql.connection.cursor()

        # Retrieve all data from the database
        cursor.execute("SELECT * FROM users")
        all_data = cursor.fetchall()
        cursor.close()

        return jsonify({'status': 'success', 'data': all_data})

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True , host= '0.0.0.0', port=8080)
