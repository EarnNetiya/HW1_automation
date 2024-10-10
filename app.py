from flask import Flask, request, session, redirect, url_for, render_template, flash
from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException
import os,json

app = Flask(__name__)
app.secret_key = 'phatkawee' 

DEVICE_FILE = 'devices.json'


def load_devices():
    if not os.path.exists(DEVICE_FILE):
        return []  
    with open(DEVICE_FILE, 'r') as f:
        return json.load(f)

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
    devices = load_devices() 
    
    if request.method == 'POST':
        if 'add' in request.form:
            hostname = request.form.get('device_name') 
            ip = request.form.get('ipaddress') 
            username = request.form.get('username')  
            password = request.form.get('password')  
            
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
                
                try:
                    connection = ConnectHandler(**device)
                    connection.disconnect()
                   
                    devices.append({
                        'device_type': 'cisco_ios',
                        'hostname': hostname, 
                        'ip': ip,
                        'username': username,
                        'password': password,
                    })
                    save_devices(devices) 
                    flash(f'Device "{hostname}" with IP "{ip}" added successfully!', 'success')
                except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
                    flash(f'Failed to connect to device with IP "{ip}": {str(e)}', 'error')

        elif 'delete' in request.form:
            device_to_delete_ip = request.form.get('ipaddress', None)  

            if device_to_delete_ip:
                original_length = len(devices)
                devices = [d for d in devices if d.get('ip') != device_to_delete_ip]

                if len(devices) < original_length:
                    save_devices(devices) 
                    flash(f'Device with IP "{device_to_delete_ip}" deleted successfully!', 'success')
                else:
                    flash(f'Device with IP "{device_to_delete_ip}" not found!', 'error')
            else:
                flash('IP address not provided for deletion.', 'error')

    return render_template('add_device.html', devices=devices)


@app.route('/configurations', methods=["GET", "POST"])
def configurations():
    devices = load_devices()  
    
    if request.method == "POST":
        selected_device = request.form.get('selected_device')  
        device_info = next((d for d in devices if d.get('ip') == selected_device), None)

        if not device_info:
            flash("Selected device not found!", "error")
            return redirect(url_for('configurations'))

        if 'device_type' not in device_info:
            flash("Device type is missing in device information!", "error")
            return redirect(url_for('configurations'))

        action = request.form.get('action')  
        vlan_id = request.form.get('vlan_id')
        vlan_name = request.form.get('vlan_name')
        vlan_id_delete = request.form.get('vlan_id_delete') 
        interface = request.form.get('interface') 
        ip_address = request.form.get('ip_address')  
        no_ip_address = request.form.get('no_ip_address')
        subnet_mask = request.form.get('subnet_mask')
        default_gateway  = request.form.get('default_gateway')
        line_type = request.form.get('line_type')
        transport_protocol = request.form.get('transport_protocol')
        default_route = request.form.get('default_route')
        subnet_mask = request.form.get('subnet_mask')
        switchport = request.form.get('switchport')
        noswitchport = request.form.get('noswitchport')
        no_subnet_mask = request.form.get('no_subnet_mask')
        no_interface = request.form.get('no_interface')
        interface_name = request.form.get('interface_name')
        vlan_number = request.form.get('vlan_number')
        mode1 = request.form.get('mode1')
        mode1 = request.form.get('mode1')
        mode2 = request.form.get('mode2')
        no_vlan_number = request.form.get('no_vlan_number')
        no_interface_name = request.form.get('no_interface_name')
        no_default_route = request.form.get('no_default_route')
        destination_network_static = request.form.get('destination_network_static')
        subnet_mask_static = request.form.get('subnet_mask_static')
        next_hop_static = request.form.get('next_hop_static')
        no_destination_network_static = request.form.get('no_destination_network_static')
        no_subnet_mask_static = request.form.get('no_subnet_mask_static')
        no_next_hop_static = request.form.get('no_next_hop_static')
        ospf_id = request.form.get('ospf_id')
        no_ospf_id = request.form.get('no_ospf_id')
        network_ospf = request.form.get('network_ospf')
        wildcard_ospf = request.form.get('wildcard_ospf')
        version_rip = request.form.get('version_rip')
        network_rip = request.form.get('network_rip')
        
        
        
        try:
            connection_params = {
                'device_type': device_info['device_type'],
                'ip': device_info['ip'],
                'username': device_info['username'],
                'password': device_info['password'],
            }

            net_connect = ConnectHandler(**connection_params)  
            net_connect.enable() 

            if action == 'vlan_config':
                    config_commands = [
                        f'vlan {vlan_id}',
                        f'name {vlan_name}',
                        'exit', 
                        'end', 
                        'show vlan'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'delete_vlan': 
                    config_commands = [
                        f'no vlan {vlan_id_delete}',
                        'end',
                        'show vlan'
                    ]
                    output = net_connect.send_config_set(config_commands)
                    
            elif action == 'interface_config':
                    config_commands = [
                        f'interface {interface}',
                        f'ip address {ip_address} {subnet_mask}',
                        'no shutdown',
                        'end',
                        'show ip interface brief'
                    ]

                    if noswitchport == 'yes':
                        config_commands.insert(1, 'no switchport')

                    output = net_connect.send_config_set(config_commands)

            elif action == 'no_ipaddress':              
                    config_commands = [
                        f'interface {no_interface}',
                        f'no ip address {no_ip_address} {no_subnet_mask}',  
                        'no shutdown',
                        'end',
                        'show ip interface brief'
                    ]
                    
                    if switchport == 'yes': 
                        config_commands.insert(4, 'switchport')
                    
                    output = net_connect.send_config_set(config_commands)


            elif action == 'sw_mode':
                config_commands = [
                        f'interface {interface_name}',
                        'switchport trunk encapsulation dot1q',
                        f'switchport mode {mode1}',
                        f'switchport access vlan {vlan_number}',
                        'end',
                        'show vlan brief',
                        'show interface trunk'
                    ]

                # if switchport == 'yes':
                #     config_commands.insert(1, 'switchport')  

                output = net_connect.send_config_set(config_commands)
                    
                    
            elif action == 'no_sw_mode':
                config_commands = [
                        f'interface {no_interface_name}',
                        'no switchport trunk encapsulation dot1q',
                        'no switchport mode trunk',
                        f'no switchport mode {mode2}',
                        f'no switchport access vlan {no_vlan_number}',
                        'end',
                        'show vlan brief',
                        'show interface trunk'
                    ]
                
                # if noswitchport == 'yes':
                #     config_commands.insert(1, 'no switchport')  

                output = net_connect.send_config_set(config_commands)

            elif action == 'ip_default_gateway':
                    config_commands = [
                        f'ip default-gateway {default_gateway}',
                        'end',
                        'show running-config | include ip default-gateway'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'no_ip_default_gateway':
                config_commands = [
                    'no ip default-gateway',
                    'end',
                    'show running-config | include ip default-gateway'
                ]
                output = net_connect.send_config_set(config_commands)

            elif action == 'vty_line_config':
                if line_type in ['0 4', '5 15'] and transport_protocol in ['telnet', 'ssh', 'all']:
                    config_commands = [
                        f'line vty {line_type}',
                        f'transport input {transport_protocol}',  
                        'login local',
                        'exit',
                        'end',
                        'show running-config | include line vty'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'default_route':
                    config_commands = [
                        f'ip route {default_route}',
                        'end',
                        'show ip route'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'no_default_route':
                    config_commands = [
                        f'no ip route {no_default_route}',
                        'end',
                        'show ip route'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'static_routes':
                    config_commands = [
                        f'ip route {destination_network_static} {subnet_mask_static} {next_hop_static}',
                        'end',
                        'show ip route static'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'no_static':
                    config_commands = [
                        f'no ip route {no_destination_network_static} {no_subnet_mask_static} {no_next_hop_static}',
                        'end', 
                        'show ip route static'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'ospf_config':
                    config_commands = [
                        'ip routing',
                        f'router ospf {ospf_id}',
                        f'network {network_ospf} {wildcard_ospf} area 0', 
                        'exit',
                        'end',
                        'show ip ospf'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'no_ospf':
                    config_commands = [
                        f'no router ospf {no_ospf_id}',
                        'end',
                        'show ip ospf'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'rip_config':
                    config_commands = [
                        'router rip',
                        f'version {version_rip}',
                        'no auto-summary',
                        f'network {network_rip}',
                        'exit',
                        'end',
                        'show ip route rip'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'no_rip':
                config_commands = [
                    'no router rip',
                    'end',
                    'show ip route rip'
                ]
                output = net_connect.send_config_set(config_commands)

            else:
                output = "Invalid action."
                    
            
            net_connect.disconnect()

            return render_template('configurations.html', output=output)

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for('configurations'))

    return render_template('configurations.html', devices=devices)


@app.route('/show_configs', methods=["GET", "POST"])
def show_configs():
    devices = load_devices()  

    if request.method == "POST":
        selected_device = request.form.get('selected_device')  
        device_info = next((d for d in devices if d.get('ip') == selected_device), None)

        if not device_info:
            flash("Selected device not found!", "error")
            return redirect(url_for('show_configs'))

        try:
            connection_params = {
                'device_type': device_info['device_type'],
                'ip': device_info['ip'],
                'username': device_info['username'],
                'password': device_info['password'],
            }

            net_connect = ConnectHandler(**connection_params)  
            net_connect.enable() 

            show_commands = []
            if request.form.get('show_run'):
                show_commands.append('show running-config')
            if request.form.get('show_ip_int_brief'):
                show_commands.append('show ip interface brief')
            if request.form.get('show_version'):
                show_commands.append('show version')
            if request.form.get('show_interface'):
                show_commands.append('show interfaces')
            if request.form.get('show_vlan'):
                show_commands.append('show vlan brief')
            if request.form.get('show_interface_trunk'):
                show_commands.append('show interface trunk')
            if request.form.get('show_ip_route'):
                show_commands.append('show ip route')
            if request.form.get('show_ip_ospf'):
                show_commands.append('show ip ospf')
            if request.form.get('show_ip_rip'):
                show_commands.append('show ip route rip')
            if request.form.get('show_ip_protocol'):
                show_commands.append('show ip protocol')

            output = ""
            for command in show_commands:
                output += f"\nCommand: {command}\n"
                result = net_connect.send_command(command)
                output += result + "\n"

            net_connect.disconnect()

            return render_template('show_configs.html', devices=devices, output=output)

        except Exception as e:
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for('show_configs'))

    return render_template('show_configs.html', devices=devices)



if __name__ == '__main__':
    app.run(debug=True)
