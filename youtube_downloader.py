import streamlit as st
import yt_dlp
import os
import tempfile
import logging
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure page settings
st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="🎥",
    layout="centered"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #ffffff 0%, #ffe5e5 50%, #ffcccc 100%);
    }
    .main {
        padding: 2rem;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
    }
    .download-header {
        background: linear-gradient(to right, #FF0000, #CC0000);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(255, 0, 0, 0.2);
    }
    .stButton button {
        background-color: #FF0000;
        color: white;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(255, 0, 0, 0.2);
    }
    .stButton button:hover {
        background-color: #CC0000;
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(255, 0, 0, 0.3);
    }
    .stRadio > label, .stSelectbox > label {
        font-size: 1.2rem;
        font-weight: bold;
        color: #444;
    }
    .element-container, .stTextInput > label {
        color: #333;
    }
    div[data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    .stRadio > div[role="radiogroup"] label {
        color: #808080 !important;
    }
    .stRadio > label {
        font-size: 1.2rem;
        font-weight: bold;
        color: #808080 !important;
    }
    .stRadio > div[role="radiogroup"] div {
        color: #808080 !important;
    }
    .stExpander > div[role="button"] {
        color: #808080 !important;
    }
    .stExpander > div[role="button"] > div {
        color: #808080 !important;
    }
    .stExpander > div[role="button"]:hover {
        color: #808080 !important;
    }
    .stExpander > div[role="button"] > div:hover {
        color: #808080 !important;
    }
    .stExpander > div[role="button"] > div > div {
        color: #808080 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="download-header">
        <h1>YouTube video Downloader</h1>
        <p>Download your favorite videos and audio with ease  !</p>
    </div>
    """, unsafe_allow_html=True)

def create_progress_hook(progress_bar):
    def progress_hook(d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes:
                progress = downloaded_bytes / total_bytes
                progress_bar.progress(progress, f"Downloading: {progress:.1%}")
    return progress_hook

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def download_video(url, quality='720p'):
    progress_bar = st.progress(0)
    with tempfile.TemporaryDirectory(dir='/tmp') as temp_dir:
        logging.debug(f"Temporary directory: {temp_dir}")
        # Define quality formats
        quality_formats = {
            'highest': 'bestvideo+bestaudio/best',
            '2160p': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
            '1440p': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
        }
        
        try:
            # First extract info without downloading
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                sanitized_title = sanitize_filename(info['title'])
                
            # Then download with sanitized filename
            ydl_opts = {
                'format': quality_formats.get(quality, quality_formats['720p']),
                'merge_output_format': 'mp4',
                'outtmpl': os.path.join(temp_dir, f"{sanitized_title}.%(ext)s"),
                'progress_hooks': [create_progress_hook(progress_bar)],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                video_path = os.path.join(temp_dir, f"{sanitized_title}.mp4")
                logging.debug(f"Video path: {video_path}")
                
                with open(video_path, 'rb') as f:
                    content = f.read()
                progress_bar.progress(1.0, "Download Complete!")
                return content, sanitized_title
        except Exception as e:
            logging.error(f"Download error: {str(e)}")
            st.error(f"Download error: {str(e)}")
            st.error("Please check the URL or try a different video.")
            return None, None

def download_audio(url):
    progress_bar = st.progress(0)
    with tempfile.TemporaryDirectory(dir='/tmp') as temp_dir:
        logging.debug(f"Temporary directory: {temp_dir}")
        try:
            # First extract info without downloading
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                sanitized_title = sanitize_filename(info['title'])
                
            # Then download with sanitized filename
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_dir, f"{sanitized_title}.%(ext)s"),
                'progress_hooks': [create_progress_hook(progress_bar)],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                audio_path = os.path.join(temp_dir, f"{sanitized_title}.mp3")
                logging.debug(f"Audio path: {audio_path}")
                
                with open(audio_path, 'rb') as f:
                    content = f.read()
                progress_bar.progress(1.0, "Download Complete!")
                return content, sanitized_title
        except Exception as e:
            logging.error(f"Download error: {str(e)}")
            st.error(f"Download error: {str(e)}")
            st.error("Please check the URL or try a different video.")
            return None, None

# Modify the columns layout to accommodate quality selection
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    url = st.text_input("🔗 Enter YouTube URL:", placeholder="https://youtube.com/...")

with col2:
    download_type = st.radio(
        " Format:",
        ["Video", "Audio"],
        help="Choose between video (MP4) or audio (MP3)"
    )

with col3:
    if download_type == "Video":
        quality = st.selectbox(
            " Quality:",
            ["highest", "2160p", "1440p", "1080p", "720p", "480p", "360p"],
            index=3,  # Default to 1080p
            help="Select video quality"
        )

# Remove the existing "How to use" section
# Info box
# with st.expander("ℹ How to use"):
#     st.markdown("""
#     1. Paste a YouTube URL in the input field
#     2. Select your preferred format (Video/Audio)
#     3. Click the Download button
#     4. Wait for processing
#     5. Click 'Save' when ready
#     """)

if st.button("⬇ Download", help="Start downloading"):
    if url:
        try:
            with st.spinner("🎵 Processing your request..."):
                if download_type == "Video":
                    content, title = download_video(url, quality)
                    file_extension = "mp4"
                    icon = "🎥"
                else:
                    content, title = download_audio(url)
                    file_extension = "mp3"
                    icon = "🎵"
                
                if content:
                    st.success(f" Ready to save! {'(Quality: ' + quality + ')' if download_type == 'Video' else ''}")
                    
                    # Styled download button
                    st.markdown("""
                        <style>
                        .stDownloadButton button {
                            background-color: #00CC00 !important;
                            color: white;
                            padding: 0.5rem 2rem;
                            font-weight: bold;
                        }
                        .stDownloadButton button:hover {
                            background-color: #009900 !important;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    st.download_button(
                        label=f"{icon} Save {download_type}",
                        data=content,
                        file_name=f"{title}.{file_extension}",
                        mime=f"{'video' if download_type == 'Video' else 'audio'}/{file_extension}",
                        key="download_button"
                    )
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            st.error(f" Error: {str(e)}")
    else:
        st.warning("⚠️ Please enter a YouTube URL")
