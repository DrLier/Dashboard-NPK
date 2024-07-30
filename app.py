import os
from flask import Flask, render_template, request, jsonify
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import joblib

# Create the Flask application instance
app = Flask(__name__)

# File untuk menyimpan waktu tanam dan prediksi
PLANTING_TIME_FILE = 'planting_time.json'
PREDICTION_HISTORY_FILE = 'prediction_history.json'

def save_planting_time(planting_time):
    with open(PLANTING_TIME_FILE, 'w') as f:
        json.dump({'planting_time': planting_time}, f)

def get_planting_time():
    try:
        with open(PLANTING_TIME_FILE, 'r') as f:
            data = json.load(f)
            return data.get('planting_time', None)
    except FileNotFoundError:
        return None

def save_prediction_history(prediction):
    try:
        with open(PREDICTION_HISTORY_FILE, 'r') as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []

    # Check if there is already an entry for today
    today = datetime.now().date()
    if any(datetime.fromisoformat(entry['timestamp']).date() == today for entry in history):
        return

    history.append({'timestamp': datetime.now().isoformat(), 'prediction': prediction})
    with open(PREDICTION_HISTORY_FILE, 'w') as f:
        json.dump(history, f)

def get_prediction_history():
    try:
        with open(PREDICTION_HISTORY_FILE, 'r') as f:
            history = json.load(f)
            # Filter data untuk 7 hari terakhir
            seven_days_ago = datetime.now() - timedelta(days=7)
            return [entry for entry in history if datetime.fromisoformat(entry['timestamp']) > seven_days_ago]
    except FileNotFoundError:
        return []

def calculate_plant_age(planting_time):
    if planting_time:
        planting_time = datetime.fromtimestamp(planting_time / 1000)  # Convert from milliseconds to seconds
        current_time = datetime.now()
        age_in_days = (current_time - planting_time).days
        return age_in_days
    return 0

def get_npk_values():
    headers = {
        'X-M2M-Origin': '44dbb85550128192:c079ec55758e79bb'
    }
    url_potassium = 'https://platform.antares.id:8443/~/antares-cse/antares-id/interest/pota/la'
    url_phosphor = 'https://platform.antares.id:8443/~/antares-cse/antares-id/interest/phospor/la'
    url_nitrogen = 'https://platform.antares.id:8443/~/antares-cse/antares-id/interest/Nitrogen/la'
    url_ph = 'https://platform.antares.id:8443/~/antares-cse/antares-id/interest/ph/la'

    response_potassium = requests.get(url_potassium, headers=headers)
    response_phosphor = requests.get(url_phosphor, headers=headers)
    response_nitrogen = requests.get(url_nitrogen, headers=headers)
    response_ph = requests.get(url_ph, headers=headers)

    if response_potassium.status_code == 200 and response_phosphor.status_code == 200 and response_nitrogen.status_code == 200:
        data_potassium = response_potassium.json()
        potassium_value = data_potassium['m2m:cin']['con']
        potassium_value = potassium_value.strip("'")
        potassium_value = int(potassium_value)

        data_phosphor = response_phosphor.json()
        phosphor_value = data_phosphor['m2m:cin']['con']
        phosphor_value = phosphor_value.strip("'")
        phosphor_value = int(phosphor_value)

        data_nitrogen = response_nitrogen.json()
        nitrogen_value = data_nitrogen['m2m:cin']['con']
        nitrogen_value = nitrogen_value.strip("'")
        nitrogen_value = int(nitrogen_value)
        nitrogen_timestamp = data_nitrogen['m2m:cin']['ct']  # Mengambil timestamp

        data_ph = response_ph.json()
        ph_value = data_ph['m2m:cin']['con']
        ph_value = ph_value.strip("'")
        ph_value = int(ph_value) / 100  # Sesuaikan format nilai pH

        return {
            'potassium': potassium_value,
            'phosphor': phosphor_value,
            'nitrogen': nitrogen_value,
            'ph': ph_value,
            'nitrogen_timestamp': nitrogen_timestamp  # Menambahkan timestamp ke hasil
        }
    else:
        return {
            'potassium': 0,
            'phosphor': 0,
            'nitrogen': 0,
            'ph': 0,
            'nitrogen_timestamp': None  # Menambahkan timestamp ke hasil
        }

def predict_status(nitrogen, phospor, potassium):
    # Memuat model yang telah disimpan
    model = joblib.load('model.pkl')
    
    # Membuat DataFrame untuk data input
    data = pd.DataFrame([[nitrogen, phospor, potassium]], columns=['Nitrogen', 'Phospor', 'Potasium'])
    
    # Melakukan prediksi
    prediction = model.predict(data)
    
    # Mengembalikan hasil prediksi
    return 'Butuh Pupuk' if prediction[0] == 1 else 'Tidak Butuh Pupuk'

# Define routes
@app.route('/')
def index():
    title = 'Dashboard'
    hst = 10

    planting_time = get_planting_time()
    plant_age = calculate_plant_age(planting_time)
    npk_values = get_npk_values()
    prediction = predict_status(npk_values['nitrogen'], npk_values['phosphor'], npk_values['potassium'])
    
    # Simpan hasil prediksi ke dalam history
    save_prediction_history(prediction)

    return render_template('index.html', 
                           potassium=npk_values['potassium'], 
                           phosphor=npk_values['phosphor'], 
                           nitrogen=npk_values['nitrogen'], 
                           ph=npk_values['ph'], 
                           hst=hst, 
                           title=title, 
                           planting_time=planting_time, 
                           plant_age=plant_age,
                           prediction=prediction,
                           nitrogen_timestamp=npk_values['nitrogen_timestamp'])  # Menambahkan timestamp ke template

@app.route('/set_planting_time', methods=['POST'])
def set_planting_time():
    planting_time = request.json.get('planting_time')
    save_planting_time(planting_time)
    return jsonify({'status': 'success'})

@app.route('/get_npk_values', methods=['GET'])
def get_npk_values_route():
    npk_values = get_npk_values()
    return jsonify(npk_values)

@app.route('/get_prediction_history', methods=['GET'])
def get_prediction_history_route():
    history = get_prediction_history()
    return jsonify(history)

@app.route('/get_latest_timestamp', methods=['GET'])
def get_latest_timestamp():
    npk_values = get_npk_values()
    return jsonify({'nitrogen_timestamp': npk_values['nitrogen_timestamp']})

# Run the application
if __name__ == '__main__':

    port = int(os.environ.get('PORT', 5000))

    app.run(host='0.0.0.0', port=port, debug=False)