import re
import numpy as np

class GcodeParser:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.e = 0.0 # Extruder position
        self.f = 0.0 # Feedrate (speed)
        self.absolute_positioning = True # G90 (True) or G91 (False)
        self.absolute_extrusion = True   # M82 (True) or M83 (False)

    def parse_line(self, line):
        line = line.strip()
        if not line or line.startswith(';') or line.startswith('('):
            return None # Ignorar líneas vacías o comentarios

        match = re.match(r'^([GMX][0-9.]+)(.*)', line)
        if not match:
            return None

        command = match.group(1)
        params_str = match.group(2)

        params = {}
        # Usar una expresión regular para encontrar todos los parámetros alfabéticos
        param_matches = re.findall(r'([A-Z])([-+]?\d*\.?\d+)', params_str)
        for key, value in param_matches:
            params[key] = float(value)

        current_x, current_y, current_z, current_e = self.x, self.y, self.z, self.e

        if command.startswith('G'):
            g_command = int(float(command[1:]))
            if g_command in [0, 1]: # G0 (rapid move), G1 (controlled move)
                # Actualizar posición X
                if 'X' in params:
                    if self.absolute_positioning:
                        self.x = params['X']
                    else:
                        self.x += params['X']
                # Actualizar posición Y
                if 'Y' in params:
                    if self.absolute_positioning:
                        self.y = params['Y']
                    else:
                        self.y += params['Y']
                # Actualizar posición Z
                if 'Z' in params:
                    if self.absolute_positioning:
                        self.z = params['Z']
                    else:
                        self.z += params['Z']
                # Actualizar extrusión E
                if 'E' in params:
                    if self.absolute_extrusion:
                        self.e = params['E']
                    else:
                        self.e += params['E']
                # Actualizar velocidad F
                if 'F' in params:
                    self.f = params['F']

                # Devolver el estado antes del movimiento y el estado después
                return {
                    'type': 'move',
                    'prev_pos': (current_x, current_y, current_z, current_e),
                    'current_pos': (self.x, self.y, self.z, self.e),
                    'extruding': self.e > current_e # Asumimos extrusión si E aumenta
                }
            elif g_command == 28: # G28 (Home)
                self.x, self.y, self.z = 0.0, 0.0, 0.0 # O a los límites home de tu impresora
                return {'type': 'home', 'current_pos': (self.x, self.y, self.z, self.e)}
            elif g_command == 90: # G90 (Absolute Positioning)
                self.absolute_positioning = True
                return {'type': 'set_abs_pos'}
            elif g_command == 91: # G91 (Relative Positioning)
                self.absolute_positioning = False
                return {'type': 'set_rel_pos'}
        elif command.startswith('M'):
            m_command = int(float(command[1:]))
            if m_command == 82: # M82 (Absolute Extrusion)
                self.absolute_extrusion = True
                return {'type': 'set_abs_ext'}
            elif m_command == 83: # M83 (Relative Extrusion)
                self.absolute_extrusion = False
                return {'type': 'set_rel_ext'}
        return None

    def parse_file(self, filepath):
        moves = []
        with open(filepath, 'r') as f:
            for line in f:
                result = self.parse_line(line)
                if result and result['type'] == 'move':
                    moves.append(result)
        return moves
