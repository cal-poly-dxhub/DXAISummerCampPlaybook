# Cal Poly AI Summer Camp: Interactive AI Chatbot with Streamlit

Welcome to our AI Summer Camp! This project will teach you how to build a web-based AI chatbot using Streamlit and AWS Bedrock.

## Contact Information

**Instructor**: Ryan Gertz - rgertz@calpoly.edu

Feel free to reach out if you have questions about:
- Setting up AWS credentials
- Understanding Streamlit web development
- Troubleshooting chatbot functionality
- Ideas for extending this project
- General questions about AI and web applications

## Video Tutorial
- For a walkthrough of installing VS Code and Python on windows [check this video out](https://drive.google.com/file/d/1hwVswLDUorcEJJz8gbOUracmx9Ufj3QE/view?usp=sharing)

- For a walkthrough of setting up a Virtual Environment with python in VS Code [check this repository out](https://github.com/RyanGertz/ai-summercamp-scripts)

- For a complete walkthrough of this project, check out my video explanation:
[AI Summer Camp Tutorial - AWS Bedrock Streamlit Chatbot](https://drive.google.com/file/d/1rSkpOh5eiQ1vsIbhT45n2RsJOISZt-Ct/view?usp=sharing)

## What You'll Learn

- **Streamlit Web Development**: Creating interactive web applications with Python and Streamlit
- **Real-time Chat Interface**: Building a conversational UI with message history
- **AWS Bedrock Integration**: Connecting your web app to cloud-based AI services

## What This Code Does

This project demonstrates how to create a fully functional AI chatbot web application. The code:

1. **Creates a Web Interface**: Uses Streamlit to build a chat-like user interface
2. **Manages Conversations**: Maintains message history and context throughout the chat
3. **Connects to Bedrock**: Uses AWS Bedrock to send messages to an LLM
4. **Allows Users to Chat with an LLM Real Time**: Users can have a back and forth conversation with an LLM

## Prerequisites

Before you start, you'll need:

### 1. Python Installation
- Python 3.7 or higher installed on your computer
- You can download it from [python.org](https://www.python.org/downloads/)
- You can also watch [my video](https://drive.google.com/file/d/1hwVswLDUorcEJJz8gbOUracmx9Ufj3QE/view?usp=drive_link) explaning how to install it on Windows

### 2. AWS Account Setup
- An AWS account
- AWS credentials configured on your computer
- Access to AWS Bedrock service and Anthropic Claude model

### 3. Required Python Packages
Install the necessary packages by running this command in your terminal:
```bash
pip install streamlit boto3
```

## Understanding the Code

### Key Components

**Streamlit**: A Python library that makes it easy to create web applications. It handles all the web development complexity for you.

**AWS Bedrock**: AWS's suite for working with LLMs

### The Functions Explained

#### Function 1: `get_bedrock_client()`
This function creates and caches the AWS connection:
- Uses Streamlit's `@st.cache_resource` decorator to avoid recreating the client
- Connects to AWS Bedrock
- Returns a reusable client object for making API calls

#### Function 2: `invoke_model(messages: List[Dict[str, str]])`
This function handles communication with Claude:
- Takes the full conversation history as input
- Converts Streamlit message format to Bedrock's expected format
- Sends the conversation to Claude using the converse API
- Returns Claude's response or an error message if something goes wrong

#### Main Application Logic
The main part of the code handles the user interface:
- Sets up the page configuration and title
- Manages session state for conversation history
- Displays all previous messages in chronological order
- Handles new user input and generates AI responses
- Updates the interface in real-time

## How to Run the Code

1. **Save the code**: Clone this repo or copy the code into a file called `chatbot.py`

2. **Open your terminal/command prompt**

3. **Navigate to your project folder**:
   ```bash
   cd path/to/your/project
   ```

4. **Run the Streamlit app**:
   ```bash
   streamlit run chatbot.py
   ```

5. **Open your browser**: Streamlit will automatically open your default browser to `http://localhost:8501`

6. **Start chatting**: Type a message in the input box and press Enter to chat with the AI!

## Understanding the Interface

### Chat Display
The app shows a conversation flow similar to popular messaging apps:
- **User messages**: Appear with a user icon
- **AI responses**: Appear with an assistant icon
- **Message history**: All previous messages remain visible
- **Thinking indicator**: Shows when the AI is processing

## Common Issues and Solutions

### "No module named 'streamlit'"
Install the required package:
```bash
pip install streamlit
```

### "Port already in use"
If port 8501 is busy, Streamlit will automatically try other ports:
- Check the terminal output for the correct URL
- Or specify a different port: `streamlit run chatbot.py --server.port 8502`

### "No credentials found"
This means your AWS credentials aren't set up. You need:
- AWS Access Keys configured
- AWS CLI setup or environment variables
- IAM permissions for Bedrock

### "Access denied to model"
Your AWS account might not have permission to use Claude:
- Check your AWS Bedrock model access in the console
- Ensure you have the correct model ID
- Verify your IAM permissions include bedrock actions

### "Connection timeout"
Network or AWS service issues:
- Check your internet connection
- Try a different AWS region
- Verify AWS service status

## Important Notes

- **Cost Awareness**: Each message exchange costs money (usually a few cents per conversation)
- **Rate Limits**: AWS has limits on how many requests you can make per minute
- **Session Persistence**: Messages are only saved while the app is running
- **Local Development**: The app runs on your computer by default

## Use Cases for AI Chatbots

This type of chatbot application is useful for:
- **Customer Support**: Automated assistance for common questions
- **Educational Tools**: Tutoring and learning assistance
- **Code Assistance**: Programming help and debugging
- **Research Assistant**: Information gathering and analysis
- **Personal Assistant**: Task management and reminders

## Getting Help

If you run into issues:
1. Check the terminal output for detailed error messages
2. Verify your AWS credentials are working
3. Ask our camp staff for assistance
4. Test with a simple message first
5. Check the Streamlit documentation for UI issues

## Resources for Further Learning

- [Streamlit Documentation](https://docs.streamlit.io/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Streamlit Gallery](https://streamlit.io/gallery) - Example applications

---

Happy coding! 🚀
