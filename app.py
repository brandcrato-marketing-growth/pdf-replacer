from flask import Flask, render_template, request, jsonify
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    file = request.files['file']
    doc = fitz.open(stream=file.read(), filetype="pdf")
    extracted_blocks = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text_page = page.get_text("blocks")
        
        # ডিজিটাল টেক্সট না পাওয়া গেলে OCR ব্যবহার করবে
        if not text_page:
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            for i in range(len(ocr_data['text'])):
                if ocr_data['text'][i].strip():
                    extracted_blocks.append({
                        'text': ocr_data['text'][i],
                        'x': ocr_data['left'][i],
                        'y': ocr_data['top'][i],
                        'w': ocr_data['width'][i],
                        'h': ocr_data['height'][i]
                    })
        else:
            for b in text_page:
                extracted_blocks.append({
                    'text': b[4],
                    'x': b[0],
                    'y': b[1],
                    'w': b[2] - b[0],
                    'h': b[3] - b[1]
                })

    return jsonify({'blocks': extracted_blocks})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
