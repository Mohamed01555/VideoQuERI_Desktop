from utils import *
import threading  
import webbrowser

from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.scrollview import MDScrollView
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDFillRoundFlatIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.screen import MDScreen
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.slider import MDSlider
from kivymd.uix.gridlayout import MDGridLayout

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager
from kivy.metrics import dp

from kivy.lang import Builder
from kivy.properties import StringProperty , NumericProperty
from asyncio import run
import gpt4_curl, gp4_tls, gpt3

from kivy.event import EventDispatcher
from kivy.core.clipboard import Clipboard

from kivymd.toast import toast
from bidi.algorithm import get_display
from arabic_reshaper import reshape

selcted_chunks = [] # define the choosed chunks after user select them
chunks = None

class VideoQueri(MDApp):
    generated_caption_dict = {}  # Property to store the generated caption
    chunks = None                # Property to store the caption chunks
    def show_toast(self):
        '''Displays a toast on the screen.'''
        toast('Copied To Clipboard')

    def copy_message(self, text):
        Clipboard.copy(text)
    
    def build(self):
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.theme_style = 'Dark'

        self.sm = ScreenManager()

        self.main_screen = Builder.load_file("Main.kv")
        self.caption_screen = CaptionScreen(name='caption_page')
        self.chat_screen = Builder.load_file("chats.kv")
        
        self.sm.add_widget(self.main_screen)
        self.sm.add_widget(self.caption_screen)
        self.sm.add_widget(self.chat_screen)
        return self.sm

    def open_link(self, link):
        webbrowser.open(link)
    
    def wrap_query(self):
        prompt = """
        You are very good at handling very long texts,so I will give you a video transcription (mostly,in english) splitted in small pieces.
        You will get a request about it, you should translate this request to the language of transcription if it isn't,
        then give me the answer in the language of question, or in another one if I asked.
        you should enhance your answer with useful proper resources.\n\n
        
        transcription: {} \n\n
        
        request: {} \n\n
        
        feel free to neglect the given transcription if you see that the request is not related to it like thank you, hello or ok and similars, provide instead an appropriate answer like you are welcome.
        
        you may be asked to provide your answer in specific language like arabic, and you must provide your answer in the asked language.
            
        Your answer:\n\n
        """ 
        if len(selcted_chunks) != 0:
            for i in selcted_chunks:
                print('i:', i)
                print('chunks[i]:', chunks[i])
                prompt = prompt.format(chunks[i], query)
                yield prompt
    
    def decode_unicode(self, text):
        return bytes(text, "utf-8").decode("unicode-escape")
    
    def reshape_arabic_text(self, text):
        reshaped_text = reshape(text)
        return get_display(reshaped_text)
    
    def show_error_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(text="OK", on_release=self.dismiss_dialog)
            ]
        )
        self.error_dialog = dialog  # Store a reference to the dialog
        dialog.open()

    def dismiss_dialog(self, instance):
        self.error_dialog.dismiss()

    def get_response(self, *args):  
        # Show the spinner
        self.show_spinner_chatting()

        # Define a function to run get_bot_answer in a thread
        def run_get_answer():
            if len(selcted_chunks) != 0:
                for q in self.wrap_query():
                    try:  
                        print(q)
                        resp = run(self.get_bot_answer(question = q))
                        resp = self.postprocess_response(resp)
                        resp = self.decode_unicode(resp)
                        resp = self.reshape_arabic_text(resp)  # Apply reshaping and bidi if the text is arabic
                        Clock.schedule_once(lambda dt: self.add_clickable_label(resp), 0)
                    except:
                        Clock.schedule_once(lambda dt: self.show_error_dialog("Invalid Video URL Or Connection error", 
                                       "Most likely it is not a video, you're disconnected to internet,\
                                        or caption generation service if full now. Please try again later."), 0)
                        
                        # Clock.schedule_once(self.hide_spinner, 0)  # Hide the spinner after a short delay
                        return

                    # Add ClickableLabel and hide spinner in the main thread
            else:
                try:
                    resp = run(self.get_bot_answer(question = query))
                    resp = self.postprocess_response(resp)
                    resp = self.decode_unicode(resp)
                    resp = self.reshape_arabic_text(resp)  # Apply reshaping and bidi if the text is arabic
               
                    # Add ClickableLabel and hide spinner in the main thread
                    Clock.schedule_once(lambda dt: self.add_clickable_label(resp), 0)
                except:
                    Clock.schedule_once(lambda dt: self.show_error_dialog("Connection error", "Most likely You're disconnected to Internet, Please Check your connectivity and try again."), 0)
                    # Clock.schedule_once(self.hide_spinner, 0)  # Hide the spinner after a short delay
                    return
        
        # Start a new thread to run get_bot_answer
        threading.Thread(target=run_get_answer).start()
        
    def send(self):
        if self.sm.get_screen('chats').text_input != "":
            global query, size
            query = self.sm.get_screen('chats').text_input.text
            
            #handling the size of the query container based on the query length
            size  = len(query) * 0.03
            if size > 0.7:
                size = 0.7
            print('query : ', query)
            self.sm.get_screen('chats').chat_list.add_widget(Command(text = str(query), size_hint_x=size, halign = "center"))
            # self.sm.get_screen('chats').chat_list.add_widget(MDTextField(text = str(query), size_hint_x=size, multiline=True))
            print('i am in send function',selcted_chunks)
            
            
            Clock.schedule_once(self.get_response, 0)
            self.sm.get_screen('chats').text_input.text = ""
    
    def style_headings(self, text):
        # Define a regular expression to find headings
        # heading_pattern = r'^(#+)\s+(.+)$'
        
        heading_pattern = r'^(#+)\s+([^\n]+)'
        # Find all headings and apply styles
        styled_text = re.sub(heading_pattern, self.style_heading, text, flags=re.MULTILINE)
        
        return styled_text

    def style_heading(self, match):
        # Determine the heading level
        heading_level = len(match.group(1))
        
        # Apply appropriate styles based on heading level
        if heading_level == 1:
            return f'[color=FFFFFF][size=25][b]{match.group(2)}[/b][/size][/color]'
        elif heading_level == 2:
            return f'[color=FFFFFF][size=25][b]{match.group(2)}[/b][/size][/color]'
        elif heading_level == 3:
            return f'[color=FFFFFF][size=25][b]{match.group(2)}[/b][/size][/color]'
        elif heading_level == 4:
            return f'[color=FFFFFF][size=23][b]{match.group(2)}[/b][/size][/color]'
        else:
            return f'[color=FFFFFF][size=21][b]{match.group(2)}[/b][/size][/color]'
        
    def style_bold_text(self, text):
        def style_bold(match):
            bold_text = match.group(1)  # Get the text inside **
            return f'[b][color=FFFFFF]{bold_text}[/color][/b]'
        
        bold_pattern = r'\*\*(.*?)\*\*'
        styled_text = re.sub(bold_pattern, style_bold, text)
        return styled_text
    
    def style_backtick_words(self, text):
        def style_backtick(match):
            backtick_word = match.group(1)  # Get the word inside backticks
            return f'[color=FFFFFF]{backtick_word}[/color]'
        
        backtick_pattern = r'`([^`]+)`'
        styled_text = re.sub(backtick_pattern, style_backtick, text)
        return styled_text
    
    def style_code(self, text):
        def style_triple_backtick(match):
            backtick_word = match.group(1)  # Get the word inside backticks
            return f'[color=FFFFFF]{backtick_word}[/color]'
        
        backtick_pattern = r'```([^`]+)```'
        styled_text = re.sub(backtick_pattern, style_triple_backtick, text, re.DOTALL)
        return styled_text
    
    def style_url(self, match):
        global counter
        url = match.group(0)
        counter += 1
        return f'[color=FF5733][u][ref={url}] [{counter}] [/ref][/u][/color]'

    def postprocess_response(self, response):
        global counter
        counter = 0
        response = re.sub(r'\[\[\d+\]\]', '', response)
        url_pattern = r'https?://[^\s,)]+'
        response = re.sub(url_pattern, self.style_url, response)
        response = self.style_headings(response)  # Apply heading styles
        response = self.style_bold_text(response)
        response = self.style_code(response)  # Apply backtick word styles
        response = self.style_backtick_words(response)  # Apply backtick word styles

        return response
    
    async def get_bot_answer(self, question):
        try:
            # resp = await gpt3.Completion().create(question)
            resp = await gp4_tls.Completion().create(question)
            return resp
        except:
            try:
                resp = await gpt4_curl.Completion().create(question)
                return resp
            except:
                try:
                    resp = await gpt3.Completion().create(question)
                    return resp
                except:
                    return False

    def add_clickable_label(self, resp):
        self.sm.get_screen('chats').chat_list.add_widget(ClickableLabel(
            text=resp,
            size_hint_x=0.77,
            markup=True,
            font_size=22,
        ))
        
        # Hide the spinner
        self.hide_spinner()

    def show_spinner_chatting(self):
        self.sm.get_screen('chats').spinner.active = True
        self.sm.get_screen('chats').spinner.opacity = 1
    
    def hide_spinner(self):
        self.sm.get_screen('chats').spinner.active = False
        self.sm.get_screen('chats').spinner.opacity = 0

    def go_back(self):
        self.sm.transition.direction = 'left'
        self.sm.current = 'caption_page'

class ClickableLabel(MDLabel, EventDispatcher):
    font_name = "Poppins-SemiBold.ttf"
    font_size = 20
    # text_language = 'fa'

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.bind(on_ref_press=lambda instance, x: webbrowser.open(x))

    def copy_text(self, text):
        Clipboard.copy(text)    

class CaptionScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.MAX_CAPTIONS = 10
        self.checkbox_states = {}  # Initialize an empty list to store checkbox states

        layout = MDScreen()
        
        self.sub_layout = BoxLayout(orientation= 'vertical',
        spacing= '10dp',
        padding= '0dp',
        size_hint_x= None,
        width= dp(600),  # Adjust the width as needed
        pos_hint= {'center_x': 0.5}
        )

        self.url_input_field = MDTextField(
            hint_text= "Paste the Video URL here...",
            mode= "rectangle",
            helper_text_mode= "on_error",
            required= True,

            size_hint_y= None,
            height= "40dp",
            pos_hint={'center_x':0.5},
        )
        
        self.chars_text = MDLabel(
            text= "Enter the number of characters for each chunk : ",
            height= "0dp",
            halign='center',
            pos_hint={'center_x':0.5}
            )
        
        self.slider = MDSlider(
            min= 1000,
            max= 20000,
            value= 5000,
            size_hint_y= None,
            height= "30dp",
            pos_hint={'center_x':0.5}
        )

        self.slider.bind(value=self.update_info_text)  # Bind the slider's value property to the update_info_text method
        
        self.info_text = MDLabel(
            text= f"Number of characters for each chunk: {str(int(int(self.slider.value)))}",
            height= "0dp",
            halign='center',
            pos_hint={'center_x':0.5}
            )
    
        self.gen_button = MDFillRoundFlatIconButton(
            text= "Generate Caption \nthen please choose chunks you wanna ask about!",
            on_release= self.generate_caption,
            pos_hint={'center_x':0.5, 'center_y':0}
        )
        
        self.scroll_chunks = MDScrollView(
            size_hint_y= None,
            height= "300dp",
            # pos_hint:{'center_x':0}
        )

        self.gotochat_button = MDFillRoundFlatIconButton(
            text= "Go to ask your questions..",
            pos_hint={'center_x':0.5},
            on_release= self.go_to_chat_page  # Define your button action method
        )
        
        self.success_label_layout = MDFloatLayout()
        self.success_label = MDLabel(
            text="",  # Initial text is empty
            halign="center",
            theme_text_color="Secondary",
            pos_hint = {'center_x': 0.5}#, 'center_y': 0.6}
        )

        # Create the "Back" button
        back_button = MDIconButton(
            icon='arrow-left',
            pos_hint={'x': 0, 'top': 1},
            on_release=self.go_back
        )
         
        # Create a horizontal layout for the "Back" button and input text
        self.back_and_input_layout = BoxLayout(
            orientation='horizontal',
            spacing='10dp',
            size_hint_y=None,
            height="58dp",  # Adjust the height as needed
            pos_hint={'center_x': 0.5},
        )

        self.grid = MDGridLayout(cols=1, spacing="100dp",padding='70dp',size_hint_y=None)

        self.grid.bind(minimum_height=self.grid.setter("height"))
        
        # Add the "Back" button and input text to the horizontal layout
        self.back_and_input_layout.add_widget(back_button)
        self.back_and_input_layout.add_widget(self.url_input_field)

        # self.sub_layout.add_widget(back_button)
        self.sub_layout.add_widget(self.back_and_input_layout)
        self.sub_layout.add_widget(self.chars_text)
        self.sub_layout.add_widget(self.slider)
        self.sub_layout.add_widget(self.info_text)

        self.sub_layout.add_widget(self.gen_button)  
        self.sub_layout.add_widget(self.scroll_chunks)
        self.sub_layout.add_widget(self.gotochat_button)  
        
        self.success_label_layout.add_widget(self.success_label)
        self.sub_layout.add_widget(self.success_label_layout)
        
        layout.add_widget(self.sub_layout)  
        self.add_widget(layout)
    
    def go_to_chat_page(self, instance):
        global selcted_chunks
        self.manager.transition.direction = 'left'
        self.manager.current = 'chats'  
        selcted_chunks = self.get_selected_checkboxes()
        print('i am in go_to_chat_page function',selcted_chunks)

    def go_back(self, instance):
        self.manager.transition.direction = 'right'
        self.manager.current = 'main'
    
    def show_spinner(self):
        self.spinner = MDSpinner(
        size_hint=(None, None),
        size=(32, 32),
        palette=[[0.28627450980392155, 0.8431372549019608, 0.596078431372549, 1],
                    [0.3568627450980392, 0.3215686274509804, 0.8666666666666667, 1],
                    [0.8862745098039215, 0.36470588235294116, 0.592156862745098, 1],
                    [0.8784313725490196, 0.9058823529411765, 0.40784313725490196, 1]],
        pos_hint = {'center_x': 0.5}
        )
        self.add_widget(self.spinner)
        self.spinner.active = True

    def hide_spinner(self, dt):
        self.remove_widget(self.spinner)
        self.spinner.active = False
    
    def update_info_text(self, instance, value):
        # Update the info_text label with the current slider value
        self.info_text.text = f"Number of characters for each chunk: {int(value)}"
    
    def generate_caption(self, instance):
        # Implement your caption generation logic here
        self.video_url = self.url_input_field.text
        if (self.video_url.strip().startswith('http') or self.video_url.strip().startswith('https')):
            self.show_spinner()  # Show the spinner
            
            threading.Thread(target=self.generate_caption_thread).start()  # Start the caption generation thread
            
            Clock.schedule_once(self.hide_success_label, 6)  # Schedule hide after 6 seconds

        else:            
            # Show an error message
            self.show_error_dialog("Invalid URL", "Valid URL must start with http:// or https://")

    def generate_caption_thread(self):       
        # Store the generated caption dict and video chunks in the App's property
        app = MDApp.get_running_app()
        global chunks
        if self.video_url not in app.generated_caption_dict.keys():
            caption, ret = get_transcript(self.video_url)

            if caption:
                if ret == 'return_from_whisper':
                    app.generated_caption_dict[self.video_url] = caption
                # text_splitter = RecursiveCharacterTextSplitter(chunk_size = int(self.slider.value), chunk_overlap=20)
                chunks = split_text_into_chunks(text=caption, chunk_size = int(self.slider.value), chunk_overlap=20)
                # print(chunks)
            else:
                Clock.schedule_once(lambda dt: self.show_error_dialog("Invalid Video URL Or Connection error", 
                                       "Most likely it is not a video, you're disconnected to internet,\
                                        or caption generation service if full now. Please try again later."), 0)
                Clock.schedule_once(self.hide_spinner, 0)  # Hide the spinner after a short delay
                return
        else:
            caption = app.generated_caption_dict[self.video_url]
            # text_splitter = RecursiveCharacterTextSplitter(chunk_size = int(self.slider.value), chunk_overlap=20)
            # chunks = text_splitter.split_text(caption)
            chunks = split_text_into_chunks(text=caption, chunk_size = int(self.slider.value), chunk_overlap=20)
            # print(chunks)


        
        # Limit the number of stored captions
        if len(app.generated_caption_dict) > self.MAX_CAPTIONS:
            oldest_url = next(iter(app.generated_caption_dict))
            app.generated_caption_dict.pop(oldest_url)
        
        
        def add_checkbox(dt):
            self.scroll_chunks.clear_widgets()
            self.grid.clear_widgets()
            for c,doc in enumerate(chunks):        
                start, end = extract_start_end_time(doc)
                
                if start is not None and end is not None:
                    t = f'Chunk {c+1} : from {start} to {end}'
                    box = BoxLayout(orientation="horizontal", spacing="10dp")
                    checkbox = MDCheckbox(size_hint_y=None)
                    label = MDLabel(text=t, size_hint_y=None)

                    # Bind the checkbox's active property to a callback function
                    checkbox.bind(active=lambda checkbox, value, idx=c: self.update_checkbox_state(idx, value))
                    
                    box.add_widget(checkbox)
                    box.add_widget(label)
                    
                    self.grid.add_widget(box)
            
            self.scroll_chunks.add_widget(self.grid)
        
        Clock.schedule_once(add_checkbox, 0)

        # Hide the spinner
        Clock.schedule_once(self.hide_spinner, 0)  # Hide the spinner after a short delay
        
        # Show the success label
        self.show_success_label()
        
        # hide the success label after a short delay
        Clock.schedule_once(self.hide_success_label, 5)  
    
    def update_checkbox_state(self, idx, value):
        # Update the checkbox state list at the specified index
        self.checkbox_states[idx] = value
        print('I am in update_checkbox_state function',self.checkbox_states)
    
    def get_selected_checkboxes(self):
        selected_checkboxes = []
        for idx, state in self.checkbox_states.items():
            if state:
                selected_checkboxes.append(idx)
        print('I am in get_selected_checkboxes function',selected_checkboxes)
        return selected_checkboxes

    def show_success_label(self):
        self.success_label.text = "Caption generated successfully! You can ask now."

    def hide_success_label(self, dt):
        self.success_label.text = ""

    def show_error_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(text="OK", on_release=self.dismiss_dialog)
            ]
        )
        self.error_dialog = dialog  # Store a reference to the dialog
        dialog.open()
    
    def dismiss_dialog(self, instance):
        self.error_dialog.dismiss()

class Command(MDLabel):
    text = StringProperty()
    size_hint_x = NumericProperty()
    halign = StringProperty()
    font_name = "Poppins-SemiBold.ttf"
    font_size = 20

## to support arabic in textinput field
# class Ar_text(TextInput):
#     max_chars = NumericProperty()  # maximum character allowed
#     str = StringProperty()

#     def __init__(self, **kwargs):
#         super(Ar_text, self).__init__(**kwargs)
#         # self.text = get_display(arabic_reshaper.reshape("اطبع شيئاً"))
#         # self.str = self.str+substring

#     def insert_text(self, substring, from_undo=False):
#         reversed_substring = substring[::-1]

#         self.str = self.str + reversed_substring
#         self.text = get_display(reshape(self.str))
        
#         substring = ""
        
#         super(Ar_text, self).insert_text(substring, from_undo)

#     def do_backspace(self, from_undo=False, mode='bkspc'):
#         self.str = self.str[0:len(self.str)-1]
#         print('str: ',self.str)
#         self.text = get_display(reshape(self.str))
#         print('text:',self.text)

#         # self.str = ""
if __name__ == '__main__':
    VideoQueri().run()