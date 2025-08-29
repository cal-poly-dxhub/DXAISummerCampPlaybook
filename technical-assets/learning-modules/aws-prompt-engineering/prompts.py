import boto3
import time
from typing import List, Literal, Dict, Optional
from pydantic import BaseModel, Field
import pdfplumber
import instructor


def create_bedrock_client():
    """Create an instructor-wrapped Bedrock client for structured outputs"""
    bedrock_client = boto3.client("bedrock-runtime", region_name="us-west-2")
    return instructor.from_bedrock(bedrock_client)

def retry_with_backoff(func, max_retries=3):
    """Decorator to handle API throttling with exponential backoff"""
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if "(ThrottlingException)" in str(e) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                raise e
    return wrapper

def extract_text_from_pdf(pdf_file_path: str) -> str:
  """Extract text from PDF using pdfplumber"""
  print(f"Extracting text from {pdf_file_path}...")
  
  extracted_text = ""
  with pdfplumber.open(pdf_file_path) as pdf:
    for page in pdf.pages:
      text = page.extract_text()
      if text:
        extracted_text += text + "\n"
  return extracted_text

# =============================================================================
# 0. TESTING DIALS AND PARAMETERS
# =============================================================================

@retry_with_backoff
def test_dials_and_parameters():
    """
    Test different dials and parameters for the Bedrock model
    This is a simple test to ensure the model can handle various settings
    Please feel free to modify the prompt and parameters!!
    """
    print("\n=== Testing Dials and Parameters ===")
    
    client = boto3.client("bedrock-runtime", region_name="us-west-2")

    prompt = "Give me a short response to this question: What is the meaning of life?"

    try:
        result = client.converse(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={  
                'temperature': 0.7,  # temperature for creativity
                'topP': 1,  # Use top-p sampling
                'stopSequences': ["<END>"],
            }
        )
        
        print(f"Response: {result['output']['message']['content'][0]['text']}")
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None


# =============================================================================
# 1. BASIC STRUCTURED OUTPUT WITH INSTRUCTOR
# =============================================================================

class MovieReview(BaseModel):
    """Model for extracting movie review sentiment and details"""
    title: str = Field(description="Movie title")
    sentiment: Literal["Positive", "Negative", "Neutral"] = Field(description="Overall sentiment")
    rating: float = Field(ge=1.0, le=10.0, description="Rating out of 10")
    key_points: List[str] = Field(description="Main points mentioned in review")

@retry_with_backoff
def basic_extraction_example():
    """
    Example 1: Basic structured data extraction
    Shows how to extract structured information from unstructured text
    """
    print("\n=== Example 1: Basic Structured Extraction ===")
    
    client = create_bedrock_client()
    
    review_text = """
    I watched The Matrix last night and wow! The special effects were groundbreaking 
    for 1999, and Keanu Reeves delivered a solid performance. The philosophical themes 
    about reality and choice really made me think. The action sequences were incredible, 
    especially the bullet-time effects. I'd give it a 9/10 - definitely a must-watch!
    """
    
    # Clear, specific instruction with context
    prompt = f"""
    Analyze this movie review and extract key information:
    
    Review: {review_text}
    
    Extract the movie title, overall sentiment, rating, and main points discussed.
    """
    
    try:
        result = client.chat.completions.create(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.1,  # Low temperature for consistent extraction
            response_model=MovieReview,
        )
        
        print(f"Movie: {result.title}")
        print(f"Sentiment: {result.sentiment}")
        print(f"Rating: {result.rating}/10")
        print(f"Key Points: {', '.join(result.key_points)}")
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None

# =============================================================================
# 2. FEW-SHOT PROMPTING FOR CLASSIFICATION
# =============================================================================

class EmailClassification(BaseModel):
    """Model for email classification with confidence scores"""
    category: Literal["Spam", "Important", "Personal", "Work", "Promotional"] = Field(
        description="Primary email category"
    )
    urgency: Literal["Low", "Medium", "High"] = Field(description="Urgency level")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in classification")
    reasoning: str = Field(description="Brief explanation of classification")

@retry_with_backoff
def few_shot_classification_example():

    print("\n=== Example 2: Few-Shot Email Classification ===")
    
    client = create_bedrock_client()
    
    # Example emails to classify
    test_email = """
    Subject: URGENT: System maintenance tonight
    From: it-team@company.com
    
    Hi everyone,
    
    We will be performing critical system maintenance tonight from 11 PM to 3 AM.
    All services will be unavailable during this time. Please plan accordingly.
    
    Thanks,
    IT Team
    """
    
    # Few-shot prompt with clear examples
    prompt = f"""
    Classify emails into categories based on these examples:
    
    EXAMPLES:
    
    Example 1:
    Subject: "Free iPhone! Click now!"
    From: "winner@random-site.com"
    Category: Spam
    Urgency: Low
    Reasoning: Obvious spam with suspicious sender and unrealistic offer
    
    Example 2:
    Subject: "Meeting moved to 2 PM"
    From: "boss@company.com"
    Category: Work
    Urgency: High
    Reasoning: Work-related schedule change from supervisor
    
    Example 3:
    Subject: "Happy Birthday!"
    From: "mom@email.com"
    Category: Personal
    Urgency: Low
    Reasoning: Personal message from family member
    
    Now classify this email:
    {test_email}
    """
    
    try:
        result = client.chat.completions.create(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.2,
            response_model=EmailClassification,
        )
        
        print(f"Category: {result.category}")
        print(f"Urgency: {result.urgency}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Reasoning: {result.reasoning}")
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None

# =============================================================================
# 3. CHAIN OF THOUGHT REASONING
# =============================================================================

class MathSolution(BaseModel):
    """Model for step-by-step math problem solving"""
    problem: str = Field(description="The original problem")
    steps: List[str] = Field(description="Step-by-step solution process")
    final_answer: str = Field(description="Final numerical answer with units")
    confidence: Literal["Low", "Medium", "High"] = Field(description="Confidence in solution")

@retry_with_backoff
def chain_of_thought_example():
    """
    Example 3: Chain of thought reasoning for problem solving
    Shows how to get step-by-step reasoning from the model
    """
    print("\n=== Example 3: Chain of Thought Reasoning ===")
    
    client = create_bedrock_client()
    
    math_problem = """
    A company's revenue increased by 15% in Q1, then decreased by 8% in Q2, 
    and finally increased by 12% in Q3. If their starting revenue was $500,000, 
    what was their revenue at the end of Q3?
    """
    
    # Prompt explicitly asking for step-by-step thinking
    prompt = f"""
    Solve this business math problem step by step. Show your reasoning clearly:
    
    Problem: {math_problem}
    
    Think through this systematically:
    1. Identify what we know
    2. Calculate each quarter's change
    3. Show the math for each step
    4. Arrive at the final answer
    
    Be precise with calculations and show intermediate results.
    """
    
    try:
        result = client.chat.completions.create(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.1,  # Low temperature for mathematical accuracy
            response_model=MathSolution,
        )
        
        print(f"Problem: {result.problem}")
        print("\nSolution Steps:")
        for i, step in enumerate(result.steps, 1):
            print(f"{i}. {step}")
        print(f"\nFinal Answer: {result.final_answer}")
        print(f"Confidence: {result.confidence}")
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None

# =============================================================================
# 4. SYNTHETIC DATA GENERATION
# =============================================================================

class Product(BaseModel):
    """Model for synthetic product data"""
    name: str = Field(description="Product name")
    category: str = Field(description="Product category")
    price: float = Field(ge=1.0, le=10000.0, description="Price in USD")
    description: str = Field(description="Product description")
    features: List[str] = Field(description="Key product features")
    target_audience: str = Field(description="Target customer demographic")

class ProductCatalog(BaseModel):
    """Collection of synthetic products"""
    products: List[Product] = Field(description="List of synthetic products")

@retry_with_backoff
def synthetic_data_generation_example():
    """
    Example 4: Generating synthetic product data
    Shows how to create realistic test data for applications
    """
    print("\n=== Example 4: Synthetic Data Generation ===")
    
    client = create_bedrock_client()
    
    # Detailed prompt for synthetic data generation
    prompt = """
    Generate 5 diverse and realistic tech products for an e-commerce website.
    
    Requirements:
    - Mix of different tech categories (smartphones, laptops, accessories, etc.)
    - Realistic pricing based on product type
    - Varied target audiences (students, professionals, gamers, etc.)
    - Creative but believable product names
    - Detailed descriptions with specific features
    - Features should be relevant to each product category
    
    Make the data feel authentic and varied, as if from a real tech store.
    """
    
    try:
        result = client.chat.completions.create(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.7,  # Higher temperature for creativity
            response_model=ProductCatalog,
        )
        
        print(f"Generated {len(result.products)} products:")
        print("-" * 50)
        
        for i, product in enumerate(result.products, 1):
            print(f"{i}. {product.name}")
            print(f"   Category: {product.category}")
            print(f"   Price: ${product.price:,.2f}")
            print(f"   Target: {product.target_audience}")
            print(f"   Features: {', '.join(product.features[:3])}...")
            print()
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None

# =============================================================================
# 5. MULTI-STEP DATA PROCESSING (ETL EXAMPLE)
# =============================================================================

class Supervisor(BaseModel):
  name: str = Field(description="Name of the supervisor")
  district: str = Field(description="District the supervisor represents")

class SocialServicesItem(BaseModel):
  item_number: str = Field(description="The item number on the agenda")
  title_or_summary: str = Field(description="Short summary or title of the item")
  districts: Optional[List[str]] = Field(description="List of districts mentioned, if specified")
  type: str = Field(description="Type of agenda item, like 'Consent', 'Public Hearing', etc.")

class ProcessedAgenda(BaseModel):
  meeting_title: str = Field(description="The official meeting title")
  date: str = Field(description="Date of the meeting, in YYYY-MM-DD format if possible")
  location: str = Field(description="Where the meeting was held")
  supervisors: List[Supervisor] = Field(description="List of supervisors with name and district")
  all_section_titles: List[str] = Field(description="List of all section titles in the agenda")
  social_services_items: List[SocialServicesItem] = Field(
    description="Detailed agenda items related to social services"
  )


@retry_with_backoff
def etl_processing_example():
    """
    Example 5: ETL (Extract, Transform, Load) processing
    Shows how to process messy customer feedback into structured data
    """
    print("\n=== Example 5: ETL Data Processing ===")
    
    client = create_bedrock_client()
    
    # Raw, unstructured customer feedback (simulate real messy data)
    pdf_text = extract_text_from_pdf("Board-of-Supervisors-Agenda.pdf")
    
    # ETL prompt for batch processing
    prompt = f"""
    Please analyze the following document text and extract key information into a structured JSON format.

    Return an object with the following fields:

    - meeting_title
    - date
    - location
    - supervisors (list of names and districts)

    - all_section_titles: a list of all agenda section titles in the document

    - social_services_items: a list of detailed items specifically related to Social Services. These may appear in a section titled "Social Services" or be items that address social services topics such as welfare, benefits, homelessness, housing support, child services, etc.

    Each item in social_services_items should strictly include:
      - item_number
      - title or summary
      - districts (if specified)
      - type (e.g. "Consent", "Public Hearing", "Presentation", etc.)
    do not include anything else for an item. 

    Return only valid JSON. Do not include any explanatory text.

    Document text:
    {pdf_text}
    """
    
    try:
        result = client.chat.completions.create(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.5,  # Balanced temperature for processing
            response_model= ProcessedAgenda,
        )
        
        print("-" * 60)
        
        with open("processed_etl_agenda.json", "w") as f:
            f.write(result.model_dump_json(indent=2))
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None

# =============================================================================
# 6. ADVANCED PROMPT WITH FLAGS AND CONTEXT
# =============================================================================

class TechnicalExplanation(BaseModel):
    """Model for technical explanations with different complexity levels"""
    topic: str = Field(description="The technical topic being explained")
    complexity_level: str = Field(description="Target audience complexity level")
    explanation: str = Field(description="Main explanation content")
    key_concepts: List[str] = Field(description="Important concepts covered")
    practical_examples: List[str] = Field(description="Real-world examples")
    next_steps: str = Field(description="Suggested next learning steps")

@retry_with_backoff
def advanced_prompt_with_flags_example():
    """
    Example 6: Advanced prompting with flags and context control
    Shows how to use flags to control AI behavior and output style
    """
    print("\n=== Example 6: Advanced Prompting with Flags ===")
    
    client = create_bedrock_client()
    
    topic = "machine learning"
    audience = "college students new to programming"
    
    # Advanced prompt with multiple flags and context
    prompt = f"""
    [FLAG: EDUCATIONAL_CONTENT]
    [FLAG: BEGINNER_FRIENDLY]
    [FLAG: INCLUDE_EXAMPLES]
    [FLAG: PRACTICAL_FOCUS]
    [FLAG: ENCOURAGE_LEARNING]
    
    Context: You are an experienced computer science professor explaining to {audience}.
    
    Task: Explain {topic} in an engaging, accessible way.
    
    Guidelines:
    - Use analogies and real-world examples
    - Avoid overwhelming technical jargon
    - Focus on practical applications
    - Encourage further exploration
    - Make it relevant to student life
    
    Topic to explain: {topic}
    
    Structure your explanation to build understanding progressively.
    """
    
    try:
        result = client.chat.completions.create(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.5,  # Balanced for educational content
            response_model=TechnicalExplanation,
        )
        
        print(f"Topic: {result.topic}")
        print(f"Level: {result.complexity_level}")
        print(f"\nExplanation:\n{result.explanation}")
        print(f"\nKey Concepts:")
        for concept in result.key_concepts:
            print(f"• {concept}")
        print(f"\nPractical Examples:")
        for example in result.practical_examples:
            print(f"• {example}")
        print(f"\nNext Steps: {result.next_steps}")
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None

# =============================================================================
# 7. COMPARISON AND ANALYSIS
# =============================================================================

class ProductComparison(BaseModel):
    """Model for comparing products or services"""
    items_compared: List[str] = Field(description="Items being compared")
    comparison_criteria: List[str] = Field(description="Criteria used for comparison")
    detailed_analysis: Dict[str, Dict[str, str]] = Field(
        description="Detailed analysis for each item across criteria"
    )
    recommendation: str = Field(description="Overall recommendation based on analysis")
    best_for_scenarios: Dict[str, str] = Field(
        description="Which option is best for different use cases"
    )

@retry_with_backoff
def comparison_analysis_example():
    """
    Example 7: Tree of thought for complex comparisons
    Shows how to get structured comparative analysis
    """
    print("\n=== Example 7: Comparative Analysis ===")
    
    client = create_bedrock_client()
    
    # Complex comparison prompt
    prompt = """
    Compare these three programming languages for college students learning their first language:
    1. Python
    2. JavaScript  
    3. Java
    
    Analyze them across these criteria:
    - Learning curve and beginner-friendliness
    - Job market opportunities
    - Versatility and use cases
    - Community support and resources
    - Long-term career prospects
    
    Consider multiple perspectives:
    - Academic learning environment
    - Industry requirements
    - Personal project possibilities
    - Future technology trends
    
    Provide a nuanced analysis that acknowledges trade-offs and different student goals.
    Include specific recommendations for different scenarios.
    """
    
    try:
        result = client.chat.completions.create(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.4,  # Balanced for analytical thinking
            response_model=ProductComparison,
        )
        
        print("Programming Language Comparison for College Students")
        print("=" * 55)
        print(f"Languages: {', '.join(result.items_compared)}")
        print(f"Criteria: {', '.join(result.comparison_criteria)}")
        
        print("\nDetailed Analysis:")
        for item, analysis in result.detailed_analysis.items():
            print(f"\n{item.upper()}:")
            for criterion, assessment in analysis.items():
                print(f"  • {criterion}: {assessment}")
        
        print(f"\nRecommendation:\n{result.recommendation}")
        
        print("\nBest For Different Scenarios:")
        for scenario, choice in result.best_for_scenarios.items():
            print(f"• {scenario}: {choice}")
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None

# =============================================================================
# MAIN FUNCTION TO RUN ALL EXAMPLES
# =============================================================================

def main():
    """
    Run all prompt engineering examples
    """
    print("Prompt Engineering Examples with AWS Bedrock and Instructor")
    print("=" * 60)
    print("Educational examples for college students learning Python and AI")
    
    examples = [
        ("Testing Dials and Parameters", test_dials_and_parameters),
        ("Basic Structured Extraction", basic_extraction_example),
        ("Few-Shot Classification", few_shot_classification_example),
        ("Chain of Thought Reasoning", chain_of_thought_example),
        ("Synthetic Data Generation", synthetic_data_generation_example),
        ("ETL Data Processing", etl_processing_example),
        ("Advanced Prompting with Flags", advanced_prompt_with_flags_example),
        ("Comparative Analysis", comparison_analysis_example),
    ]
    
    results = {}
    
    for name, func in examples:
        try:
            print(f"\nRunning: {name}")
            print("-" * 40)
            result = func()
            results[name] = result
        except Exception as e:
            print(f"✗ {name} failed: {e}")
            results[name] = None
        
        # Small delay between examples to be respectful to API
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print(f"Successfully ran {sum(1 for r in results.values() if r is not None)}/{len(examples)} examples")
    
    return results

if __name__ == "__main__":
    main()
