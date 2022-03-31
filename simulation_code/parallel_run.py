import concurrent.futures
import time
import jsonlines
import os
import shutil
from VaxModel import VaxModel

def set_priority(pid=None,priority=1):
    """ Set The Priority of a Windows Process.  Priority is a value between 0-5 where
        2 is normal priority.  Default sets the priority of the current
        python process but can take any valid process ID. """
        
    import win32api,win32process,win32con
    
    priorityclasses = [win32process.IDLE_PRIORITY_CLASS,
                       win32process.BELOW_NORMAL_PRIORITY_CLASS,
                       win32process.NORMAL_PRIORITY_CLASS,
                       win32process.ABOVE_NORMAL_PRIORITY_CLASS,
                       win32process.HIGH_PRIORITY_CLASS,
                       win32process.REALTIME_PRIORITY_CLASS]
    if pid == None:
        pid = win32api.GetCurrentProcessId()
    handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
    win32process.SetPriorityClass(handle, priorityclasses[priority])


#define the function for running an entire simulation from start to finish
def single_run(run_dict):
    model = VaxModel(run_dict["config"],run_dict["run_number"],run_dict["tmpdirname"])
    model.init_simulation()
    model.generate_network()
    run_number = model.run_full_simulation()
    return run_number

def run(configs_list,number_of_runs):
    
    start_time = time.time()

    set_priority() #set the priority of this script to the lowest, so it doesn't cause my laptop to crash

    #create a directory for storing temporary data files
    tmpdirname = "temporary_files"
    if not os.path.exists(tmpdirname):  # Check whether the specified path exists or not
        os.mkdir(tmpdirname) #ccreate the directory if it doesn't exist already

    run_dicts = []
    overall_count = 0
    for config in configs_list:
        for _ in range(number_of_runs):
            run_dict = {
                "run_number": overall_count,
                "tmpdirname": tmpdirname,
                "config": config
            }
            run_dicts.append(run_dict)
            overall_count += 1

    #this ProcessPoolExecutor manages our multi-processing
    with concurrent.futures.ProcessPoolExecutor() as executor:
    
        num_completed = 0
        futures = {executor.submit(single_run, run_dict) for run_dict in run_dicts} # save the results of each process
        total_processes = len(run_dicts)

        for fut in concurrent.futures.as_completed(futures):
            
            #when a replication finishes running, copy data from the temporary data file to the main data file
            run_number = fut.result()
            with jsonlines.open(tmpdirname + f'/experiment_data_{run_number}.log') as reader:
                with jsonlines.open('experiment_data.log', mode='a') as writer:
                    for obj in reader:
                        writer.write(obj)

            #keep track of the number of replications completed
            num_completed += 1
            print(f"{num_completed} replications completed.")

            if num_completed == total_processes: #once we finish processing all replications, tidy up
                
                shutil.rmtree(tmpdirname) #delete the directory of temporary data files

                #print how long it took to run this whole simuatlion
                duration_seconds = time.time() - start_time 
                duration_minutes = duration_seconds / 60
                print(f"Simulation finished running after {duration_minutes} minutes.")

