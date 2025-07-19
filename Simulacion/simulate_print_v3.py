import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import tkinter as tk
from tkinter import filedialog, ttk
import numpy as np
import time
import os
import sys

class GCodeViewer:
    def __init__(self, master, initial_gcode_id=None):
        self.master = master
        master.title("Visualizador de Impresión 3D G-code")

        # CAMBIO AQUÍ: Usar 'zoomed' para maximizar en lugar de '-fullscreen'
        master.state('zoomed') 

        self.fig = None
        self.ax = None
        self.lines = []
        self.current_point_marker = None
        self.animation = None
        self.gcode_data = []
        self.current_frame_index = 0
        self.is_playing = False
        self.total_gcode_points = 0
        
        self.animation_interval_ms = 1 
        self.animation_step_size = 1

        self.fixed_z_height_for_plot = 30.0
        self.plot_margin_factor = 0.05 

        self.awaiting_key_press = False 

        self.create_widgets()

        if initial_gcode_id:
            self.load_gcode_from_id(initial_gcode_id)

        # Iniciar animación automáticamente después de 5 segundos
        self.master.after(5000, self.start_auto_play_animation)


    def create_widgets(self):
        self.frame_controls = tk.Frame(self.master)
        self.frame_controls.pack(pady=10)

        self.btn_load = tk.Button(self.frame_controls, text="Cargar G-code", command=self.load_gcode)
        self.btn_load.pack(side=tk.LEFT, padx=5)

        self.btn_play_pause = tk.Button(self.frame_controls, text="Reproducir", command=self.toggle_play_pause)
        self.btn_play_pause.pack(side=tk.LEFT, padx=5)

        self.btn_go_to_end = tk.Button(self.frame_controls, text="Ir al final", command=self.go_to_end_of_print)
        self.btn_go_to_end.pack(side=tk.LEFT, padx=5)

        self.speed_label = tk.Label(self.frame_controls, text="Velocidad:")
        self.speed_label.pack(side=tk.LEFT, padx=5)
        self.speed_slider = tk.Scale(self.frame_controls, from_=1, to_=200, resolution=1, orient=tk.HORIZONTAL,
                                     command=self.update_animation_interval, label="ms/frame")
        self.speed_slider.set(self.animation_interval_ms)
        self.speed_slider.pack(side=tk.LEFT, padx=5)
        
        self.step_label = tk.Label(self.frame_controls, text="Salto:")
        self.step_label.pack(side=tk.LEFT, padx=5)
        self.step_slider = tk.Scale(self.frame_controls, from_=1, to_=100, resolution=1, orient=tk.HORIZONTAL,
                                    command=self.update_animation_step_size, label="Puntos/frame")
        self.step_slider.set(self.animation_step_size)
        self.step_slider.pack(side=tk.LEFT, padx=5)

        self.progressbar = ttk.Progressbar(self.master, orient="horizontal", length=500, mode="determinate")
        self.progressbar.pack(pady=10, fill=tk.X, padx=10)

        self.setup_plot()

    def setup_plot(self):
        if self.fig is None:
            self.fig = plt.Figure(figsize=(8, 6))
            self.ax = self.fig.add_subplot(111, projection='3d')
            self.ax.set_xlabel("X")
            self.ax.set_ylabel("Y")
            self.ax.set_zlabel("Z")
            # self.ax.set_title("Visualizador de Impresión 3D") # Eliminado o comentado
            self.ax.grid(True)

            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.pack(fill=tk.BOTH, expand=True)

            self.current_point_marker = self.ax.plot([], [], [], 'ro', markersize=8, label='Cabezal')[0]
            self.ax.legend()
        else:
            self.ax.clear()
            self.ax.set_xlabel("X")
            self.ax.set_ylabel("Y")
            self.ax.set_zlabel("Z")
            # self.ax.set_title("Visualizador de Impresión 3D") # Eliminado o comentado
            self.ax.grid(True)
            self.current_point_marker = self.ax.plot([], [], [], 'ro', markersize=8, label='Cabezal')[0]
            self.ax.legend()


    def load_gcode(self, file_path=None):
        if file_path is None:
            file_path = filedialog.askopenfilename(filetypes=[("Archivos G-code", "*.gcode"), ("Todos los archivos", "*.*")])
            if not file_path:
                return

        self.gcode_data = self.parse_gcode(file_path)
        if not self.gcode_data:
            print(f"No se pudieron extraer datos válidos del archivo G-code: {file_path}")
            return

        self.reset_animation()
        self.plot_initial_path(draw_full_path=False)
        self.total_gcode_points = len(self.gcode_data)
        print(f"G-code cargado con {self.total_gcode_points} movimientos desde {os.path.basename(file_path)}.")

    def load_gcode_from_id(self, order_id):
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        
        gcode_file_path = os.path.join(
            current_script_dir, 
            'STL_Gcode_excel', 
            'Pedidos', 
            str(order_id), 
            f"{order_id}.gcode"
        )
        
        print(f"Intentando cargar G-code para el pedido {order_id} desde: {gcode_file_path}")
        if os.path.exists(gcode_file_path):
            self.load_gcode(gcode_file_path)
        else:
            print(f"Error: El archivo G-code '{gcode_file_path}' no se encontró para el pedido {order_id}.")

    def parse_gcode(self, file_path):
        data = []
        current_x, current_y, current_z = 0.0, 0.0, 0.0
        
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(';') or line.startswith('('):
                    continue

                if ';' in line:
                    line = line.split(';')[0].strip()
                if '(' in line: 
                    line = line.split('(')[0].strip()

                parts = line.split()
                if not parts: 
                    continue

                command = parts[0]

                if command == 'G0' or command == 'G1':
                    new_x, new_y, new_z = current_x, current_y, current_z
                    extrusion_change = False

                    for part in parts[1:]:
                        if part.startswith('X'):
                            new_x = float(part[1:])
                        elif part.startswith('Y'):
                            new_y = float(part[1:])
                        elif part.startswith('Z'):
                            new_z = float(part[1:])
                        elif part.startswith('E'):
                            e_val_new = float(part[1:])
                            if command == 'G1' and e_val_new > 0: 
                                extrusion_change = True

                    data.append({
                        'x': new_x,
                        'y': new_y,
                        'z': new_z,
                        'extruding': extrusion_change, 
                        'prev_x': current_x,
                        'prev_y': current_y,
                        'prev_z': current_z
                    })
                    current_x, current_y, current_z = new_x, new_y, new_z

                elif command == 'G28':
                    current_x, current_y, current_z = 0.0, 0.0, 0.0
                    data.append({
                        'x': current_x,
                        'y': current_y,
                        'z': current_z,
                        'extruding': False, 
                        'prev_x': current_x,
                        'prev_y': current_y,
                        'prev_z': current_z
                    })

        return data

    def plot_initial_path(self, draw_full_path=True):
        self.setup_plot() 
        
        if not self.gcode_data:
            return

        x_coords = []
        y_coords = []
        z_coords = []
        
        for i, point in enumerate(self.gcode_data):
            x_coords.append(point['x'])
            y_coords.append(point['y'])
            z_coords.append(point['z'])
            
        if draw_full_path:
            lines_to_plot_extruding_x = []
            lines_to_plot_extruding_y = []
            lines_to_plot_extruding_z = []

            for i, point in enumerate(self.gcode_data):
                if point['extruding']:
                    lines_to_plot_extruding_x.extend([point['prev_x'], point['x'], np.nan])
                    lines_to_plot_extruding_y.extend([point['prev_y'], point['y'], np.nan])
                    lines_to_plot_extruding_z.extend([point['prev_z'], point['z'], np.nan])

            if lines_to_plot_extruding_x:
                self.ax.plot(lines_to_plot_extruding_x, lines_to_plot_extruding_y, lines_to_plot_extruding_z,
                             color='blue', linewidth=1.5, alpha=1.0) 

        if x_coords and y_coords and z_coords:
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            min_z, max_z = min(z_coords), max(z_coords)

            if min_x == max_x: max_x += 10 
            if min_y == max_y: max_y += 10
            if min_z == max_z: max_z += 10 

            range_x = max_x - min_x
            range_y = max_y - min_y

            margin_x_y = self.plot_margin_factor 
            self.ax.set_xlim(min_x - range_x * margin_x_y, max_x + range_x * margin_x_y)
            self.ax.set_ylim(min_y - range_y * margin_x_y, max_y + range_y * margin_x_y)

            x_limit_range = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
            y_limit_range = self.ax.get_ylim()[1] - self.ax.get_ylim()[0]
            z_limit_range = self.fixed_z_height_for_plot 

            self.ax.set_box_aspect((x_limit_range, y_limit_range, z_limit_range))
            
            self.ax.set_zlim(0, self.fixed_z_height_for_plot) 

        self.canvas.draw_idle()

    def update_plot(self, frame_animation_index):
        actual_gcode_index = self.current_frame_index + frame_animation_index * self.animation_step_size

        if actual_gcode_index >= self.total_gcode_points:
            if self.animation:
                self.animation.event_source.stop()
            self.is_playing = False
            self.btn_play_pause.config(text="Reproducir")
            self.progressbar['value'] = 100 

            if not self.awaiting_key_press:
                print("Animación finalizada. Presione cualquier tecla para cerrar la ventana.")
                self.awaiting_key_press = True
                self.master.bind('<Key>', self.on_key_press)
            return [self.current_point_marker] 

        current_point = self.gcode_data[actual_gcode_index]

        self.current_point_marker.set_data([current_point['x']], [current_point['y']])
        self.current_point_marker.set_3d_properties([current_point['z']])

        if current_point['extruding']:
            line, = self.ax.plot([current_point['prev_x'], current_point['x']],
                                 [current_point['prev_y'], current_point['y']],
                                 [current_point['prev_z'], current_point['z']],
                                 color='blue', linewidth=2)
            self.lines.append(line)

        progress = (actual_gcode_index / self.total_gcode_points) * 100
        self.progressbar['value'] = progress

        return self.lines + [self.current_point_marker]

    def start_auto_play_animation(self):
        if self.gcode_data: # Asegurarse de que el G-code ya esté cargado
            print("Iniciando animación automáticamente...")
            self.toggle_play_pause() # Esto iniciará la reproducción
        else:
            print("G-code no cargado. No se puede iniciar la animación automáticamente.")


    def toggle_play_pause(self):
        if not self.gcode_data:
            print("Cargue un archivo G-code primero.")
            return

        if self.awaiting_key_press:
            self.awaiting_key_press = False
            self.master.unbind('<Key>', self.on_key_press)

        if self.animation is None:
            self.start_animation()
            self.btn_play_pause.config(text="Pausar")
            self.is_playing = True
        elif self.is_playing:
            self.animation.event_source.stop()
            self.btn_play_pause.config(text="Reproducir")
            self.is_playing = False
        else:
            self.animation.event_source.start()
            self.btn_play_pause.config(text="Pausar")
            self.is_playing = True

    def start_animation(self):
        if self.animation:
            self.animation.event_source.stop() 

        num_frames_to_animate = (self.total_gcode_points - self.current_frame_index + self.animation_step_size - 1) // self.animation_step_size
        
        if num_frames_to_animate <= 0:
            print("No hay más frames para animar o el paso es demasiado grande.")
            self.progressbar['value'] = 100 
            if not self.awaiting_key_press:
                print("Animación finalizada. Presione cualquier tecla para cerrar la ventana.")
                self.awaiting_key_press = True
                self.master.bind('<Key>', self.on_key_press)
            return

        self.animation = FuncAnimation(
            self.fig,
            self.update_plot,
            frames=num_frames_to_animate, 
            interval=self.animation_interval_ms,
            blit=True,
            repeat=False,
            init_func=self.init_animation
        )
        self.canvas.draw_idle()

    def init_animation(self):
        for line in self.lines:
            line.remove()
        self.lines = []
        if self.gcode_data and self.current_frame_index < self.total_gcode_points:
            initial_point_for_animation = self.gcode_data[self.current_frame_index]
            self.current_point_marker.set_data([initial_point_for_animation['x']], [initial_point_for_animation['y']])
            self.current_point_marker.set_3d_properties([initial_point_for_animation['z']])
        else:
            self.current_point_marker.set_data([], [])
            self.current_point_marker.set_3d_properties([])
            
        return self.lines + [self.current_point_marker]

    def reset_animation(self):
        if self.animation:
            self.animation.event_source.stop()
            self.animation = None

        self.current_frame_index = 0
        self.is_playing = False
        self.btn_play_pause.config(text="Reproducir")
        self.setup_plot() 
        
        if self.gcode_data:
            self.plot_initial_path(draw_full_path=False)
            initial_point = self.gcode_data[0] if self.gcode_data else {'x': 0, 'y': 0, 'z': 0}
            self.current_point_marker.set_data([initial_point['x']], [initial_point['y']])
            self.current_point_marker.set_3d_properties([initial_point['z']])
            self.canvas.draw_idle()
        
        self.progressbar['value'] = 0
        if self.awaiting_key_press:
            self.awaiting_key_press = False
            self.master.unbind('<Key>', self.on_key_press)


    def update_animation_interval(self, val):
        self.animation_interval_ms = int(val)
        if self.animation and self.is_playing:
            self.animation.event_source.stop()
            self.start_animation()

    def update_animation_step_size(self, val):
        self.animation_step_size = int(val)
        self.reset_animation()

    def go_to_end_of_print(self):
        if not self.gcode_data:
            print("Cargue un archivo G-code primero.")
            return

        if self.animation:
            self.animation.event_source.stop()
            self.animation = None
        self.is_playing = False
        self.btn_play_pause.config(text="Reproducir")

        self.setup_plot()
        self.plot_initial_path(draw_full_path=True) 

        if self.gcode_data:
            last_point = self.gcode_data[-1]
            self.current_point_marker.set_data([last_point['x']], [last_point['y']])
            self.current_point_marker.set_3d_properties([last_point['z']])
            self.canvas.draw_idle()

        self.progressbar['value'] = 100

        print("impresión finalizada")
        if not self.awaiting_key_press:
            print("Presione cualquier tecla para cerrar la ventana.")
            self.awaiting_key_press = True
            self.master.bind('<Key>', self.on_key_press)

    def on_key_press(self, event):
        if self.awaiting_key_press:
            self.master.destroy()
            sys.exit() # Cierra la consola y termina el script


if __name__ == "__main__":
    root = tk.Tk()
    
    initial_id = None
    if len(sys.argv) > 1:
        initial_id = sys.argv[1]

    app = GCodeViewer(root, initial_gcode_id=initial_id)
    root.mainloop()
