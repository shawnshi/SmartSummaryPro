# SmartSummary Pro

**Version: 1.0.6** | [Changelog](#version-history)

**SmartSummary Pro** is a powerful Calibre plugin that leverages advanced AI models to automatically generate deep, literary summaries for your ebook library.

## Features

*   **Multi-Model Support**: Use your preferred AI provider:
    *   OpenAI (GPT-3.5, GPT-4)
    *   DeepSeek
    *   Anthropic (Claude)
    *   Google Gemini (via OpenAI-compatible endpoint)
    *   Custom OpenAI-compatible providers
*   **Intelligent Failover**: Automatically switches to the next configured model if the primary one fails (e.g., due to rate limits or network issues).
*   **Quota Management**: Set daily request limits for each model to control costs and usage.
*   **Batch Processing**: Generate summaries for multiple books in the background without freezing Calibre.
*   **Smart Review**:
    *   **Batch Review Dialog**: Review all generated summaries in a single window.
    *   **Side-by-Side Comparison**: Compare the new AI summary with existing metadata.
    *   **Selective Update**: Choose exactly which summaries to apply or discard.
*   **Customizable Prompts**: Edit the system prompt to tailor the style and depth of the summaries.

## Installation

> **Important**: After installing or updating the plugin, you **must restart Calibre** for the plugin to appear in the toolbar settings.

1.  Download the plugin ZIP file (`SmartSummaryPro.zip`).
2.  Open Calibre.
3.  Go to **Preferences** → **Plugins**.
4.  Click **"Load plugin from file"**.
5.  Select the `SmartSummaryPro.zip` file.
6.  Click **Yes** to confirm the security warning.
7.  **Restart Calibre** (critical step!).
8.  After restart, proceed to the Configuration section below to add the plugin to your toolbar.

## Configuration

### 1. Add to Toolbar (Required)

> **Note**: As of version 1.0.6, the plugin correctly registers as a User Interface Action and will appear in the Available actions list.

The plugin does not automatically appear on your toolbar. You need to add it manually:

1.  Go to **Preferences** → **Toolbars & menus**.
2.  Select **"The main toolbar"** from the dropdown.
3.  Find **SmartSummary Pro** in the **Available actions** list (right side).
4.  Select it and click the **Left Arrow (<-)** button to move it to **Current actions**.
5.  Arrange its position as desired (optional).
6.  Click **Apply**.

The plugin icon should now appear in your main toolbar!

### 2. Configure API Keys
1.  Click the **SmartSummary Pro** icon in the toolbar (or right-click menu) -> **Configure**.
    *   *Alternatively: Go to Preferences -> Plugins -> SmartSummary Pro -> Customize plugin.*
2.  Go to the **Model Management** tab.
3.  Click **Add Model**.
4.  Enter your details:
    *   **Provider**: Select OpenAI, DeepSeek, Gemini, etc.
    *   **API Key**: Your secret API key.
    *   **Daily Limit**: Max requests per day for this model.
5.  Add multiple models if desired. Drag and drop to reorder their priority.

## Usage

1.  Select one or more books in your library.
2.  Click the **SmartSummary Pro** button (or right-click -> SmartSummary Pro).
3.  Confirm the number of books to process.
4.  Wait for the background job to complete.
5.  When finished, the **Review Summaries** dialog will appear.
6.  Review the results:
    *   **Keep**: Selected by default.
    *   **Discard**: Toggle for summaries you don't like.
7.  Click **Process All** to save the approved summaries to your library metadata.

## Requirements

*   Calibre 5.0 or newer (Fully compatible with Calibre 8.x).
*   Active Internet connection.
*   Valid API Key for at least one supported AI provider.

## Troubleshooting

### Plugin Not Appearing in Available Actions?

**Solution**: 
1. Ensure you've installed version **1.0.6 or later** (earlier versions had a plugin type registration issue).
2. Completely **close and restart Calibre** after installation.
3. Check **Preferences** → **Plugins** to verify the plugin is listed and shows version 1.0.6+.

### Plugin Icon Not Showing on Toolbar?

The plugin must be manually added to the toolbar. See the "Add to Toolbar" section in Configuration above.

### Import or Loading Errors?

Ensure you are using a version compatible with your Calibre installation (requires Calibre 5.0+).

### Generation Failed?

*   **No API configured**: Go to plugin settings and add at least one AI model API key.
*   **Network issues**: Check your internet connection.
*   **Quota exceeded**: Verify you haven't exceeded your daily limit for the configured model.
*   **Invalid API key**: Double-check your API key is correct and active.

## Version History

### v1.0.6 (2026-01-03)
*   **Fixed**: Corrected plugin type registration issue that prevented the plugin from appearing in Calibre's toolbar actions list.
*   **Changed**: Migrated from `Plugin` base class to `InterfaceActionBase` for proper Calibre integration.
*   **Improved**: Enhanced documentation with clearer installation and troubleshooting steps.

### v1.0.5 (Previous)
*   Multi-model support with intelligent failover
*   Batch processing and review dialog
*   Customizable prompts
*   Quota management
