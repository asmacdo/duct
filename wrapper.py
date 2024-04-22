#!/usr/bin/env python3
import os
import subprocess
import time
import argparse

import duct


def get_processes_in_session(session_id):
    """Retrieve all PIDs belonging to the given session ID."""
    pids = []
    for pid in os.listdir('/proc'):
        if pid.isdigit():
            try:
                with open(os.path.join('/proc', pid, 'stat'), 'r') as f:
                    data = f.read().split()
                if int(data[5]) == session_id:  # Check session ID in stat file
                    pids.append(int(pid))
            except IOError:  # proc has already terminated
                continue
    return pids


def generate_subreport(session_id, elapsed_time, report_interval, report, subreport):
    """Monitor and log details about all processes in the given session."""
    if elapsed_time >= (subreport.number+1) * report_interval:
        print(subreport)
        report.subreports.append(subreport)
        subreport = duct.SubReport(subreport.number+1)

    pids = get_processes_in_session(session_id)
    for pid in pids:
        duct.pid_dummy_monitor(pid, elapsed_time, subreport)

    return subreport


def main(command, args, sample_interval, report_interval):
    """ A wrapper to execute a command, monitor and log the process details. """
    try:
        start_time = time.time()
        print(f"Starting at {start_time}...")
        process = subprocess.Popen([command] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)

        session_id = os.getsid(process.pid)  # Get session ID of the new process
        report = duct.Report()
        subreport = duct.SubReport()
        elapsed_time = 0

        while True:
            current_time = time.time()
            elapsed_time = current_time - start_time
            subreport = generate_subreport(session_id, elapsed_time, report_interval, report, subreport)
            if process.poll() is not None:  # the process has stopped
                break
            time.sleep(sample_interval)

        stdout, stderr = process.communicate()
        end_time = time.time()
        print(f"Command executed in {end_time - start_time:.2f} seconds.")
        print("STDOUT:", stdout.decode())
        print("STDERR:", stderr.decode())

    except Exception as e:
        print(f"Failed to execute command: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A process wrapper script that monitors the execution of a command.")
    parser.add_argument('command', help="The command to execute.")
    parser.add_argument('arguments', nargs='*', help="Arguments for the command.")
    parser.add_argument('--sample-interval', type=float, default=1.0, help="Interval in seconds between status checks of the running process.")
    parser.add_argument('--report-interval', type=float, default=60.0, help="Interval in seconds at which to report aggregated data.")

    args = parser.parse_args()
    main(args.command, args.arguments, args.sample_interval, args.report_interval)
