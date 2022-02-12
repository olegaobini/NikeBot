# These constants can be set by the external UI-layer process, don't change them manually
is_ui_process = False
execution_id = ''
task_id = ''
executable_name = 'nikebot'
# no need in these checks if location permission is denied beforehand
do_location_permission_dialog_checks = True


def callback(profile_name):
    pass


hardban_detected_callback = callback
softban_detected_callback = callback


def is_nikebot():
    return execution_id == ''
