from flask import Flask, render_template
import requests

# Create the Flask application instance
app = Flask(__name__)

# Define routes
@app.route('/')
def index():
    title = 'Dashboard'
    # Lakukan GET request ke API
    headers = {
        'X-M2M-Origin': '44dbb85550128192:c079ec55758e79bb'
    }
    url_potassium = 'https://platform.antares.id:8443/~/antares-cse/antares-id/interest/pota/la'
    url_phosphor = 'https://platform.antares.id:8443/~/antares-cse/antares-id/interest/phospor/la'
    url_nitrogen = 'https://platform.antares.id:8443/~/antares-cse/antares-id/interest/Nitrogen/la'
    hst = 10
    response_potassium = requests.get(url_potassium, headers=headers)
    response_phosphor = requests.get(url_phosphor, headers=headers)
    response_nitrogen = requests.get(url_nitrogen, headers=headers)

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

        return render_template('index.html', potassium=potassium_value, phosphor=phosphor_value, nitrogen=nitrogen_value, hst=hst, title=title)
    else:
        return render_template('index.html', title=title, potassium=0, phosphor=0, nitrogen=0)

# Run the application
if __name__ == '__main__':
    app.run(debug=False)
