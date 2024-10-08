from flask import Flask, request, session, redirect, url_for, render_template, flash
from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException
import os,json

app = Flask(__name__)
app.secret_key = 'phatkawee' 

DEVICE_FILE = 'devices.json'

#   load device from devices.JSON
def load_devices():
    if not os.path.exists(DEVICE_FILE):
        return []  
    with open(DEVICE_FILE, 'r') as f:
        return json.load(f)

#   save devices.JSON
def save_devices(devices):
    with open(DEVICE_FILE, 'w') as f:
        json.dump(devices, f, indent=4)

            
@app.route('/')
def index():
        return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        session['username'] = username
        session['password'] = password
        flash('Login successful!', 'success')
        return redirect(url_for('add_device'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))


@app.route('/add_device', methods=['GET', 'POST'])
def add_device():
    devices = load_devices()  # โหลดอุปกรณ์จากไฟล์ JSON
    
    if request.method == 'POST':
        if 'add' in request.form:
            hostname = request.form.get('device_name')  # ชื่อโฮสต์
            ip = request.form.get('ipaddress')  # IP address
            username = request.form.get('username')  # ชื่อผู้ใช้
            password = request.form.get('password')  # รหัสผ่าน
            
            if not hostname or not ip or not username or not password:
                flash('All fields are required.', 'error')
                return render_template('add_device.html', devices=devices)

            existing_device = next((d for d in devices if d.get('ip') == ip), None)

            if existing_device:
                flash(f'Device with IP "{ip}" already exists!', 'error')
            else:
                device = {
                    'device_type': 'cisco_ios',
                    'ip': ip,
                    'username': username,
                    'password': password,
                }
                
                # ตรวจสอบการเชื่อมต่อกับอุปกรณ์ก่อนที่จะบันทึก
                try:
                    connection = ConnectHandler(**device)
                    connection.disconnect()
                    # ถ้าการเชื่อมต่อสำเร็จให้บันทึกอุปกรณ์
                    devices.append({
                        'device_type': 'cisco_ios',
                        'hostname': hostname, 
                        'ip': ip,
                        'username': username,
                        'password': password,
                    })
                    save_devices(devices)  # บันทึกอุปกรณ์ทั้งหมด
                    flash(f'Device "{hostname}" with IP "{ip}" added successfully!', 'success')
                except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
                    flash(f'Failed to connect to device with IP "{ip}": {str(e)}', 'error')

        elif 'delete' in request.form:
            device_to_delete_ip = request.form.get('ipaddress', None)  # ใช้ IP address สำหรับการลบ

            if device_to_delete_ip:
                original_length = len(devices)
                devices = [d for d in devices if d.get('ip') != device_to_delete_ip]

                if len(devices) < original_length:
                    save_devices(devices)  # บันทึกหลังจากลบอุปกรณ์
                    flash(f'Device with IP "{device_to_delete_ip}" deleted successfully!', 'success')
                else:
                    flash(f'Device with IP "{device_to_delete_ip}" not found!', 'error')
            else:
                flash('IP address not provided for deletion.', 'error')

    return render_template('add_device.html', devices=devices)


@app.route('/configurations', methods=["GET", "POST"])
def configurations():
    devices = load_devices()  # โหลดอุปกรณ์จากไฟล์ JSON

    if request.method == "POST":
        selected_device = request.form.get('selected_device')  # ดึง IP ของอุปกรณ์ที่เลือก
        device_info = next((d for d in devices if d.get('ip') == selected_device), None)

        if not device_info:
            flash("Selected device not found!", "error")
            return redirect(url_for('configurations'))

        # ตรวจสอบว่ามี device_type ก่อนจะเชื่อมต่อ
        if 'device_type' not in device_info:
            flash("Device type is missing in device information!", "error")
            return redirect(url_for('configurations'))

        action = request.form.get('action')  # ดึง action จากฟอร์ม
        vlan_id = request.form.get('vlan_number')  # สำหรับการสร้าง VLAN
        vlan_id_delete = request.form.get('vlan_number_delete')  # สำหรับการลบ VLAN

        try:
            connection_params = {
                'device_type': device_info['device_type'],
                'ip': device_info['ip'],
                'username': device_info['username'],
                'password': device_info['password'],
            }

            net_connect = ConnectHandler(**connection_params)  # เชื่อมต่อกับอุปกรณ์
            net_connect.enable()  # เข้าสู่โหมด enable

            # ตรวจสอบว่า action คือ vlan_config หรือ delete_vlan
            if action == 'vlan_config':
                if vlan_id and request.form.get('vlan_name'):
                    vlan_name = request.form.get('vlan_name')
                    config_commands = [
                        f'vlan {vlan_id}',
                        f'name {vlan_name}',
                        'exit', 
                        'end', 
                        'show vlan'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'delete_vlan':
                if vlan_id_delete:  # เช็คว่ามี vlan_id_delete ที่รับมาหรือไม่
                    config_commands = [
                        f'no vlan {vlan_id_delete}',
                        'end',
                        'show vlan'
                    ]
                    output = net_connect.send_config_set(config_commands)
                else:
                    output = "VLAN ID is required for deletion."
                    
            

            net_connect.disconnect()

            return render_template('configurations.html', output=output)

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for('configurations'))

    return render_template('configurations.html', devices=devices)



if __name__ == '__main__':
    app.run(debug=True)
