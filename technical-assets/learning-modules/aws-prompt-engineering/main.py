import time
from utils import retry_with_backoff

# Import all task functions
from task01_testing_dials import test_dials_and_parameters
from task02_basic_extraction import basic_extraction_example
from task03_few_shot_classification import few_shot_classification_example
from task04_chain_of_thought import chain_of_thought_example
from task05_synthetic_data import synthetic_data_generation_example
from task06_etl_processing import etl_processing_example
from task07_advanced_prompting import advanced_prompt_with_flags_example
from task08_comparison_analysis import comparison_analysis_example


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
    print(
        f"Successfully ran {sum(1 for r in results.values() if r is not None)}/{len(examples)} examples"
    )

    return results


if __name__ == "__main__":
    main()
