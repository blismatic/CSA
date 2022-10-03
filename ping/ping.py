import os
import pandas as pd
from datetime import datetime
from alive_progress import alive_it
from threading import Thread, Lock
import time
from colorama import init, Fore
import argparse
import sys


def main():
    start_time = time.time()
    init()  # Required for colorama to work

    # Handle argument parsing
    args = handleArguments()

    # Load the IPs from the .csv file
    ips_and_switches = loadIPs(args.input)

    # Create data structure to hold the results
    results = {
        "Dead": [],
        "Alive": []
    }

    # Create threads
    threads = [None] * len(ips_and_switches)
    lock = Lock()

    # Start threads
    for index, row in enumerate(ips_and_switches):
        ip, switch_name = row
        threads[index] = Thread(target=ping, args=(
            ip, switch_name, results, args, lock))
        threads[index].start()

    # Wait for the threads to complete
    bar = alive_it(threads, bar='classic', spinner='classic',
                   elapsed=False, stats=False)
    for t in bar:
        t.join()

    # Write the results to a new file
    if not args.no_outfile:
        out_file_name = f'{generateFileName()}.txt'
        writeToFile(f'./output/{out_file_name}', results)

    # Print a summary to the console
    summarize(results, time.time(), start_time)


def generateFileName():
    ct = datetime.now()
    return ct.strftime('%b %d %Y %I-%M-%S %p')


def handleArguments():
    parser = argparse.ArgumentParser(
        description='Ping a list of IPs, and return the results in a text file')
    parser.add_argument('input', nargs='?', metavar='file',
                        help='file to read IPs from', default='LAKEWOOD SWITCHES - Sheet1.csv')
    parser.add_argument('-nf', '--no_outfile',
                        action='store_true', help='do not generate a text file')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='only print the summary')

    return parser.parse_args()


def loadIPs(in_file_path):
    try:
        df = pd.read_csv(in_file_path)
    except FileNotFoundError:
        print(
            f'FileNotFoundError: The system cannot find the file specified: \'{Fore.CYAN}{in_file_path}{Fore.RESET}\'')
        sys.exit()

    print(
        f'Reading from \'{Fore.CYAN}{in_file_path}{Fore.RESET}\', last modified on {unixToReadable(os.path.getmtime(in_file_path))}')

    try:
        subset = df[['IP Address', 'Switch Name']
                    ][df['IP Address'].str.startswith('10.', na=False)]
    except:
        print(
            f'Something went wrong when trying to read from \'{Fore.CYAN}{in_file_path}{Fore.RESET}\'... are you sure it is formatted correctly?')
        sys.exit()

    ips_and_switches = list(
        subset.itertuples(index=False, name=None))

    return ips_and_switches


def writeToFile(file_name, dictionary):
    with open(file_name, 'a') as out_file:
        for status in dictionary:
            for result in dictionary[status]:
                ip, switch_name = result
                if status == 'Dead':
                    out_file.write(f'{status}, {ip} - {switch_name}\n')
                else:
                    out_file.write(f'{status}, {ip}\n')
            if (status == 'Dead' and len(dictionary[status])):
                out_file.write('\n')
    print(f'Results written to {Fore.CYAN}{file_name}{Fore.RESET}\n')


def ping(ip_address, switch_name, results_dict, args, lock):
    cmd_response = os.popen(f'ping {ip_address}').read().splitlines()
    cmd_response = [line.strip() for line in cmd_response]

    for line in cmd_response:
        if not line.startswith('Packets'):
            continue

        packet_loss_percent = line.split()[-2][1:-1]

        with lock:
            if packet_loss_percent == '100':
                results_dict['Dead'].append([ip_address, switch_name])
                if not args.quiet:
                    print(
                        f'[{Fore.RED}D{Fore.RESET}] {ip_address} - {Fore.RED}{switch_name}{Fore.RESET}\n')
            elif packet_loss_percent == '0':
                results_dict['Alive'].append([ip_address, switch_name])
                if not args.quiet:
                    print(f'[{Fore.GREEN}A{Fore.RESET}] {ip_address}\n')
            else:
                return 'ERROR'


def unixToReadable(timestamp):
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def summarize(dict, end_time, start_time):
    print((f'Summary: '
           f'{Fore.RED if len(dict["Dead"]) else Fore.RESET}'
           f'{len(dict["Dead"])} dead IP(s){Fore.RESET} | '
           f'{Fore.GREEN if len(dict["Alive"]) else Fore.RESET}'
           f'{len(dict["Alive"])} alive IP(s){Fore.RESET} | '
           f'Finished in {Fore.CYAN}{round(end_time - start_time, 1)} seconds{Fore.RESET}'))


if __name__ == '__main__':
    main()
