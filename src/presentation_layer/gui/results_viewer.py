import kivy
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

class ResultsViewer(BoxLayout):
    def __init__(self, **kwargs):
        super(ResultsViewer, self).__init__(**kwargs)
        self.orientation = 'vertical'

        self.results_label = Label(text="Analysis Results:")
        self.add_widget(self.results_label)

        self.results_text = TextInput(multiline=True, readonly=True)
        self.add_widget(self.results_text)

    def display_results(self, results):
        self.results_text.text = results
