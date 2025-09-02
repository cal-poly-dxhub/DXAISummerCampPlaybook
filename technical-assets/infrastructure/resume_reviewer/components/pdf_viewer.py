import streamlit as st
import base64
import json

class PDFViewer:
    @staticmethod
    def display_pdf_native(pdf_file):
        """Display PDF in its native format"""
        base64_pdf = base64.b64encode(pdf_file.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

    @staticmethod
    def is_youtube_url(url):
        """Check if URL is a YouTube URL"""
        if not url:
            return False
        youtube_patterns = [
            'youtube.com/watch?v=',
            'youtu.be/',
            'youtube.com/embed/'
        ]
        return any(pattern in url.lower() for pattern in youtube_patterns)

    @staticmethod
    def display_video_content(url, index):
        """Display video content - either embedded YouTube or link"""
        if PDFViewer.is_youtube_url(url):
            # Extract video ID
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0]
            elif "embed/" in url:
                video_id = url.split("embed/")[1].split("?")[0]
            else:
                st.write(f"Video {index}: {url}")
                return

            # Create embedded iframe
            st.markdown(f"""
                <iframe width="100%" height="400"
                    src="https://www.youtube.com/embed/{video_id}"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen>
                </iframe>
            """, unsafe_allow_html=True)
        else:
            # Display as regular link
            st.write(f"Video {index}: [{url}]({url})")

    @staticmethod
    def display_resume_package(content_package):
        """Display resume and supplemental content"""
        if not content_package:
            st.error("Failed to load resume content")
            return False

        try:
            # Create list of tabs
            tab_titles = ["Resume"]
            
            # Add supplemental PDF tabs
            supplemental_pdfs = []
            i = 0
            while f'supplemental_file_{i}' in content_package:
                tab_titles.append(f"Supplemental {i+1}")
                supplemental_pdfs.append(content_package[f'supplemental_file_{i}'])
                i += 1
            
            # Add videos tab if videos exist in supplemental.json
            supplemental_json = content_package.get('supplemental_json')
            has_videos = False
            video_links = []
            if supplemental_json:
                try:
                    data = json.loads(supplemental_json)
                    if data.get('YouTubeLink') or data.get('YouTubeLink2'):
                        has_videos = True
                        if data.get('YouTubeLink'):
                            video_links.append(data['YouTubeLink'])
                        if data.get('YouTubeLink2'):
                            video_links.append(data['YouTubeLink2'])
                        tab_titles.append("Supplemental Videos")
                except json.JSONDecodeError:
                    pass

            # Create tabs
            tabs = st.tabs(tab_titles)
            
            # Display main resume in first tab
            with tabs[0]:
                PDFViewer.display_pdf_native(content_package['resume'])
            
            # Display supplemental PDFs
            for i, pdf in enumerate(supplemental_pdfs):
                with tabs[i+1]:
                    PDFViewer.display_pdf_native(pdf)
            
            # Display videos if they exist
            if has_videos:
                with tabs[-1]:
                    for i, video_url in enumerate(video_links, 1):
                        st.subheader(f"Video {i}")
                        PDFViewer.display_video_content(video_url, i)

            return True

        except Exception as e:
            st.error(f"Error displaying the resume package: {str(e)}")
            return False