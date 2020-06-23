import subprocess

import server_frontend
from data_structures import State, Machine

print_error = print #global function for printing errors


def setup(state):
    """
    This function tries to setup the iperf server.
    state holds all values about the currrent progress of the setup
    """
    if state == None:
        state = new_state()

    state.sudo_pw = server_frontend.server_settings.sudo_pw
    if state.sudo_pw == None or (not state.shell_works): #None indicates user wants to continue without sudo, if shell doesn't work,
                                                        #sudo is not necessary
        state.wants_sudo = False
        state.has_sudo = False
    else:
        state.wants_sudo = True
        #TODO check if correct sudo password
        state.has_sudo = True

    #Check if correct sudo password
    if state.wants_sudo and (not state.has_sudo):
        print_error(["Incorrect sudo password"])
        return state

    #TODO
    return state

def new_state():
    """
    Generate a new initial state
    """

    state = State()

    state.shell_works = True
    try:
        subprocess.call(["ls"])
    except FileNotFoundError:
        state.shell_works = False

    #TODO initialize machines
    #for d in server_frontend.active_config

    
    return state
