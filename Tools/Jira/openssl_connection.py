#!/usr/bin/python3
import subprocess
import random
import time
import sys

scale = 250
fb  = 2
openssl_ver = '-tls1_3'
cipher_all = ['X25519', 'X448', 'secp521r1', 'brainpoolP512r1', 'p521_hqc256', 'p384_hqc192', \
               'kyber768','kyber1024', 'bikel1', 'kyber90s1024', 'p256_hqc128', 'p256_kyber512', \
               'p384_kyber768', 'kyber512', 'hqc192', 'X25519:p256_hqc128:hqc192', 'kyber768:X448:p384_hqc192', \
               'kyber1024:secp521r1:p256_hqc128', 'hqc192:p384_kyber768:brainpoolP512r1', 'bikel1:p521_hqc256:X25519']
uip = 'NoNo'

for i in range(2, scale):
    if fb == 255:
        fb = 5
    kex = random.choice(cipher_all)
    try:
        print("TRYING.....")
        args_line = 'echo -e "GET /home/paloalto/OPENSSL_DIR/index.html HTTP/1.1" | \
        openssl s_client -CAfile /home/paloalto/PA.pem -bind 192.168.30.{0} \
        -curves {1} -connect www.pqc01.com {2}'.format(fb,kex,openssl_ver)
    except:
        print("EXCEPT.....")
        args_line = 'echo -e "GET /home/test/openssl/index.html HTTP/1.1" | \
        openssl s_client -CAfile /home/paloalto/PA.pem -bind 192.168.30.2 \
        -curves {1} -connect www.pqc01.com {2}'.format(fb,kex,openssl_ver)
    subprocess.run(args_line, shell=True)
    fb += 1