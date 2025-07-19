import os
from fpdf import FPDF
from PyPDF2 import PdfMerger
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader

# === FUNCIONES PARA PDF ===

class PDF(FPDF):
    def header(self):
        pass
    def footer(self):
        pass

class PDF(FPDF):
    pass  # Asegúrate de tener esta clase definida o usa directamente FPDF()

def crear_pdf(nombre_archivo, texto_arriba, texto_abajo, imagen_path, imagen_esquina_path, carpeta_destino, tiempo_entrega=None, costo_total=None):
    pdf_path = os.path.join(carpeta_destino, f"{nombre_archivo}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Encabezado
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Factura de Pedido")

    # Texto arriba (ej: tiempo proveedor)
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, texto_arriba)

    # Agregar tiempo de entrega y costo total justo debajo del texto arriba
    y_pos = height - 110
    c.setFont("Helvetica-Bold", 12)
    if tiempo_entrega is not None:
        c.drawString(50, y_pos, f"Tiempo de entrega: {tiempo_entrega} ")
        y_pos -= 20
    if costo_total is not None:
        c.drawString(50, y_pos, f"Costo total: ${costo_total:,.2f}")
        y_pos -= 20

    # Imagen principal centrada
    if imagen_path and os.path.exists(imagen_path):
        try:
            img = ImageReader(imagen_path)
            img_width, img_height = img.getSize()
            aspect = img_height / float(img_width)
            img_display_width = 4 * inch
            img_display_height = img_display_width * aspect
            c.drawImage(img, (width - img_display_width) / 2, y_pos - img_display_height - 20, width=img_display_width, height=img_display_height)
        except Exception as e:
            print(f"Error cargando imagen principal: {e}")

    # Imagen esquina (por ejemplo logo)
    if imagen_esquina_path and os.path.exists(imagen_esquina_path):
        try:
            logo = ImageReader(imagen_esquina_path)
            logo_width, logo_height = logo.getSize()
            logo_display_width = 1.5 * inch
            logo_display_height = logo_display_width * (logo_height / float(logo_width))
            c.drawImage(logo, width - logo_display_width - 50, height - logo_display_height - 30, width=logo_display_width, height=logo_display_height)
        except Exception as e:
            print(f"Error cargando imagen de esquina: {e}")

    # Texto abajo (por ejemplo nota o agradecimiento)
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, 50, texto_abajo)

    # Pie de página con número de página
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 30, f"Página 1")

    c.save()
    print(f"PDF creado en {pdf_path}")