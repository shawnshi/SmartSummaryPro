from calibre.customize import Plugin

class SmartSummaryProPlugin(Plugin):
    name                = 'SmartSummary Pro'
    description         = 'Generate deep literary summaries using AI models.'
    supported_platforms = ['windows', 'osx', 'linux']
    author              = 'Gemini User'
    version             = (1, 0, 0)
    minimum_calibre_version = (5, 0, 0)
    type                = 'Interface'

    # actual_plugin = '...'  <-- Removed string reference
    
    def load_actual_plugin(self, gui):
        from .ui import SmartSummaryProAction
        return SmartSummaryProAction(gui, self.site_customization)

    def is_customizable(self):
        return True

    def config_widget(self):
        from .config import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()
