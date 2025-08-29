from typing import List
from pydantic import BaseModel, Field
from utils import create_bedrock_client, retry_with_backoff


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


if __name__ == "__main__":
    synthetic_data_generation_example()
