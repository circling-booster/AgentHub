# **Melon MCP Server Integration Guide**

original source : [Melon MCP | 카카오엔터테인먼트 테크블로그](https://tech.kakaoent.com/ai/using-melon-mcp-server-en/)

🚧 **Beta Feature**

By enabling this app integration, you acknowledge that you are using an experimental Model Context Protocol (MCP) server to connect Melon with external large language models (LLMs). As this is an experimental beta tool, it is provided on an “as is” basis. You may encounter bugs, errors, or unexpected results.

## **Overview**

Melon provides a Model Context Protocol (MCP) server that allows AI assistants and other applications to securely access Melon’s comprehensive music data and services. This server offers a way to interact with the Melon music platform through various AI platforms and tools that support MCP, such as Claude by Anthropic and PlayMCP by Kakao.

With this server, Melon MCP users can perform tasks such as:

* Search and discover music content from Melon’s vast catalog  
* Access real-time music charts and rankings  
* Get personalized music recommendations  
* Retrieve detailed information about songs, albums, and artists  
* Manage personal music collections and playlists  
* Access music streaming statistics and reports  
* Explore music genres and curated content

## **Getting Started**

### **Requirements**

* A compatible MCP client (e.g., Claude.ai, Claude Desktop, PlayMCP, or any application implementing an MCP client)  
* Valid Melon account credentials  
* Active Melon subscription (may be required for full access to premium features)

### **Connection Details**

* **Endpoint URL (Streamable HTTP):** https://mcp.melon.com/mcp  
* **Authentication:** OAuth 2.0

Use the Endpoint URL above when configuring your AI client. When you connect, a standard OAuth 2.0 authentication process will begin, granting API access upon user consent.

**Authentication Notes:**

While the Melon MCP server is publicly accessible, the OAuth redirect URI allowlist and client credentials issuance are managed via a whitelist. Therefore, you may need to contact **\[Melon Customer Support (melon\_info@kakaoent.com)\]** to register your information before use.

### **Supported Clients**

The Melon MCP server officially supports integration with the following clients:

* Anthropic [Claude.ai](https://claude.ai/) & Claude Desktop  
* Kakao [PlayMCP](https://playmcp.kakao.com/mcp/4)

### **Using with Claude.ai**

1. Navigate to claude.ai.  
2. Click on the Tools menu.  
3. Enable the “Melon” connector from the list of available connectors.  
4. If it’s your first time, you will be prompted to “Connect” and go through the Melon account authentication process.  
5. Once authenticated, you can start using Melon’s features within Claude.

## **Security Best Practices**

To use Melon MCP securely, please adhere to the following recommendations:

* **Verify the Official Endpoint:** Always ensure you are connecting through the official Endpoint URL (https://mcp.melon.com/mcp).  
* **Enable User Confirmation:** For critical actions (e.g., playing music, managing playlists), it is recommended to design workflows where the AI agent gets explicit confirmation from the user. This helps prevent unintended actions.  
* **Beware of Prompt Injection:** If constructing prompts with external input, carefully validate and sanitize the input to prevent malicious instructions from being included.

## **Usage Examples**

| User Prompt | Tools Used | Description |
| :---- | :---- | :---- |
| “Find some upbeat songs for a workout.” | search\_melon\_music\_contents | Search for playlists using keywords like ‘workout’ and ‘upbeat’. |
| “What song did I listen to the most around this time last year?” | get\_my\_most\_listened\_songs | Query the user’s listening history for a specific period. |
| “Recommend a song with a similar style to this one.” | recommend\_similar\_songs\_by\_dj\_mallang | Recommend similar songs based on the ID of the currently playing track. |
| “Show me the latest TOP 100 chart and play the first song.” | get\_music\_chart, create\_playback\_url | Fetch the chart and pass the retrieved song ID to the playback tool. |
| “What was my most played song this month?” | get\_my\_most\_listened\_songs | Retrieve the user’s listening rank for “this month”. |
| “Tell me about \[Artist\]‘s latest album.” | search\_melon\_music\_contents, get\_music\_content\_details | Search for albums in chronological order and fetch details. |
| “Recommend some music that fits my taste.” | recommend\_personalized\_songs\_by\_dj\_mallang | Analyze listening history and preferences for recommendations. |
| “Find a Melon magazine article about musicals.” | search\_melon\_magazines | Search Melon’s music magazine (Music Story) using keywords. |

## **Tool Reference**

### **Music Search & Discovery**

| Name | Description | Sample Prompt |
| :---- | :---- | :---- |
| search\_melon\_music\_contents | Search for songs, albums, artists, and playlists by keyword. | “Search for IU’s ‘Through the Night’” |
| search\_melon\_magazines | Search for music magazines, interviews, and editorial content. | “Find the latest magazine article about IU” |
| get\_music\_chart | Retrieve official Melon music charts (TOP 100, Daily, Weekly). | “Show me the TOP 100 chart” |
| get\_music\_content\_details | Fetch detailed information for a song, album, or artist using its ID. | “When was this album released?” |
| get\_artist\_songs | List songs released by or featuring a specific artist. | “Find all songs featuring Jay Park” |
| get\_latest\_music\_contents | Retrieve the latest music releases in chronological order. | “What new songs came out today?” |
| get\_music\_contents\_by\_genre | Search for songs or playlists belonging to a specific genre. | “Find an indie music playlist” |
| get\_main\_genres | Retrieve a list of all available music genres for searching. | “What music genres can I search for?” |
| get\_song\_streaming\_stats | Check the total stream count and number of listeners for a song. | “How popular is IU’s ‘Through the Night’?” |

### **Personalization & My Music**

| Name | Description | Sample Prompt |
| :---- | :---- | :---- |
| recommend\_personalized\_songs\_by\_dj\_mallang | Recommend songs based on user listening patterns. | “Anything new I should listen to?” |
| recommend\_similar\_songs\_by\_dj\_mallang | Recommend songs similar in style to a specific track. | “Find more songs like this one” |
| get\_my\_liked\_music\_contents | Retrieve a list of liked songs, albums, and playlists. | “Show me my liked songs” |
| get\_my\_most\_listened\_songs | Retrieve most played songs over a specific period. | “What did I listen to most last month?” |
| get\_recently\_played\_music\_contents | Retrieve a list of recently played songs. | “What songs did I listen to recently?” |
| get\_my\_followed\_artists | List fan artists and affinity history. | “Show me the list of artists I’m a fan of” |
| get\_my\_song\_streaming\_history | Check play count and first-heard date for a specific song. | “How many times have I listened to this song?” |

### **Playback & Playlist Management**

| Name | Description | Sample Prompt |

| :--- | :--- | : :--- |

| create\_playback\_url | Generate a URL to play a given song, album, or playlist. | “Play this playlist now” |

| get\_playlist\_tracks | Retrieve all songs included in a specific playlist. | “Show me the tracklist for this playlist” |

| get\_my\_created\_playlists | Retrieve a list of playlists created by the user. | “Show me my playlists” |

## **Troubleshooting**

### **Authentication Issues**

* Refer to the “Connection Details \> Authentication Notes” section if errors occur.  
* Ensure you have an active Melon subscription for personalization features.

### **Connection Problems**

* Ensure your MCP client supports **Streamable HTTP** (not SSE).  
* Verify that your client can handle the OAuth authentication flow.  
* If an invalid\_redirect\_uri error occurs, check the whitelist registration.

### **API Limitations**

* Some features require a Melon subscription.  
* Certain content may be subject to regional restrictions.

### **Common Errors**

* **Content Not Found**: Double-check the content ID or search query.  
* **Permission Denied**: Check Melon account permissions and subscription status.

## **Support**

For additional help:

* Contact **Melon Customer Support**  
* Report issues via the Melon app or website

## **Data Privacy & Security**

Melon takes your data privacy seriously:

* All data transmission is encrypted using HTTPS.  
* OAuth 2.0 authentication ensures secure access.  
* Personal listening data is only accessed with proper user authorization.  
* Sensitive data, including authentication tokens, is not stored on the MCP server.