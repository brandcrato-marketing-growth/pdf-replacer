import os
import fitz  # PyMuPDF
from flask import Flask, render_template, request, send_file, jsonify

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/replace-text', methods=['POST'])
def replace_text():
    try:
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'PDF ফাইল নির্বাচন করা হয়নি!'}), 400

        file = request.files['pdf_file']
        old_text = request.form.get('old_text', '').strip()
        new_text = request.form.get('new_text', '').strip()

        if not file or not old_text or not new_text:
            return jsonify({'error': 'সবগুলো ঘর সঠিকভাবে পূরণ করুন!'}), 400

        input_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"edited_{file.filename}")
        file.save(input_path)

        doc = fitz.open(input_path)

        for page in doc:
            # পেজের সমস্ত টেক্সটের বিস্তারিত মেটাডেটা (ফন্ট, সাইজ, কালার) এক্সট্র্যাক্ট করা
            text_instances = page.search_for(old_text)

            if not text_instances:
                continue

            text_page = page.get_text("dict")
            font_size = 12
            font_color = (0, 0, 0)

            # অরিজিনাল টেক্সটের ফন্ট প্রপার্টিজ খুঁজে বের করা
            for block in text_page["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if old_text in span["text"]:
                                font_size = span["size"]
                                # RGB Color integer value to Tuple Conversion
                                color_int = span["color"]
                                r = ((color_int >> 16) & 255) / 255.0
                                g = ((color_int >> 8) & 255) / 255.0
                                b = (color_int & 255) / 255.0
                                font_color = (r, g, b)
                                break

            # ১. অরিজিনাল টেক্সট রিমুভ (Redaction)
            for inst in text_instances:
                page.add_redact_annot(inst, fill=(1, 1, 1))
                page.apply_redactions()

                # ২. অরিজিনাল ফন্ট সাইজ, কালার ও কোঅর্ডিনেট ব্যবহার করে নতুন টেক্সট ড্র করা
                page.insert_text(
                    fitz.Point(inst.x0, inst.y1 - 1.5),
                    new_text,
                    fontsize=font_size,
                    fontname="helv", # প্রমিত স্ট্যান্ডার্ড টাইপফেস
                    color=font_color
                )

        doc.save(output_path)
        doc.close()

        return send_file(output_path, as_attachment=True, download_name=f"edited_{file.filename}")

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)