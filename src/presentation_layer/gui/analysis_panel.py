import kivy
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button

class AnalysisPanel(BoxLayout):
    def __init__(self, **kwargs):
        super(AnalysisPanel, self).__init__(**kwargs)
        self.orientation = 'vertical'

        self.analysis_label = Label(text="Select analysis options:")
        self.add_widget(self.analysis_label)

        self.analysis_spinner = Spinner(
            text='Select Analysis',
            values=('Basic Statistics', 'Contact Analysis', 'Time Analysis')
        )
        self.add_widget(self.analysis_spinner)

        self.analyze_button = Button(text="Analyze")
        self.analyze_button.bind(on_press=self.analyze)
        self.add_widget(self.analyze_button)

    def analyze(self, instance):
        selected_analysis = self.analysis_spinner.text
        if selected_analysis == 'Basic Statistics':
            print("Performing Basic Statistics analysis...")
        elif selected_analysis == 'Contact Analysis':
            print("Performing Contact Analysis...")
        elif selected_analysis == 'Time Analysis':
            print("Performing Time Analysis...")
        else:
            print("No analysis selected.")
