from calibre.customize import Plugin

class SmartSummaryProPlugin(Plugin):
    name                = 'SmartSummary Pro'
    description         = 'Generate deep literary summaries using AI models.'
    supported_platforms = ['windows', 'osx', 'linux']
    author              = 'shawn shi'
    version             = (1, 0, 5)
    minimum_calibre_version = (5, 0, 0)
    type                = 'Interface'

    # The strict requirement for the interface action visibility:
    actual_plugin       = 'calibre_plugins.smart_summary_pro.ui:SmartSummaryProAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        from .config import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()
