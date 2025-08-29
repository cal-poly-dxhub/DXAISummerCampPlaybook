# Cal Poly AI Summer Camp: Simple RAG Chatbot with Amazon Bedrock
Welcome to our AI Summer Camp! This project give you scripts to a minimal Streamlit chatbot that lets you chat with your documents using Amazon Bedrock Knowledge Bases.

## Contact Information
Instructor: Shrey Shah - sshah84@calpoly.edu

### Feel free to reach out if you have questions about:

- Cross-platform compatibility issues
- Project organization strategies
- General development environment setup

## Video Tutorial
For a complete walkthrough of this project, check out my video explanation: [RAG Chatbot with Amazon Bedrock](https://drive.google.com/file/d/1JMOY54Q2DaL1HPl_GFUgAXnfWRuf0KoT/view?usp=drive_link) 

## What is RAG?
RAG (Retrieval Augmented Generation) is like giving an AI assistant a filing cabinet of your documents so it can look things up before answering.

### How it works:
1. Convert to Vectors: Your documents get turned into "vectors" (think of them as numerical fingerprints that capture meaning)
2. Store in Knowledge Base: These vectors are stored in a searchable database
3. Find Similar Content: When you ask a question, the system finds documents with similar meaning using "semantic similarity"
4. Generate Answer: The AI reads the relevant documents and writes a custom answer

### Key Concepts Made Simple:

**What is a Vector?**
- A vector is just a list of numbers that represents the "meaning" of text
- Similar ideas have similar numbers
- Example: "dog" and "puppy" would have very similar vectors
- "dog" and "spaceship" would have very different vectors

**What is Semantic Similarity?**
- It's how we find documents that mean the same thing, even if they use different words
- "car" and "automobile" are semantically similar
- "happy" and "joyful" are semantically similar
- This is way smarter than just matching exact words!

## Features

- Simple chat interface
- Queries your Bedrock Knowledge Base
- Maintains conversation history
- Only 3 files, less than 100 lines of code!

## Quick Start

### 1. Clone this repo
```bash
git clone https://github.com/cal-poly-dxhub/streamlit-rag-chatbot-kb.git
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up AWS Bedrock Knowledge Base

#### Enable Bedrock Models:
1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Navigate to **Model access**
3. Click **Enable access** for **Claude 3.5 Sonnet v2**

#### Create Knowledge Base:
1. In Bedrock console, go to **Knowledge bases**
2. Click **Create knowledge base**
3. Name: `chatbot-kb`
4. Follow the setup wizard:
   - Create an S3 bucket for your documents
   - Choose **Amazon OpenSearch Serverless** for vector store
   - Use default settings
5. **Copy the Knowledge Base ID** (you'll need this!)

#### Upload Documents:
1. Upload PDF, TXT, or DOCX files to your S3 bucket
2. In Knowledge Base, click **Sync** to process documents
3. Wait for sync to complete (5-10 minutes)

### 4. Configure environment
Modify the `.env` file with your AWS credentials:


```env
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
KNOWLEDGE_BASE_ID=your_knowledge_base_id_here
```

**To get AWS credentials:**
1. Go to AWS Console → IAM → Users
2. Create user or select existing user
3. Attach policy: `AmazonBedrockFullAccess`
4. Create access key → Copy the keys

### 5. Run the app
```bash
streamlit run app.py
```

### 6. Test it!
- Open your browser to the Streamlit URL
- Ask questions about your documents
- Example: "What is our company vacation policy?"

## File Structure
```
simple-rag-chatbot/
├── app.py              # Main Streamlit app
├── requirements.txt    # Dependencies
├── .env               # Your AWS keys (don't commit this!)
└── README.md          # This file
```

## How It Works

1. **User asks a question** in the chat interface
2. **Bedrock searches** your Knowledge Base for relevant documents
3. **Claude 3.5 Sonnet V2 generates** an answer based on found documents
4. **Response displays** in the chat with the AI-generated answer

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Knowledge base not found" | Check your `KNOWLEDGE_BASE_ID` in `.env` |
| "Access denied" | Verify AWS credentials and IAM permissions |
| Generic answers only | Make sure documents are uploaded and synced |
| "Module not found" | Run `pip install -r requirements.txt` |
| Slow responses | Knowledge Base sync might still be running |

## Requirements

- Python 3.8+
- AWS Account with Bedrock access
- Documents uploaded to Knowledge Base
- Internet connection

## IAM Permissions Needed

Your AWS user needs these permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:RetrieveAndGenerate"
            ],
            "Resource": "*"
        }
    ]
}
```

## Example Questions to Try

Once you have documents uploaded:
- "What is the main topic discussed in the documents?"
- "Summarize the key points"
- "What does the document say about [specific topic]?"

**Built for simplicity** - This is designed to demonstrate RAG concepts with minimal complexity.
