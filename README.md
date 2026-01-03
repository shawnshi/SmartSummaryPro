# SmartSummary Pro

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

1.  Download the plugin ZIP file.
2.  Open Calibre.
3.  Go to **Preferences** -> **Plugins**.
4.  Click **"Load plugin from file"**.
5.  Select the `SmartSummaryPro` ZIP file.
6.  Click **Yes** to confirm security warning.
7.  **Restart Calibre**.

## Configuration

### 1. Add to Toolbar (Required)
By default, the plugin might not appear on your toolbar.
1.  Go to **Preferences** -> **Toolbars & menus**.
2.  Select **"The main toolbar"** (or "The context menu for books...").
3.  Find **SmartSummary Pro** in the **Available actions** list (right side).
4.  Select it and click the **Left Arrow (<-)** button to move it to **Current actions**.
5.  Click **Apply**.

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

*   **Plugin icon not showing?** See "Add to Toolbar" section above.
*   **Import Errors?** Ensure you are using the latest version compatible with Calibre's internal Python environment.
*   **Generation Failed?** Check your API Key and internet connection. Verify you haven't exceeded your daily quota.
