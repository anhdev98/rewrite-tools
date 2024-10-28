import streamlit as st
import textwrap
from pytube import YouTube 
from youtube_transcript_api import YouTubeTranscriptApi
from newspaper import Article
import google.generativeai as genai
import time

def init_gemini():
    # Cấu hình Gemini API 
    try:
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            GEMINI_API_KEY = "AIzaSyD2FAvYNFEezIZn4bzbY7v1-RSLlfDGudg"  # Fallback key
        genai.configure(api_key=GEMINI_API_KEY)
        return genai.GenerativeModel('gemini-pro')
    except Exception as e:
        st.error(f"Lỗi khởi tạo Gemini: {str(e)}")
        return None

def get_youtube_content(url):
    try:
        yt = YouTube(url)
        video_id = yt.video_id
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['vi', 'en'])
        return "\n".join([entry['text'] for entry in transcript])
    except Exception as e:
        return f"Lỗi khi lấy nội dung YouTube: {str(e)}"

def get_article_content(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        return f"Lỗi khi lấy nội dung bài viết: {str(e)}"

def split_into_chunks(text, chunk_size=4000):
    return textwrap.wrap(text, chunk_size, break_long_words=False)

def rewrite_content(model, content, style_prompt, progress_bar, chunk_size=4000):
    try:
        chunks = split_into_chunks(content, chunk_size)
        rewritten_content = []
        
        for i, chunk in enumerate(chunks):
            system_prompt = f"""
            {style_prompt}
            Hãy viết lại đoạn văn sau theo phong cách tự nhiên, 
            tránh từ ngữ máy móc và giữ nguyên ý chính. Nếu đoạn văn bằng tiếng Việt, 
            hãy giữ nguyên tiếng Việt và thêm các từ địa phương phù hợp:
            
            {chunk}
            """
            
            response = model.generate_content(system_prompt)
            rewritten_content.append(response.text)
            
            # Cập nhật tiến độ
            progress = (i + 1) / len(chunks)
            progress_bar.progress(progress)
            
            # Thêm delay nhỏ để tránh rate limit
            time.sleep(0.5)
            
        return "\n".join(rewritten_content)
        
    except Exception as e:
        return f"Lỗi khi viết lại nội dung: {str(e)}"

def main():
    st.set_page_config(
        page_title="Content Rewrite Tool",
        page_icon="📝",
        layout="wide"
    )
    
    st.title("📝 Content Rewrite Tool")
    
    # Khởi tạo Gemini model
    model = init_gemini()
    if not model:
        st.error("Không thể kết nối với Gemini API. Vui lòng kiểm tra API key.")
        return
    
    # Input section
    st.header("Input")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        input_type = st.radio("Chọn loại input:", ["URL", "Text trực tiếp"])
    
    with col2:
        chunk_size = st.number_input("Độ dài chunk (ký tự):", 
                                   min_value=1000, 
                                   max_value=8000, 
                                   value=4000)
    
    content = ""
    if input_type == "URL":
        url = st.text_input("Nhập URL (YouTube hoặc bài viết):")
        if url:
            with st.spinner("Đang lấy nội dung..."):
                if "youtube.com" in url or "youtu.be" in url:
                    content = get_youtube_content(url)
                else:
                    content = get_article_content(url)
    else:
        content = st.text_area("Nhập nội dung cần viết lại:", height=200)
    
    # Style selection
    st.subheader("Phong cách viết")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        style = st.selectbox(
            "Chọn phong cách:",
            ["Tự nhiên", "Học thuật", "Blog", "Báo chí", "Truyện ngắn"]
        )
    
    style_prompts = {
        "Tự nhiên": "Viết với giọng điệu tự nhiên, thân thiện như đang trò chuyện. Sử dụng từ ngữ đời thường, dễ hiểu.",
        "Học thuật": "Viết theo phong cách học thuật, chuyên nghiệp. Sử dụng ngôn ngữ trang trọng và trích dẫn khi cần.",
        "Blog": "Viết theo phong cách blog cá nhân, chia sẻ trải nghiệm. Thêm cảm xúc và quan điểm cá nhân.",
        "Báo chí": "Viết theo phong cách báo chí, khách quan và súc tích. Tập trung vào sự kiện và dữ liệu.",
        "Truyện ngắn": "Viết theo phong cách văn học, tăng tính miêu tả và cảm xúc. Thêm chi tiết sinh động."
    }
    
    # Process button
    if st.button("Viết lại nội dung", type="primary"):
        if not content:
            st.warning("Vui lòng nhập nội dung trước khi viết lại")
            return
            
        progress_bar = st.progress(0)
        
        # Display original content
        st.subheader("Nội dung gốc")
        with st.expander("Xem nội dung gốc"):
            st.text_area("", value=content, height=200, disabled=True)
        
        # Process and display rewritten content
        st.subheader("Nội dung đã viết lại")
        with st.spinner("Đang xử lý..."):
            rewritten = rewrite_content(
                model, 
                content, 
                style_prompts[style],
                progress_bar,
                chunk_size
            )
            st.text_area("", value=rewritten, height=400)
        
        progress_bar.progress(1.0)
        
        # Download button for rewritten content
        st.download_button(
            label="Tải nội dung đã viết lại",
            data=rewritten,
            file_name="rewritten_content.txt",
            mime="text/plain"
        )
        
        st.success("Hoàn thành!")

if __name__ == "__main__":
    main()
