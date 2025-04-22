import kivy
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView

class VisualizationViewer(BoxLayout):
    def __init__(self, **kwargs):
        super(VisualizationViewer, self).__init__(**kwargs)
        self.orientation = 'vertical'

        self.visualization_label = Label(text="Visualization Viewer")
        self.add_widget(self.visualization_label)

        self.file_chooser = FileChooserListView()
        self.add_widget(self.file_chooser)

        self.load_button = Button(text="Load Visualization")
        self.load_button.bind(on_press=self.load_visualization)
        self.add_widget(self.load_button)

    def load_visualization(self, instance):
        selected_file = self.file_chooser.selection
        if selected_file:
            self.show_visualization(selected_file[0])
        else:
            self.show_popup("No file selected.")

    def show_visualization(self, file_path):
        # Placeholder for visualization loading logic
        self.show_popup(f"Loaded visualization from: {file_path}")

    def show_popup(self, message):
        popup = Popup(title='Visualization Viewer',
                      content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()
