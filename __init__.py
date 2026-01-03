from calibre.customize import InterfaceActionBase

class SmartSummaryProPlugin(InterfaceActionBase):
    name                = 'SmartSummary Pro'
    description         = 'Generate deep literary summaries using AI models.'
    supported_platforms = ['windows', 'osx', 'linux']
    author              = 'shawn shi'
    version             = (1, 1, 1)
    minimum_calibre_version = (5, 0, 0)
    
    # InterfaceActionBase automatically sets type = 'User Interface Action'
    actual_plugin       = 'calibre_plugins.smart_summary_pro.ui:SmartSummaryProAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        from .config import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()
