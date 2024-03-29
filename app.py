from flask import Flask, render_template, request, redirect, jsonify, session
import psycopg2
from psycopg2.extras import RealDictCursor
import requests

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Set a secret key for the session

# Database connection parameters
DB_HOST = "localhost"
DB_NAME = "chatgpt"
DB_USER = "postgres"
DB_PASS = "ezwq2173"

# Establish a database connection
def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
    return conn

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    # Create users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            fullname VARCHAR(100),
            email VARCHAR(100),
            collegename VARCHAR(100),
            phonenumber VARCHAR(15),
            lab VARCHAR(50)
        )
    """)

    # Create submissions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            submission_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            submission_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            prompt_text TEXT,
            image_url VARCHAR(255),
            final_submission BOOLEAN DEFAULT FALSE
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

# Call the function to create tables
create_tables()



# Define the API endpoint for image generation
IMAGE_GENERATION_API = "https://modelslab.com/api/v6/realtime/text2img"
  # Replace this with your actual bearer token

# Define your login route
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            data = request.form
            username = data['username']
            email = data['email']
            full_name = data['fullname']
            phone_number = data['phonenumber']
            college_name = data['collegename']
            lab = data['lab']
            
            # Store username in session
            session['username'] = username
            
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute('INSERT INTO users (username, email, lab, fullname, phonenumber, collegename) VALUES (%s, %s, %s, %s, %s, %s)',
                        (username, email, lab, full_name, phone_number, college_name))
            conn.commit()
            cur.close()
            conn.close()
            
            # Redirect to the image generation page after successful login
            return redirect('/generate_image')
        
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    else:
        return render_template('index.html')
    



# Define your login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.form
            username = data['username']
            phone_number = data['phonenumber']

            # Check if the username and phone number exist in the database
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute('SELECT * FROM users WHERE username = %s AND phonenumber = %s', (username, phone_number))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user:
                # Store username in session
                session['username'] = user['username']
                return redirect('/generate_image')  # Redirect to the image generation page after successful login
            else:
                error_message = "Invalid username or phone number"
                return render_template('login.html', error=error_message)
                
            # Redirect to the image generation page after successful login
            return redirect('/generate_image')

        except Exception as e:
            error_message = "An error occurred: " + str(e)
            return render_template('login.html', error=error_message)

    else:
        return render_template('login.html')




# Define the image generation route
@app.route('/generate_image', methods=['GET', 'POST'])
def generate_image():
    if request.method == 'POST':
        data = request.json

        # Prepare data for the API call
        payload = {
            "key" : "bK7OnLhSufswiXktBY38IDbPP4TlzJSAiPcW9GyLHtilcngZoVE8zAGYpips",
            "prompt": data.get('prompt', ''),
            "width": data.get('width', ''),
            "height": data.get('height', ''),               
            "providers": data.get('providers', ''),  # Handle the case where 'providers' might not exist
            "fallback_providers": data.get('fallback_providers', ''),
             "safety_checker": True  # Make safety_checker static
        }

        # Set up headers with the bearer token
        headers = {
            'Content-Type': 'application/json'
        }

        # Make a request to the image generation API
        response = requests.post(IMAGE_GENERATION_API, json=payload, headers=headers)

        # Return the response from the image generation API
        return jsonify(response.json())
    else:
        return render_template('generate_image.html')

# Define the route to submit the selected image to the database
@app.route('/submit_image', methods=['POST'])
def submit_image():
    selected_image_url = request.form.get('selectedImageUrl')
    if selected_image_url:
        # Fetch the user's details from the session
        username = session.get('username')

        if username is None:
            # If username is not found in the session, return an error response
            return jsonify({'status': 'error', 'message': 'Username not found. Please log in.'}), 401
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE users SET image_url = %s WHERE username = %s', (selected_image_url, username))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Image submitted successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    else:
        return jsonify({'status': 'error', 'message': 'No image selected'})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
