import kivy
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

class FileDialog(Popup):
    def __init__(self, **kwargs):
        super(FileDialog, self).__init__(**kwargs)
        self.title = 'Select a File'
        self.size_hint = (0.9, 0.9)

        layout = BoxLayout(orientation='vertical')

        self.file_chooser = FileChooserListView()
        layout.add_widget(self.file_chooser)

        button_layout = BoxLayout(size_hint_y=None, height='40dp')
        self.select_button = Button(text='Select')
        self.select_button.bind(on_press=self.select_file)
        button_layout.add_widget(self.select_button)

        self.cancel_button = Button(text='Cancel')
        self.cancel_button.bind(on_press=self.dismiss)
        button_layout.add_widget(self.cancel_button)

        layout.add_widget(button_layout)
        self.add_widget(layout)

    def select_file(self, instance):
        selected_file = self.file_chooser.selection
        if selected_file:
            self.dismiss()
            self.on_file_selected(selected_file[0])

    def on_file_selected(self, file_path):
        pass  # Override this method to handle the selected file
