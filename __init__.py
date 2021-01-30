bl_info = {
    'name': 'Allods Online geometry addon',
    'category': 'All',
    'version': (0, 0, 1),
    'blender': (2, 90, 0)
}

moduleNames = ['import']
moduleFullNames = []

import sys
import importlib

for moduleName in moduleNames:
    moduleFullNames.append('{}.{}'.format(__name__, moduleName))

for moduleFullName in moduleFullNames:
    if moduleFullName in sys.modules:
        importlib.reload(sys.modules[moduleFullName])
    else:
        globals()[moduleFullName] = importlib.import_module(moduleFullName)

def register():
    for moduleName in moduleFullNames:
        if moduleName in sys.modules:
            if hasattr(sys.modules[moduleName], 'register'):
                sys.modules[moduleName].register()

def unregister():
    for moduleName in moduleFullNames:
        if moduleName in sys.modules:
            if hasattr(sys.modules[moduleName], 'unregister'):
                sys.modules[moduleName].unregister()
