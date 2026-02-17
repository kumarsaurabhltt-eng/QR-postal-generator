import sys
import csv
import io
import qrcode
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import pandas as pd
import os

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 15 * mm


def load_data(csv_path):
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found: {csv_path}")
        sys.exit(1)

    try:
        df = pd.read_csv(csv_path, dtype=str).fillna('')
        return df.to_dict(orient='records')
    except Exception as e:
        print("ERROR reading CSV:", e)
        sys.exit(1)


def generate_qr_image(data, box_size=4):
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img


def fetch_tracking_details_placeholder(tracking_number):
    return {
        "tracking_number": tracking_number,
        "recipient_name": "Recipient for " + tracking_number,
        "from_address": "Sender Address XYZ",
        "to_address": "Receiver Address XYZ",
        "status": "In Transit",
        "last_update": "2025-11-08",
        "notes": ""
    }


def draw_receipt_on_canvas(c, x, y, width, height, data):
    c.setStrokeColor(colors.black)
    c.rect(x, y - height, width, height, stroke=1, fill=0)

    pad = 6
    text_x = x + pad
    text_y = y - pad

    c.setFont("Helvetica-Bold", 10)
    c.drawString(text_x, text_y, f"Tracking: {data.get('tracking_number', '')}")
    text_y -= 14

    c.setFont("Helvetica", 8)
    c.drawString(text_x, text_y, f"Status: {data.get('status', '')}")
    c.drawString(text_x + 150, text_y, f"Last update: {data.get('last_update', '')}")
    text_y -= 12

    c.drawString(text_x, text_y, "From:")
    c.drawString(text_x + 40, text_y, data.get('from_address', '')[:60])
    text_y -= 12

    c.drawString(text_x, text_y, "To:")
    c.drawString(text_x + 40, text_y, data.get('to_address', '')[:60])
    text_y -= 12

    c.drawString(text_x, text_y, f"Recipient: {data.get('recipient_name', '')[:55]}")
    text_y -= 14

    # QR Code
    qr_img = generate_qr_image(data.get("tracking_number", ""), box_size=3)
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)
    img_reader = ImageReader(buf)

    qr_size = 45
    qr_x = x + width - qr_size - pad
    qr_y = y - qr_size - pad

    c.drawImage(img_reader, qr_x, qr_y, qr_size, qr_size)


def generate_pdf(records, output_pdf_path, receipts_per_row=2, receipt_height_mm=60):
    # Ensure output folder exists
    folder = os.path.dirname(output_pdf_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    c = canvas.Canvas(output_pdf_path, pagesize=A4)

    w, h = A4
    receipt_width = (w - 2 * MARGIN - (receipts_per_row - 1) * 10) / receipts_per_row
    receipt_height = receipt_height_mm * mm

    x = MARGIN
    y = h - MARGIN

    for i, rec in enumerate(records):
        details = fetch_tracking_details_placeholder(rec.get("tracking_number"))
        details.update(rec)

        draw_receipt_on_canvas(c, x, y, receipt_width, receipt_height, details)

        x += receipt_width + 10

        if (i + 1) % receipts_per_row == 0:
            x = MARGIN
            y -= receipt_height + 15

            if y < MARGIN + receipt_height:
                c.showPage()
                x = MARGIN
                y = h - MARGIN

    c.save()
    print(f"\nPDF created successfully: {output_pdf_path}\n")


def main():
    if len(sys.argv) < 3:
        print("Usage: python app.py input.csv output/output.pdf")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_pdf = sys.argv[2]

    records = load_data(input_csv)

    if not records:
        print("No data found in CSV.")
        sys.exit(1)

    generate_pdf(records, output_pdf)


if __name__ == "__main__":
    main()
