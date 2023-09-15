from youtube_transcript_api import YouTubeTranscriptApi
import re
import base64
from whisper_result import *

def split_text_into_chunks(text, chunk_size, chunk_overlap):
    chunks = []
    start = 0

    while start < len(text):
        # print('start:', start)
        end = min(start + chunk_size, len(text))
        # print('end:', end)
        chunks.append(text[start:end])
        # print('chunks:', chunks)
        start += chunk_size - chunk_overlap

    return chunks
    
def postprocess_time_if_transcript_was_already_generated(time):
    if time < 60:
        sec = int(time)
        return f'0:{sec}'
    
    hour = int(time) // 3600
    min = int(time) // 60
    sec = int(time) % 60 
    if hour == 0:
        return f'{min}:{sec}'
    else:
        return f"{hour}:{abs(hour*60 - min)}:{sec}"
    
def ret_trans(vid):
    # retrieve the available transcripts
    transcript_list = YouTubeTranscriptApi.list_transcripts(vid)

    # iterate over all available transcripts
    for transcript in transcript_list:
        if 'en' in transcript.language_code:
            return transcript.fetch()

        elif transcript.is_translatable and 'en' in [t['language_code'] for t in transcript.translation_languages]:
            return transcript.translate('en').fetch()
        
        else:
            return transcript.fetch()
        
def get_generated_transcript(video_url):
    video_id = video_url.split('=')[1]
    res = ret_trans(video_id)
    
    transcript = ', '.join([f"{postprocess_time_if_transcript_was_already_generated(t['start'])} {t['text']}" for t in res])
    # transcript = [Document(page_content=transcript)]

    return transcript

def extract_start_end_time(passage):
    time_pattern = r'\d{1,2}:\d{1,2}(?::\d{1,2})?'
    
    times = re.findall(time_pattern, passage)
    # print(times)
    if len(times) >= 2:
        start_time = times[1]
        end_time = times[-2]
        # print(times)
        return start_time, end_time
    else:
        return None, None

def decode_unicode(text):
    return bytes(text, "utf-8").decode("unicode-escape")

def get_transcript(video_url):    
    try:  #if the transcript was alrady generated
        transcript = get_generated_transcript(video_url)
        return transcript, 'return_from_generated_transcript'
    # except: #for handling connection issues
    #     return False, 'return_from_generated_transcript'
    except:
        try:
            # s = time.time()
            transcript = get_whisper_result(video_url)
            if transcript:
                return transcript, 'return_from_whisper'
            else:
                return False, ''
        except:
            return False, ''

# Define your FAQ questions and answers
def FAQs():
    faq = {
        "What is VideoQuERI?":"It is a versatile and interactive website that utilizes AI capabilities to process videos, answer questions, generate code, solve puzzles, and perform mathematical operations.\
        It depends that the video is described in someone's voice not visually. If the video's description is solely visual, the algorithm will not function effectively.",

        "What are the Capabilities of VideoQuERI?<ul>" :
        " <li>**Video Processing**: Users can input video URLs to your website. The AI can then process these videos to extract information, such as speech recognition for transcriptions.</li>"
        " <li>**Question Answering**:Users can ask questions related to the video's content. The website's AI can analyze the video's transcriptions and content to provide relevant answers to users' questions.</li>"
        " <li>**Code Generation**: If the video contains step-by-step instructions for coding, AI can extract these instructions and generate code snippets.</li>"
        " <li>**Generating Chapters**: You can ask the bot to help you splitting your video to chapters.</li>"
        " <li>**Puzzle Solving**: Videos with puzzle verbally instructions can be processed by the AI to understand the rules and mechanics. Users can input puzzle-specific queries, and it can provide solutions or hints.</li>"
        " <li>**Memory**: Chatbot has memory to retain and recall information from previous parts of the conversation. But,honestly, it is not that strong.</li>"
        " <li>**Information Retrieval** : If you forget when a piece of information was said, you can provide the video and your question.</li>"
        " <li>**Educational Content**: Your website can serve as an educational platform by offering explanations, demonstrations, and tutorials on various subjects based on the video content.</li>"
        " <li>**Natural Language Understanding**: The AI can understand and analyze the natural language used in both the video's transcriptions and user queries. This allows for more contextually accurate responses.</li>"
        " <li>**Interactive UI**: Your website's user interface can incorporate elements like text input fields, and result displays to make the interactions intuitive and engaging.</li>"
        " <li>**Scalability**: The AI-driven capabilities can be applied to various types of videos, making your website versatile and adaptable to different content.</li> </ul> "        
          ,
    
        "What if the user has already generated transcription (e.g. from platforms like Coursera or Udemy)?":
        "You can copy it and ask ChatGPT or Poe",
        
        "what if Caption generation took a long time?":"There are two propable reasons. First, the video url is not supported. Second, the transcription generation API has too many requuests\
         If the first case, then the video may be streamed to wesite in .ts format , and .ts is not supported .However,if your case is the second case, you can visit the us after a period of time.",
        
        "What if the video is in your local machine?":"You can Upload it to your google drive and then share the link with us.",
        
        "What are supported formats?" :
        "However, most video formats are supported, streaming videos in the .ts format (Transport Stream) are currently not compatible with our system.\
         Transport Stream is a container format often used for streaming live broadcasts and might require specialized processing.\
         If you have a .ts format video, you might consider converting it to a supported format using 'ffmpeg' and upload it to your drive and share the link with us.\
         We appreciate your understanding and are here to assist you with any questions you may have! ",
        
        "How can I get the video link?":
        """You should install this <a href="https://chrome.google.com/webstore/detail/video-downloadhelper/lmjnegcaeklhafolokijcfjliaokphfk?hl=es">chrome extension</a>, \
           <a href = "https://addons.mozilla.org/en-US/firefox/addon/video-downloadhelper/">firefox extension</a>.\
           If you are in the webpage that has the desired video click on the extension logo , a menu will be listed , click copy url, finally paste in the video url input field.
        """ ,

        "What languages are supported?" : 
        "Afrikaans, Arabic, Armenian, Azerbaijani, Belarusian, Bosnian, Bulgarian, Catalan, Chinese, Croatian, Czech, Danish, Dutch, English, Estonian, Finnish, French,\
         Galician, German, Greek, Hebrew, Hindi, Hungarian, Icelandic, Indonesian, Italian, Japanese, Kannada, Kazakh, Korean, Latvian, Lithuanian, Macedonian, Malay, Marathi,\
         Maori, Nepali, Norwegian, Persian, Polish, Portuguese, Romanian, Russian, Serbian, Slovak, Slovenian, Spanish, Swahili, Swedish, Tagalog, Tamil, Thai, Turkish, Ukrainian, Urdu, Vietnamese, and Welsh.",
        
        "Is there a tip to get the most out of VideoQuERI":"Yes, you should ask your question in English and ask the bot to answer in your favourite language(e.g. What is this video about? answer in 'arabic').",
        
        "What is the purpose of the video URL field?":
        "The video URL field allows you to input the URL of the video you want to query.Our system will analyze the video content to provide relevant answers.",

        "How do I input a video URL, especially for platforms like Facebook or embedded videos?":
        "To input a video URL, simply copy the URL of the video you want to query and paste it into the video URL field.",

        "What is the chunk size slider for?":
        "The chunk size slider lets you adjust the size of video segments that the system analyzes. This can help you get more focused and precise answers based on specific parts of the video.",

        "How does the system generate answers from the video?":
        "Our system uses advanced AI technology to analyze the video's audio content. It then generates answers based on the context and content of the video.",

        "Is there a limit to the video length I can query?":
        "While there's generally no strict limit on video length, very long videos might take longer to process. It's recommended to choose appropriate chunk sizes for efficient processing and accurate answers.",

        "Can I change the chunk size while the video is being processed?":
        "No, you can adjust the chunk size slider after generating the caption then click `Generate the Caption` button again . This allows you to explore different parts of the video and get answers for specific segments.",

        "Can I ask questions while the caption is being generated?":
        "No, you can ask questions after the caption generation is completed.",

        "How accurate are the answers generated from the video?":
        "The accuracy of answers depends on various factors such as the clarity of the audio, and the specificity of your questions. Generally, the system strives to provide relevant and coherent answers.",

        "Can I save or bookmark specific answers from the video?":
        "At the moment, the system doesn't offer direct saving or bookmarking of answers. However, you can take screenshots or notes to keep track of important information.",

        "Are there certain types of videos that work better with this feature?":
        "The system is designed to work with a wide range of videos, but videos with clear audio tend to yield better results. Educational, instructional, and well-structured videos are usually more suitable."


    }
    # # with st.expander("FAQs"):
    # for i, faq_key in enumerate(faq.keys()):
    #     # with st.sidebar.expander(faq_key):
    #     st.write(f"**Q{i+1}. {faq_key}**\n \n**Answer** : {faq[faq_key]}", unsafe_allow_html=True)
    #     st.write('-'*50)

def contact():
    mail = """<h2><a href="mailto:nemo45627@gmail.com">Email</a></h2>"""
    linkedin = """<h2><a href="https://www.linkedin.com/in/mohamed-algebali-213672173/">Linkedin</a></h2>"""

    con = f"""
        <h1>We can contact via :
        <ul>
            <li>{mail}</li>
            <li>{linkedin}</li>
        </ul>
        </h1>
"""
    # st.markdown(con, unsafe_allow_html=True)

def donate():
    pass

def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# # logo='vqueri.png'
# # img = get_img_as_base64(logo)

# # page_bg_img = f"""
# # <style>
# # [data-testid="stAppViewContainer"] > .main {{
# # # background-image: url("data:image/jpeg;base64,{img}");
# # # background-size: auto;
# # # # opacity:0.8;
# # # background-position: center;
# # # background-repeat: no-repeat;
# # # background-attachment: local;

# # }}

# # [data-testid="stSidebar"] > div:first-child {{
# # # background-image: url("data:image/jpeg;base64,{img}");
# # background-position: center; 
# # background-repeat: no-repeat;
# # background-attachment: fixed;
# # }}

# # [data-testid="stHeader"] {{
# # margin-top: 0px;

# # background: rgba(0,0,0,0);
# # }}

# # [data-testid="stToolbar"] {{
# # right: 2rem;
# # }}

# # [data-testid="stExpander"]{{
# # margin-top:50px
# # }}


# # [data-testid="stVerticalBlock"]{{
# # margin-top: -5px;
# # # margin-top:30px
# # }}
# # </style>
# # """

# # html_code = """
# <div style="display: flex;justify-content: center;align-items: center;">
#     <h1 style='text-align: center; color: '#6c757d';'>VideoQuERI, Chatting with Videos made Easy</h1>
#     <img style="width: 150px; margin-right: 10px; border-radius:50px "" src="data:image/jpeg;base64,{}" alt="Image Description">
# </div>
# """.format(img)


