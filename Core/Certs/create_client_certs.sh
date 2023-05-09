#!/bin/bash

# Prompt for the client's hostname or IP address
echo -n "Enter the client's hostname or IP address: "
read client_name

# Set the subject for the client certificate
client_subject="/C=US/ST=California/L=San Francisco/O=My Client/CN=$client_name"

# Create a temporary openssl.cnf with the client_name
openssl_cnf="openssl_${client_name}.cnf"
cp openssl_client.cnf "$openssl_cnf"
sed -i 's/\$client_name/'"$client_name"'/g' "$openssl_cnf"

i=0
while true; do
  # Generate the client private key
  key_file="client_${client_name}-${i}.key"
  if [ ! -f "$key_file" ]; then
    openssl genpkey -algorithm RSA -out "$key_file"
    break
  fi
  i=$((i + 1))
done

i=0
while true; do
  # Generate the client certificate signing request (CSR)
  csr_file="client_${client_name}-${i}.csr"
  if [ ! -f "$csr_file" ]; then
    openssl req -new -key "$key_file" -out "$csr_file" -subj "$client_subject" -config "$openssl_cnf"
    break
  fi
  i=$((i + 1))
done

i=0
while true; do
  # Sign the client certificate with the CA
  crt_file="client_${client_name}-${i}.crt"
  if [ ! -f "$crt_file" ]; then
    openssl x509 -req -in "$csr_file" -CA ca.crt -CAkey ca.key -CAcreateserial -out "$crt_file" -extfile "$openssl_cnf" -extensions v3_req
    break
  fi
  i=$((i + 1))
done

# Ask the user if they want to save the client and CA certificates as a tar.gz file
while true; do
  echo -n "Do you want to save the client and CA certificates as a tar.gz file? (y/n): "
  read save_tar
  case $save_tar in
    [Yy]* )
      tar_file="certs_${client_name}.tar.gz"
      tar -czf "$tar_file" "$key_file" "$crt_file" "ca.crt"
      echo "Client and CA certificates saved as $tar_file"
      # Delete the generated files and the CSR file
      rm -f "$key_file" "$crt_file" "$csr_file" "$openssl_cnf"
      break
      ;;
    [Nn]* )
      echo "Client private key: $key_file"
      echo "Client certificate: $crt_file"
      echo "CA certificate: ca.crt"
      # Delete the temporary openssl.cnf
      rm -f "$openssl_cnf"
      break
      ;;
    * )
      echo "Please answer y or n."
      ;;
  esac
done
