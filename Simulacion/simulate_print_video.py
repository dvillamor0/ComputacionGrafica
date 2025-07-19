import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import os
from moviepy import ImageSequenceClip
import sys
import subprocess

# Asegúrate de que GcodeParser esté definido o importado
from gcode_parser import GcodeParser

class GcodeAnimator:
    def __init__(self, gcode_filepath, output_dir="animation_frames",
                 x_lim=(0, 200), y_lim=(0, 200), z_lim=(0, 200)):
        self.gcode_filepath = gcode_filepath
        self.output_dir = output_dir
        self.parser = GcodeParser()
        self.moves = self.parser.parse_file(gcode_filepath)
        self.x_lim = x_lim
        self.y_lim = y_lim
        self.z_lim = z_lim

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        else:
            for f in os.listdir(self.output_dir):
                os.remove(os.path.join(self.output_dir, f))


        # --- Configuración de Múltiples Subgráficos ---
        self.fig = plt.figure(figsize=(16, 12)) # Ajusta el tamaño de la figura
        self.fig.suptitle(f"Simulación de Impresión 3D: {os.path.basename(gcode_filepath)}", fontsize=16)

        # Subgráfico 3D principal (superior izquierda)
        self.ax_3d = self.fig.add_subplot(221, projection='3d')
        self.ax_3d.set_xlabel('X (mm)')
        self.ax_3d.set_ylabel('Y (mm)')
        self.ax_3d.set_zlabel('Z (mm)')

        # --- CAMBIO AQUÍ: Establecer los límites de los ejes ---
        self.ax_3d.set_xlim(self.x_lim)
        self.ax_3d.set_ylim(self.y_lim)
        self.ax_3d.set_zlim(self.z_lim)

        # --- CAMBIO AQUÍ: Configurar la relación de aspecto de la caja 3D ---
        # Esto hace que las unidades se escalen por igual en X, Y y Z.
        # El eje Z se verá 'corto' porque su rango (25mm) es pequeño comparado con X/Y (300mm),
        # lo cual es la representación correcta de "sin escalar".
        self.ax_3d.set_box_aspect((self.x_lim[1] - self.x_lim[0], self.y_lim[1] - self.y_lim[0], self.z_lim[1] - self.z_lim[0]))
        # --- FIN CAMBIOS ---

        self.ax_3d.set_title('Vista 3D', fontsize=12)
        self.ax_3d.view_init(elev=45, azim=-45)
        self.ax_3d.grid(True)

        # Añadir placa de construcción al 3D view
        x_plate = np.array([[self.x_lim[0], self.x_lim[1]], [self.x_lim[0], self.x_lim[1]]])
        y_plate = np.array([[self.y_lim[0], self.y_lim[0]], [self.y_lim[1], self.y_lim[1]]])
        z_plate = np.array([[self.z_lim[0], self.z_lim[0]], [self.z_lim[0], self.z_lim[0]]])
        self.ax_3d.plot_surface(x_plate, y_plate, z_plate, color='lightgray', alpha=0.3, edgecolor='none')
        self.ax_3d.plot([self.x_lim[0], self.x_lim[1], self.x_lim[1], self.x_lim[0], self.x_lim[0]],
                        [self.y_lim[0], self.y_lim[0], self.y_lim[1], self.y_lim[1], self.y_lim[0]],
                        [self.z_lim[0], self.z_lim[0], self.z_lim[0], self.z_lim[0], self.z_lim[0]],
                        color='gray', linewidth=1.0)
        
        # Subgráfico de Vista Superior (X-Y)
        self.ax_top = self.fig.add_subplot(222)
        self.ax_top.set_xlabel('X (mm)')
        self.ax_top.set_ylabel('Y (mm)')
        self.ax_top.set_xlim(self.x_lim)
        self.ax_top.set_ylim(self.y_lim)
        self.ax_top.set_title('Vista Superior (X-Y)', fontsize=12)
        self.ax_top.set_aspect('equal', adjustable='box') # Proporciones reales
        self.ax_top.grid(True)

        # Subgráfico de Vista Frontal (X-Z)
        self.ax_front = self.fig.add_subplot(223)
        self.ax_front.set_xlabel('X (mm)')
        self.ax_front.set_ylabel('Z (mm)')
        self.ax_front.set_xlim(self.x_lim)
        self.ax_front.set_ylim(self.z_lim) # Z-axis for vertical height
        self.ax_front.set_title('Vista Frontal (X-Z)', fontsize=12)
        self.ax_front.set_aspect('equal', adjustable='box')
        self.ax_front.grid(True)

        # Subgráfico de Vista Lateral (Y-Z)
        self.ax_side = self.fig.add_subplot(224)
        self.ax_side.set_xlabel('Y (mm)')
        self.ax_side.set_ylabel('Z (mm)')
        self.ax_side.set_xlim(self.y_lim)
        self.ax_side.set_ylim(self.z_lim) # Z-axis for vertical height
        self.ax_side.set_title('Vista Lateral (Y-Z)', fontsize=12)
        self.ax_side.set_aspect('equal', adjustable='box')
        self.ax_side.grid(True)

        # --- Inicialización de Líneas y Marcadores para TODOS los Subgráficos ---
        # 3D View
        self.extruded_line_3d, = self.ax_3d.plot([], [], [], color='blue', linewidth=3, label='Extruded Path')
        self.head_position_marker_3d, = self.ax_3d.plot([], [], [], 'ro', markersize=5, label='Print Head')

        # Top View (X, Y)
        self.extruded_line_top, = self.ax_top.plot([], [], color='blue', linewidth=3)
        self.head_position_marker_top, = self.ax_top.plot([], [], 'ro', markersize=5)

        # Front View (X, Z)
        self.extruded_line_front, = self.ax_front.plot([], [], color='blue', linewidth=3)
        self.head_position_marker_front, = self.ax_front.plot([], [], 'ro', markersize=5)

        # Side View (Y, Z)
        self.extruded_line_side, = self.ax_side.plot([], [], color='blue', linewidth=3)
        self.head_position_marker_side, = self.ax_side.plot([], [], 'ro', markersize=5)
        # --- Fin Inicialización ---

        self.extruded_path_points = []
        self.current_head_pos = np.array([0.0, 0.0, 0.0])
        self.was_extruding_last_move = False

        self.frames = []

        # Ajustar el espaciado entre subplots
        plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Deja espacio para el super título

    def update(self, frame_num_gcode_move):
        if frame_num_gcode_move >= len(self.moves):
            return []

        move = self.moves[frame_num_gcode_move]
        prev_x, prev_y, prev_z, prev_e = move['prev_pos']
        curr_x, curr_y, curr_z, curr_e = move['current_pos']
        is_current_move_extruding = move['extruding']

        self.current_head_pos = np.array([curr_x, curr_y, curr_z])

        if is_current_move_extruding:
            self.extruded_path_points.append(np.array([prev_x, prev_y, prev_z]))
            self.extruded_path_points.append(np.array([curr_x, curr_y, curr_z]))
        elif self.was_extruding_last_move:
            if self.extruded_path_points and not np.isnan(self.extruded_path_points[-1][0]):
                 self.extruded_path_points.append(np.array([np.nan, np.nan, np.nan]))

        self.was_extruding_last_move = is_current_move_extruding

        updated_artists = []

        # 3D View
        if len(self.extruded_path_points) > 0:
            paths = np.array(self.extruded_path_points)
            self.extruded_line_3d.set_data(paths[:, 0], paths[:, 1])
            self.extruded_line_3d.set_3d_properties(paths[:, 2])
        self.head_position_marker_3d.set_data([curr_x], [curr_y])
        self.head_position_marker_3d.set_3d_properties([curr_z])
        updated_artists.extend([self.extruded_line_3d, self.head_position_marker_3d])

        # Top View (X, Y)
        if len(self.extruded_path_points) > 0:
            paths = np.array(self.extruded_path_points)
            self.extruded_line_top.set_data(paths[:, 0], paths[:, 1])
        self.head_position_marker_top.set_data([curr_x], [curr_y])
        updated_artists.extend([self.extruded_line_top, self.head_position_marker_top])
        
        # Front View (X, Z)
        if len(self.extruded_path_points) > 0:
            paths = np.array(self.extruded_path_points)
            self.extruded_line_front.set_data(paths[:, 0], paths[:, 2])
        self.head_position_marker_front.set_data([curr_x], [curr_z])
        updated_artists.extend([self.extruded_line_front, self.head_position_marker_front])

        # Side View (Y, Z)
        if len(self.extruded_path_points) > 0:
            paths = np.array(self.extruded_path_points)
            self.extruded_line_side.set_data(paths[:, 1], paths[:, 2])
        self.head_position_marker_side.set_data([curr_y], [curr_z])
        updated_artists.extend([self.extruded_line_side, self.head_position_marker_side])

        return updated_artists

    def animate(self, skip_frames_factor, fps):
        total_gcode_moves = len(self.moves)
        frames_saved_count = 0

        print(f"Iniciando simulación para: {os.path.basename(self.gcode_filepath)}")
        print(f"Total de movimientos G-code a procesar: {total_gcode_moves}")
        print(f"Configuración: Guardando 1 fotograma cada {skip_frames_factor} movimientos G-code.")
        print("-" * 70)
        
        bar_length = 40
        
        for i in range(total_gcode_moves):
            self.update(i)

            if i % skip_frames_factor == 0 or i == total_gcode_moves - 1:
                frame_filename = os.path.join(self.output_dir, f"frame_{frames_saved_count:05d}.png")
                plt.savefig(frame_filename, dpi=100, bbox_inches='tight')
                self.frames.append(frame_filename)
                frames_saved_count += 1
                
            progress = (i + 1) / total_gcode_moves
            block = int(round(bar_length * progress))
            
            status_message = (
                f"\rProcesando G-code: [{ '#' * block + '-' * (bar_length - block)}] "
                f"{progress:.1%} (Movimientos: {i+1}/{total_gcode_moves} | Fotogramas guardados: {frames_saved_count})"
            )
            sys.stdout.write(status_message)
            sys.stdout.flush()

        sys.stdout.write('\r' + ' ' * (bar_length + 60) + '\r')
        sys.stdout.write("\n")
        sys.stdout.flush()
        
        print(f"Generación de fotogramas completada. Total: {frames_saved_count} fotogramas.")
        print("-" * 70)

        self.create_video(output_video_filename="print_simulation.mp4", fps=fps)

    def create_video(self, output_video_filename="print_animation.mp4", fps=30):
        if not self.frames:
            print("No hay fotogramas para crear el video. Ejecuta .animate() primero.")
            return

        print(f"Creando video '{output_video_filename}' con {len(self.frames)} fotogramas a {fps} FPS...")
        output_video_full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_video_filename)

        clip = ImageSequenceClip(self.frames, fps=fps)
        clip.write_videofile(output_video_full_path, codec='libx264')
        print("Video creado exitosamente.")

        try:
            if sys.platform.startswith('win'):
                os.startfile(output_video_full_path)
            elif sys.platform.startswith('darwin'):
                subprocess.Popen(['open', output_video_full_path])
            else:
                subprocess.Popen(['xdg-open', output_video_full_path])
            print(f"Abriendo video: {os.path.basename(output_video_full_path)}")
        except Exception as e:
            print(f"No se pudo abrir el video automáticamente: {e}")

    def show_final_plot(self):
        plt.show()

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    gcode_folder = os.path.join(project_root, "STL_Gcode_excel", "Pedidos", "3")
    target_gcode_file = "3.txt"

    gcode_filepath = os.path.join(gcode_folder, target_gcode_file)

    if not os.path.exists(gcode_filepath):
        print(f"Error: El archivo G-code no se encontró en la ruta: {gcode_filepath}")
        print("Asegúrate de que la estructura de carpetas sea correcta.")
        exit()

    # --- CAMBIO AQUÍ: Definir las dimensiones deseadas ---
    printer_x_max = 300
    printer_y_max = 300
    printer_z_max = 25 # Altura máxima de 25 mm

    animator = GcodeAnimator(
        gcode_filepath=gcode_filepath,
        output_dir="animation_frames",
        x_lim=(0, printer_x_max),
        y_lim=(0, printer_y_max),
        z_lim=(0, printer_z_max)
    )

    SKIP_FACTOR = 50
    FPS_OUTPUT = 30

    animator.animate(skip_frames_factor=SKIP_FACTOR, fps=FPS_OUTPUT)
