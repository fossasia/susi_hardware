from flask import Flask , render_template
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/install')
def install():
    return 'starting the installation script'

@app.route('/config/<stt>/<tts>/<hotword>/<wake>')
def config(stt, tts, hotword, wake):
    subprocess.call('sudo ./config.sh {} {} {} {}'.format(stt,tts,hotword,wake), shell=True)  #nosec #pylint-disable type: ignore
    return 'Done' # pylint-enable

@app.route('/auth/<auth>/<email>/<passwd>')
def login(auth, email, passwd):
    subprocess.call('sudo ./login.sh {} {} {}'.format(auth, email,passwd), shell=True) #nosec #pylint-disable type: ignore
    return 'Authenticated' # pylint-enable

@app.route('/wifi_credentials/<wifissid>/<wifipassd>')
def wifi_config(wifissid,wifipassd):
    wifi_ssid = wifissid
    wifi_password = wifipassd
    subprocess.call('sudo ./home/pi/SUSI.AI/susi_linux/access_point/wifi_search.sh {} {}'.format(wifi_ssid,wifi_password), shell=True)  #nosec #pylint-disable type: ignore
    return 'Wifi Configured' # pylint-enable

if __name__ == '__main__':
    app.run(debug=False,host= '0.0.0.0') #nosec #pylint-disable type: ignore
    # pylint-enable
    # to allow the server to be accessible by any device on the network/access point #pylint-disable type: ignore
