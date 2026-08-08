import fitz  # PyMuPDF
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import io

class AdvancedScannedPDFEditor:
    def __init__(self):
        pass

    def pdf_to_images(self, pdf_bytes, dpi=300):
        """পিডিএফ ফাইলকে হাই-রেজোলিউশন ইমেজে রূপান্তর করে"""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        images = []
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        
        for page in doc:
            pix = page.get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes()))
            images.append(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
        return images

    def get_text_color(self, img_crop):
        """আসল টেক্সটের ফন্ট কালার ব্যাকগ্রাউন্ড থেকে অটো পিক করে"""
        gray = cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        text_pixels = img_crop[thresh == 0]
        if len(text_pixels) > 0:
            mean_color = np.mean(text_pixels, axis=0)
            return (int(mean_color[2]), int(mean_color[1]), int(mean_color[0])) # RGB Format
        return (0, 0, 0)

    def replace_text_advanced(self, image, old_text, new_text):
        """
        ১. ব্যাকগ্রাউন্ড ইনপেইন্টিং (Inpainting) দিয়ে দাগহীন টেক্সট মোছা
        ২. মূল কালার ও টেক্সচার বজায় রেখে নতুন শব্দ বসানো
        """
        rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        ocr_data = pytesseract.image_to_data(rgb_img, output_type=pytesseract.Output.DICT)
        
        modified = False
        n_boxes = len(ocr_data['text'])

        for i in range(n_boxes):
            word = ocr_data['text'][i].strip()
            
            if old_text.lower() in word.lower() and len(word) > 0:
                x = ocr_data['left'][i]
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]

                # ১. পুরনো টেক্সটের আসল কালার চিহ্নিতকরণ
                crop = image[max(0, y):min(image.shape[0], y+h), max(0, x):min(image.shape[1], x+w)]
                text_color = self.get_text_color(crop) if crop.size > 0 else (0, 0, 0)

                # ২. ইনপেইন্টিং মাস্ক তৈরি (ব্যাকগ্রাউন্ড ঠিক রেখে মোছা)
                mask = np.zeros(image.shape[:2], dtype=np.uint8)
                padding = 4
                cv2.rectangle(
                    mask, 
                    (max(0, x - padding), max(0, y - padding)), 
                    (min(image.shape[1], x + w + padding), min(image.shape[0], y + h + padding)), 
                    255, -1
                )

                # Inpaint প্রয়োগ
                image = cv2.inpaint(image, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)

                # ৩. নতুন সঠিক টেক্সট ড্র করা
                img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(img_pil)

                font_size = int(h * 0.85)
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()

                draw.text((x, y), new_text, font=font, fill=text_color)
                image = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
                modified = True

        return image, modified

    def images_to_pdf(self, images):
        """এডিট করা ছবিগুলোকে আবার ক্লিয়ার পিডিএফ ফরম্যাটে সেভ করা"""
        pdf_doc = fitz.open()
        for img in images:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            img_byte_arr = io.BytesIO()
            pil_img.save(img_byte_arr, format='PDF', quality=100)
            
            temp_pdf = fitz.open("pdf", img_byte_arr.getvalue())
            pdf_doc.insert_pdf(temp_pdf)
            
        return pdf_doc.tobytes()