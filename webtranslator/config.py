import threading

shared_state = {
    'current_url': "Starting Translation..."
}

state_lock = threading.Lock()