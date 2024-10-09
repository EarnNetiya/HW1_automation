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
        vlan_id = request.form.get('vlan_number')
        vlan_id_delete = request.form.get('vlan_number_delete') 
        interface = request.form.get('interface') 
        ip_address = request.form.get('ip_address')  
        subnet_mask = request.form.get('subnet_mask')
        default_gateway  = request.form.get('default_gateway')
        line_type = request.form.get('line_type')
        transport_protocol = request.form.get('transport_protocol')
        routing_protocol = request.form.get('routing_protocol')
        default_route = request.form.get('default_route')
        destination_network = request.form.get('destination_network')
        subnet_mask = request.form.get('subnet_mask')
        next_hop = request.form.get('next_hop')
        process_id = request.form.get('process_id')
        network = request.form.get('network')
        wildcard_mask = request.form.get('wildcard_mask')
        version = request.form.get('version')

        
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
                if vlan_id_delete:  
                    config_commands = [
                        f'no vlan {vlan_id_delete}',
                        'end',
                        'show vlan'
                    ]
                    output = net_connect.send_config_set(config_commands)
                else:
                    output = "VLAN ID is required for deletion."
                    
            elif action == 'interface_config':
                if interface and ip_address and subnet_mask:
                    config_commands = [f'interface {interface}']

                    # Check if the hostname exists in device_info and if it starts with 'R'
                    hostname = device_info.get('hostname')  # Get the hostname from device_info
                    if hostname:
                        # If hostname does not start with 'R', add 'no switchport'
                        if not hostname.startswith('R'):
                            config_commands.append('no switchport')

                    # Continue with the IP configuration commands
                    config_commands.extend([
                        f'ip address {ip_address} {subnet_mask}',  
                        'no shutdown',
                        'exit',
                        'end',
                        'show ip interface brief'
                    ])
                    
                    output = net_connect.send_config_set(config_commands, read_timeout=10)

                    # Update the device IP in device_info and save the changes
                    device_info['ip'] = ip_address  
                    save_devices(devices)

                    
            elif action == 'no_ipaddress':
                if interface:
                    config_commands = [
                        f'interface {interface}',
                        f'no {ip_address} {subnet_mask}',
                        'exit'
                        'end',
                        'show ip interface brief'
                    ]
                    output = net_connect.send_config_set(config_commands)
                    device_info['ip'] = ip_address  # Update the IP in device_info
                    save_devices(devices)
                    
            elif action == 'switchport_access_vlan':
                if interface and vlan_id:
                    config_commands = [
                        f'interface {interface}',
                        f'switchport access vlan {vlan_id}',
                        'exit',
                        'end',
                        'show running-config interface ' + interface
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'no_switchport_access_vlan':
                if interface:
                    config_commands = [
                        f'interface {interface}',
                        'no switchport access vlan',
                        'exit',
                        'end',
                        'show running-config interface ' + interface
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'ip_default_gateway':
                if default_gateway:
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
                if line_type in ['0 4', '5 15'] and transport_protocol in ['telnet', 'ssh']:
                    config_commands = [
                        f'line vty {line_type}',
                        f'transport input {transport_protocol}',  
                        'login local',
                        'exit',
                        'end',
                        'show running-config | include line vty'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'routing_config':
                if routing_protocol:
                    config_commands = [
                        f'router {routing_protocol}',
                        'exit',
                        'end',
                        'show ip route'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'no_routing':
                if routing_protocol:
                    config_commands = [
                        f'no router {routing_protocol}',
                        'end',
                        'show ip route'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'default_route':
                if default_route:
                    config_commands = [
                        f'ip route {default_route}',
                        'end',
                        'show ip route'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'no_default_route':
                if default_route:
                    config_commands = [
                        f'no ip route {default_route}',
                        'end',
                        'show ip route'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'static_routes':
                if destination_network and subnet_mask and next_hop:
                    config_commands = [
                        f'ip route {destination_network} {subnet_mask} {next_hop}',
                        'end',
                        'show ip route'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'no_static':
                if destination_network and subnet_mask:
                    config_commands = [
                        f'no ip route {destination_network} {subnet_mask}',
                        'end',
                        'show ip route'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'ospf_config':
                if process_id and network and wildcard_mask:
                    config_commands = [
                        f'router ospf {process_id}',
                        f'network {network} {wildcard_mask} area 0', 
                        'exit',
                        'end',
                        'show ip ospf'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'no_ospf':
                if process_id:
                    config_commands = [
                        f'no router ospf {process_id}',
                        'end',
                        'show ip ospf'
                    ]
                    output = net_connect.send_config_set(config_commands)

            elif action == 'rip_config':
                if version and network:
                    config_commands = [
                        'router rip',
                        f'version {version}',
                        f'network {network}',
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



if __name__ == '__main__':
    app.run(debug=True)
