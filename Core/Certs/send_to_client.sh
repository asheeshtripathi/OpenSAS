#!/bin/bash

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "sshpass is not installed. Installing now..."
    sudo apt-get update
    sudo apt-get install -y sshpass
fi

# Find .tar.gz files in the current directory
tar_files=( $(find . -maxdepth 1 -type f -name "*.tar.gz") )

# Check if any .tar.gz files were found
if [ ${#tar_files[@]} -eq 0 ]; then
  echo "No .tar.gz files found in the current directory."
  exit 1
fi

# Print the found .tar.gz files
echo "Found the following .tar.gz files in the current directory:"
for (( i=0; i<${#tar_files[@]}; i++ )); do
  echo "[$((i+1))] ${tar_files[i]}"
done

# Prompt the user to select a file
while true; do
  echo -n "Enter the number of the file you want to send: "
  read file_number
  if [[ $file_number =~ ^[0-9]+$ ]] && (( file_number > 0 )) && (( file_number <= ${#tar_files[@]} )); then
    break
  else
    echo "Invalid file number. Please enter a number between 1 and ${#tar_files[@]}."
  fi
done

# Get the selected file and its name
selected_file="${tar_files[file_number-1]}"
selected_file_name=$(basename "$selected_file")

# Extract the remote hostname from the selected file name, if it exists
remote_hostname_regex="^certs_([^_]+)\.tar\.gz$"
if [[ $selected_file_name =~ $remote_hostname_regex ]]; then
  default_remote_hostname="${BASH_REMATCH[1]}"
else
  default_remote_hostname=""
fi

# Prompt the user for the remote user, hostname, password, and path
echo -n "Enter the remote user: "
read remote_user
echo -n "Enter the remote hostname [${default_remote_hostname}]: "
read remote_hostname
remote_hostname=${remote_hostname:-$default_remote_hostname}
echo -n "Enter the remote password: "
read -s remote_password
echo ""
echo -n "Enter the remote directory where the file should be placed: "
read remote_directory

# Send the selected file to the remote host using scp
echo "Sending $selected_file_name to $remote_hostname ..."
sshpass -p "$remote_password" scp "$selected_file" "${remote_user}@${remote_hostname}:${remote_directory}"

# Log in to the remote host using ssh and extract the files
echo "Logging in to $remote_hostname and extracting files ..."

# Check if the remote directory exists, and create it if it doesn't
if sshpass -p "$remote_password" ssh "${remote_user}@${remote_hostname}" "[ -d \"$remote_directory\" ]"; then
  echo "Remote directory already exists."
else
  echo "Remote directory does not exist. Creating $remote_directory ..."
  sshpass -p "$remote_password" ssh "${remote_user}@${remote_hostname}" "mkdir -p $remote_directory"
fi

# Extract the files using tar
sshpass -p "$remote_password" ssh "${remote_user}@${remote_hostname}" "cd ${remote_directory} && tar -xzf ${selected_file_name}"

echo "Done."
