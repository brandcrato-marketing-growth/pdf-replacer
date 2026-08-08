import streamlit as st
import cv2
import numpy as np
from editor_engine import AdvancedScannedPDFEditor

st.set_page_config(page_title="Scanned PDF Text Editor Panel", layout="wide")

st.title("📄 Scanned PDF & Image Advanced Text Editor")
st.subheader("স্ক্যান করা বা ছবি তোলা পিডিএফের ব্যাকগ্রাউন্ড না ভেঙে রিয়েল টেক্সট এডিট প্যানেল")

@st.cache_resource
def load_editor():
    return AdvancedScannedPDFEditor()

editor = load_editor()

uploaded_file = st.file_uploader("আপনার স্ক্যান করা PDF ফাইলটি এখানে আপলোড করুন", type=["pdf"])

if uploaded_file is not None:
    pdf_bytes = uploaded_file.read()
    
    with st.spinner("পিডিএফ পেজ প্রসেস করা হচ্ছে..."):
        images = editor.pdf_to_images(pdf_bytes)
        st.success(f"মোট {len(images)} টি পেজ লোড হয়েছে।")

    page_num = st.selectbox("এডিট করার জন্য পেজ সিলেক্ট করুন:", range(1, len(images) + 1)) - 1
    current_image = images[page_num].copy()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.write("### 🔍 মূল পেজ প্রিভিউ (Preview)")
        st.image(cv2.cvtColor(current_image, cv2.COLOR_BGR2RGB), use_container_width=True)

    with col2:
        st.write("### 🛠 ম্যানুয়াল টেক্সট রিপ্লেসমেন্ট")
        old_text = st.text_input("যে ভুল বা পুরনো শব্দ/টেক্সট মুছতে চান:")
        new_text = st.text_input("যে নতুন সঠিক শব্দ/টেক্সট বসাতে চান:")

        if st.button("টেক্সট পরিবর্তন ও ব্যাকগ্রাউন্ড ক্লিন করুন"):
            if old_text and new_text:
                edited_img, success = editor.replace_text_advanced(current_image, old_text, new_text)
                if success:
                    images[page_num] = edited_img
                    st.success("টেক্সট সফলভাবে এডিট হয়েছে! কোনো দাগ বা কৃত্রিম চিহ্ন থাকবে না।")
                    st.image(cv2.cvtColor(edited_img, cv2.COLOR_BGR2RGB), use_container_width=True)
                else:
                    st.warning("উক্ত শব্দ/টেক্সটটি ফাইলের মধ্যে মেলেনি। সঠিক বানান লিখে চেষ্টা করুন।")
            else:
                st.error("দয়া করে পুরনো ও নতুন দুটো ঘরই পূরণ করুন।")

    st.markdown("---")
    if st.button("📥 নতুন এডিট করা PDF ডাউনলোড করুন"):
        final_pdf_bytes = editor.images_to_pdf(images)
        st.download_button(
            label="Save Edited PDF",
            data=final_pdf_bytes,
            file_name="Edited_Document_Clean.pdf",
            mime="application/pdf"
        )