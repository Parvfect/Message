import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
# to use buttons:
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
import socket_client
from kivy.clock import Clock
import sys
from kivy.core.window import Window

kivy.require("1.10.2")


class ConnectPage(GridLayout):
    # runs on initialization
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cols = 2  # used for our grid

        with open("prev_details.txt","r") as f:
            d = f.read().split(",")
            prev_ip = d[0]
            prev_port = d[1]
            prev_username = d[2]

        self.add_widget(Label(text='IP:'))  # widget #1, top left
        self.ip = TextInput(text=prev_ip, multiline=False)  # defining self.ip...
        self.add_widget(self.ip) # widget #2, top right

        self.add_widget(Label(text='Port:'))
        self.port = TextInput(text=prev_port, multiline=False)
        self.add_widget(self.port)

        self.add_widget(Label(text='Username:'))
        self.username = TextInput(text=prev_username, multiline=False)
        self.add_widget(self.username)

        # add our button.
        self.join = Button(text="Join")
        self.join.bind(on_press=self.join_button)
        self.add_widget(Label())  # just take up the spot.
        self.add_widget(self.join)

    def join_button(self, instance):
        port = self.port.text
        ip = self.ip.text
        username = self.username.text
        with open("prev_details.txt","w") as f:
            f.write(f"{ip},{port},{username}")
        #print(f"Joining {ip}:{port} as {username}")
        # Create info string, update InfoPage with a message and show it
        info = f"Joining {ip}:{port} as {username}"
        chat_app.info_page.update_info(info)
        chat_app.screen_manager.current = 'Info'
        Clock.schedule_once(self.connect,1)
    
    def connect(self,_):
        #Get information for the socket client
        port=int(self.port.text)
        ip=self.ip.text
        username=self.username.text

        if not socket_client.connect(ip,port,username,show_error):
            return

        chat_app.create_chat_page()
        chat_app.screen_manager.current="Chat"

class ChatPage(GridLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.cols=1
        self.rows=2
        
        self.history=Label(height= Window.size[1]*0.9, size_hint_y=None)
        self.add_widget(self.history)

        self.new_message=TextInput(width= Window.size[0]*0.8, size_hint_x=None, multiline=False)
        self.send=Button(text="Send")
        self.bind(on_press=self.send_message)

        #So we want row number 2 to have two columns instead of one, so we create a widget to do it,
        #instead of having the page be designed differently 
        bottom_line=GridLayout(cols=2)
        bottom_line.add_widget(self.new_message)
        bottom_line.add_widget(self.send)
        self.add_widget(bottom_line)
        #To be able to send messages on key down, we need to listen for it
        Window.bind(on_key_down=self.on_key_down)
        Clock.schedule_once(self.focus_text_input,1)
        socket_client.start_listening(self.incoming_message,show_error)

    def on_key_down(self,instance,keyboard,keycode,text,modifiers):
        #Checking if enter key is pressed
        if keycode==40:
            self.send_message(None)
    
    def focus_text_input(self,_):
        #Sets the focus to the text input field
        self.new_message.focus=True

    def incoming_message(self,username,message):
        #Update chat history with username and message
        self.history.update_chat_history(f'[color=20dd10]{username}[/color] > {message}')




    def send_message(self,_):
        message=self.new_message.text
        self.new_message.text=''
        if message:
            self.history.update_chat_history(f'[color=dd2020]{chat_app.connect_page.username.text}[/color] > {message}')
            socket_client.send(message)
        # As mentioned above, we have to shedule for refocusing to input field
        Clock.schedule_once(self.focus_text_input, 0.1)
    


# Simple information/error page
class InfoPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Just one column
        self.cols = 1

        # And one label with bigger font and centered text
        self.message = Label(halign="center", valign="middle", font_size=30)

        # By default every widget returns it's side as [100, 100], it gets finally resized,
        # but we have to listen for size change to get a new one
        # more: https://github.com/kivy/kivy/issues/1044
        self.message.bind(width=self.update_text_width)

        # Add text widget to the layout
        self.add_widget(self.message)

    # Called with a message, to update message text in widget
    def update_info(self, message):
        self.message.text = message

    # Called on label width update, so we can set text width properly - to 90% of label width
    def update_text_width(self, *_):
        self.message.text_size = (self.message.width * 0.9, None)


class EpicApp(App):
    def build(self):

        # We are going to use screen manager, so we can add multiple screens
        # and switch between them
        self.screen_manager = ScreenManager()

        # Initial, connection screen (we use passed in name to activate screen)
        # First create a page, then a new screen, add page to screen and screen to screen manager
        self.connect_page = ConnectPage()
        screen = Screen(name='Connect')
        screen.add_widget(self.connect_page)
        self.screen_manager.add_widget(screen)

        # Info page
        self.info_page = InfoPage()
        screen = Screen(name='Info')
        screen.add_widget(self.info_page)
        self.screen_manager.add_widget(screen)

        return self.screen_manager

    def create_chat_page(self):
        self.chat_page=ChatPage()
        screen=Screen(name="Chat")
        screen.add_widget(self.chat_page)
        self.screen_manager.add_widget(screen)


def show_error(message):
    chat_app.info_page.update_info(message)
    chat_app.screen_manager.current = 'Info'
    Clock.schedule_once(sys.exit, 10)


if __name__ == "__main__":
    chat_app = EpicApp()
    chat_app.run()