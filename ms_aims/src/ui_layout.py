from nicegui import ui

def create_header():
    with ui.header().classes('bg-blue-900 text-white items-center'):
        ui.label('MS-AIMS | Metal Sheet Inspector').classes('text-h6 font-bold')
        ui.space()
        status_label = ui.label('SYSTEM READY').classes('text-sm font-mono bg-green-600 px-2 rounded')
    return status_label

def create_sidebar():
    with ui.left_drawer(value=False) as drawer:
        ui.label('Settings').classes('text-h6')
        # Add settings controls here
    return drawer
