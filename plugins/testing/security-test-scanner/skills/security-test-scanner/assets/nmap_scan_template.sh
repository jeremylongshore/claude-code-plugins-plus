#!/bin/bash

# Script Name: nmap_scan_template.sh
# Description: Template script for running Nmap scans with various options.
# Author: [Your Name/Organization]
# Date: 2023-10-27

# Exit immediately if a command exits with a non-zero status.
set -e

# Usage Instructions:
# ./nmap_scan_template.sh <target_ip_or_hostname> [options]
#
# Options:
#   -p <port(s)>: Specify port(s) to scan (e.g., -p 80,443 or -p 1-1000)
#   -sV: Enable version detection
#   -sS: TCP SYN scan (default)
#   -sT: TCP connect scan (if SYN scan is not possible)
#   -sU: UDP scan
#   -O: Enable OS detection
#   -A: Enable aggressive scan (OS detection, version detection, script scanning, and traceroute)
#   -T<0-5>: Set timing template (0=paranoid, 1=sneaky, 2=polite, 3=normal, 4=aggressive, 5=insane)
#   -oN <output_file>: Output results to a normal format file
#   -oX <output_file>: Output results to an XML format file
#   -h: Display this help message

# Default values
TARGET=""
PORTS=""
SCAN_TYPE=""
VERSION_DETECTION=""
OS_DETECTION=""
AGGRESSIVE_SCAN=""
TIMING_TEMPLATE=""
OUTPUT_NORMAL=""
OUTPUT_XML=""

# Function to display usage instructions
usage() {
  echo "Usage: ./nmap_scan_template.sh <target_ip_or_hostname> [options]"
  echo
  echo "Options:"
  echo "  -p <port(s)>: Specify port(s) to scan (e.g., -p 80,443 or -p 1-1000)"
  echo "  -sV: Enable version detection"
  echo "  -sS: TCP SYN scan (default)"
  echo "  -sT: TCP connect scan (if SYN scan is not possible)"
  echo "  -sU: UDP scan"
  echo "  -O: Enable OS detection"
  echo "  -A: Enable aggressive scan (OS detection, version detection, script scanning, and traceroute)"
  echo "  -T<0-5>: Set timing template (0=paranoid, 1=sneaky, 2=polite, 3=normal, 4=aggressive, 5=insane)"
  echo "  -oN <output_file>: Output results to a normal format file"
  echo "  -oX <output_file>: Output results to an XML format file"
  echo "  -h: Display this help message"
  exit 1
}

# Parse command-line arguments
while getopts "p:sVsTUAOTo:o:h" opt; do
  case "$opt" in
    p)
      PORTS="-p $OPTARG"
      ;;
    s)
      VERSION_DETECTION="-sV"
      ;;
    S)
      SCAN_TYPE="-sS"
      ;;
    T)
      SCAN_TYPE="-sT"
      ;;
    U)
      SCAN_TYPE="-sU"
      ;;
    O)
      OS_DETECTION="-O"
      ;;
    A)
      AGGRESSIVE_SCAN="-A"
      ;;
    T)
      TIMING_TEMPLATE="-T$OPTARG"
      ;;
    o)
      OUTPUT_NORMAL="-oN $OPTARG"
      ;;
    O)
      OUTPUT_XML="-oX $OPTARG"
      ;;
    h)
      usage
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      usage
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      usage
      ;;
  esac
done

# Shift off the options, leaving the arguments
shift $((OPTIND-1))

# Check for the target IP or hostname
if [ -z "$1" ]; then
  echo "Error: Target IP or hostname is required."
  usage
fi

TARGET="$1"

# Construct the Nmap command
NMAP_COMMAND="nmap $PORTS $SCAN_TYPE $VERSION_DETECTION $OS_DETECTION $AGGRESSIVE_SCAN $TIMING_TEMPLATE $OUTPUT_NORMAL $OUTPUT_XML $TARGET"

# Print the Nmap command (for debugging)
echo "Running command: $NMAP_COMMAND"

# Execute the Nmap command
eval $NMAP_COMMAND

echo "Nmap scan completed."

exit 0