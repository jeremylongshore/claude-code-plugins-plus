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
  echo "  -V: Enable version detection (-sV)"
  echo "  -y <S|T|U>: Scan type — S=SYN (default), T=TCP-connect, U=UDP"
  echo "  -A: Enable aggressive scan (OS, version, script, traceroute)"
  echo "  -O: Enable OS detection"
  echo "  -t <0-5>: Timing template (0=paranoid, 5=insane)"
  echo "  -n <output_file>: Normal-format output (-oN)"
  echo "  -x <output_file>: XML-format output (-oX)"
  echo "  -h: Display this help message"
  exit 1
}

# Parse command-line arguments.
#
# Spec key (single-byte flags only — `getopts` doesn't support repeats, so
# each scan-type / output-format gets its own letter):
#   -p PORTS    port spec
#   -V          enable version detection (-sV)
#   -y TYPE     scan type, one of: S (SYN), T (TCP-connect), U (UDP)
#   -A          aggressive scan
#   -O          OS detection
#   -t N        timing template 0-5
#   -n FILE     normal-format output (-oN)
#   -x FILE     XML-format output (-oX)
#   -h          show help
while getopts "p:Vy:AOt:n:x:h" opt; do
  case "$opt" in
    p) PORTS="-p $OPTARG" ;;
    V) VERSION_DETECTION="-sV" ;;
    y)
      case "$OPTARG" in
        S) SCAN_TYPE="-sS" ;;
        T) SCAN_TYPE="-sT" ;;
        U) SCAN_TYPE="-sU" ;;
        *)
          echo "Invalid scan type: $OPTARG (use S/T/U)" >&2
          usage
          ;;
      esac
      ;;
    A) AGGRESSIVE_SCAN="-A" ;;
    O) OS_DETECTION="-O" ;;
    t) TIMING_TEMPLATE="-T$OPTARG" ;;
    n) OUTPUT_NORMAL="-oN $OPTARG" ;;
    x) OUTPUT_XML="-oX $OPTARG" ;;
    h) usage ;;
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