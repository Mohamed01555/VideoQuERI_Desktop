import time
from gradio_client import Client
import pytube
from pytube.exceptions import VideoUnavailable
   
try:
    client = Client("https://sanchit-gandhi-whisper-jax.hf.space/")
except:
    print('ConnectionError')
def get_whisper_res_if_the_video_is_youtube_video(video_url, max_recursion_time=20):
    start_time = time.time()  # Get the start time
    while True:
        try:
                    result = client.predict(
                            video_url,	# str  in 'YouTube URL' Textbox component
                            "translate",	# str  in 'Task' Radio component
                            True,	# bool  in 'Return timestamps' Checkbox component
                            fn_index=6)
                    # print('return from fn_index=6')
                    return result
        
        except:
        
            try:
                result = client.predict(
                                video_url,	# str  in 'YouTube URL' Textbox component
                                "translate",	# str  in 'Task' Radio component
                                True,	# bool  in 'Return timestamps' Checkbox component
                                fn_index=7)
                # print('return from fn_index=7')
                return result	
            
            except:
        
                try:
                            result = client.predict(
                        video_url,	# str  in 'YouTube URL' Textbox component
                        "translate",	# str  in 'Task' Radio component
                        True,	# bool  in 'Return timestamps' Checkbox component
                        api_name="/predict_2")
                            # print('return from /predict_2')
                            return result
                except:
                                if time.time() - start_time > max_recursion_time:
                                    # result = get_whisper_res_if_the_video_is_not_youtube_video(video_url)
                                    # return result
                                    return 
                                time.sleep(2)
                                continue
			
def get_whisper_res_if_the_video_is_not_youtube_video(video_url, max_recursion_time = 20):
    start_time = time.time()  # Get the start time
    while True:
        try:
            result = client.predict(
                    video_url,	# str (filepath or URL to file) in 'inputs' Audio component
                    "translate",	# str  in 'Task' Radio component
                    True,	# bool  in 'Return timestamps' Checkbox component
                    api_name="/predict")
            return result
        
        except:
            try:
                result = client.predict(
                                video_url,	# str  in 'YouTube URL' Textbox component
                                "translate",	# str  in 'Task' Radio component
                                True,	# bool  in 'Return timestamps' Checkbox component
                                api_name="/predict_1")
                return result
            
            except:
                if time.time() - start_time > max_recursion_time:
                    result = get_whisper_res_if_the_video_is_youtube_video(video_url)
                    return result 
                    
                time.sleep(2)
                continue

def postprocess_timestamps(result, index):
    output_list = []
    for text in result[index].split('\n'):
        start = text.split(' -> ')[0][1:]
        if len(start.split(':')) == 2: #there are only minutes and seconds   
            min = int(start.split(':')[0])
            sec = int(float(start.split(':')[1]))
            
            index_of_space = text[24:].find(' ')
            # text = text[24+index_of_space:]
            text = ':'.join([str(min), str(sec)]) + text[24+index_of_space:]

            output_list.append(text)
        
        else: #there are hours also
            start = text.split(' -> ')[0][1:]
            
            hour = int(start.split(':')[0])
            min = int(start.split(':')[1])
            sec = int(float(start.split(':')[2]))
            # text = text[30:]

            text = ':'.join([str(hour),str(min),str(sec)]) + text[30:]

            output_list.append(text)  
    return output_list  

def postprocess_whisper_jax_output(result):
    # index = 1 if youtube video, else if non-youtube video
    try:
        output_list = postprocess_timestamps(result, index=1)
    except:
        output_list = postprocess_timestamps(result, index=0)

    return ', '.join(output_list)

def get_whisper_result(video_url):
    # if the link is youtube video
    if 'youtube.com/watch?v=' in video_url:
        try:
            video = pytube.YouTube(video_url)
            video.check_availability()
            
            result =  get_whisper_res_if_the_video_is_youtube_video(video_url)
            transcript = postprocess_whisper_jax_output(result)
            return transcript

        except VideoUnavailable:
            return False
        
    # if the link is not a youtube video
    else:
        result =  get_whisper_res_if_the_video_is_not_youtube_video(video_url)
        if result:
            transcript = postprocess_whisper_jax_output(result)
            return transcript
    
        return False
    