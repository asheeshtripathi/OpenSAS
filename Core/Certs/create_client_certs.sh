#!/bin/bash

# Prompt for the client's hostname or IP address
echo -n "Enter the client's hostname or IP address: "
read client_name

# Set the subject for the client certificate
client_subject="/C=US/ST=California/L=San Francisco/O=My Client/CN=$client_name"

i=0
while true; do
  # Generate the client private key
  key_file="client_$client_name-$i.key"
  if [ ! -f "$key_file" ]; then
    openssl genpkey -algorithm RSA -out "$key_file"
    break
  fi
  i=$((i + 1))
done

i=0
while true; do
  # Generate the client certificate signing request (CSR)
  csr_file="client_$client_name-$i.csr"
  if [ ! -f "$csr_file" ]; then
    openssl req -new -key "$key_file" -out "$csr_file" -subj "$client_subject"
    break
  fi
  i=$((i + 1))
done

i=0
while true; do
  # Sign the client certificate with the CA
  crt_file="client_$client_name-$i.crt"
  if [ ! -f "$crt_file" ]; then
    openssl x509 -req -in "$csr_file" -CA ca.crt -CAkey ca.key -CAcreateserial -out "$crt_file"
    break
  fi
  i=$((i + 1))
done

# Print the names of the saved certificates
echo "Client private key: $key_file"
echo "Client certificate: $crt_file"
