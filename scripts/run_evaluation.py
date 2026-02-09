#!/usr/bin/env python
"""
CLI script to run LangSmith evaluations for DNA Agent

Usage:
    python scripts/run_evaluation.py --create-dataset
    python scripts/run_evaluation.py --run --experiment "baseline-v1"
    python scripts/run_evaluation.py --quick-test "What are the disease risks for a CEU Male?"
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    parser = argparse.ArgumentParser(
        description="Run DNA Agent evaluations with LangSmith",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Create evaluation dataset:
    python scripts/run_evaluation.py --create-dataset
    
  Run full evaluation:
    python scripts/run_evaluation.py --run --experiment "v1.0-baseline"
    
  Quick test single query:
    python scripts/run_evaluation.py --quick-test "Analyze sample uploads/NA20805_GIH_Male.csv"
    
  Check LangSmith status:
    python scripts/run_evaluation.py --status
        """
    )
    
    parser.add_argument(
        "--create-dataset",
        action="store_true",
        help="Create/update evaluation dataset in LangSmith"
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run evaluation on the dataset"
    )
    parser.add_argument(
        "--dataset",
        default="dna-agent-eval",
        help="Dataset name (default: dna-agent-eval)"
    )
    parser.add_argument(
        "--experiment",
        default=None,
        help="Experiment name (defaults to timestamp)"
    )
    parser.add_argument(
        "--quick-test",
        type=str,
        metavar="QUERY",
        help="Quick test a single query without LangSmith"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check LangSmith configuration status"
    )
    parser.add_argument(
        "--list-tests",
        action="store_true",
        help="List all standard test cases"
    )
    
    args = parser.parse_args()
    
    # Check status
    if args.status:
        check_status()
        return
    
    # List test cases
    if args.list_tests:
        list_test_cases()
        return
    
    # Quick test
    if args.quick_test:
        quick_test(args.quick_test)
        return
    
    # Create dataset
    if args.create_dataset:
        create_dataset(args.dataset)
    
    # Run evaluation
    if args.run:
        experiment_name = args.experiment or f"eval-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        run_evaluation(args.dataset, experiment_name)
    
    # Show help if no action specified
    if not any([args.create_dataset, args.run, args.quick_test, args.status, args.list_tests]):
        parser.print_help()


def check_status():
    """Check LangSmith configuration status"""
    print("\n🔍 Checking LangSmith Configuration...\n")
    
    try:
        from agent.config import config
        
        print("Configuration:")
        print(f"  LANGCHAIN_TRACING_V2: {config.LANGSMITH_ENABLED}")
        print(f"  LANGCHAIN_API_KEY: {'✅ Set' if config.LANGSMITH_API_KEY else '❌ Not set'}")
        print(f"  LANGCHAIN_PROJECT: {config.LANGSMITH_PROJECT}")
        print(f"  LANGCHAIN_ENDPOINT: {config.LANGSMITH_ENDPOINT}")
        print()
        
        if config.is_langsmith_enabled():
            print("✅ LangSmith is properly configured!")
            
            # Try to connect
            try:
                from langsmith import Client
                client = Client()
                # Try to list projects to verify connection
                print("✅ Successfully connected to LangSmith API")
            except Exception as e:
                print(f"⚠️  Could not connect to LangSmith: {e}")
        else:
            print("❌ LangSmith is not enabled")
            print("\nTo enable LangSmith, set these environment variables:")
            print("  export LANGCHAIN_TRACING_V2=true")
            print("  export LANGCHAIN_API_KEY=ls__your_api_key_here")
            print("  export LANGCHAIN_PROJECT=dna-analysis-agent")
            
    except ImportError as e:
        print(f"❌ Could not import agent config: {e}")
        print("   Make sure you're running from the project root")


def list_test_cases():
    """List all standard test cases"""
    print("\n📋 Standard Test Cases:\n")
    
    try:
        from agent.evaluation import STANDARD_TEST_CASES
        
        categories = {}
        for tc in STANDARD_TEST_CASES:
            if tc.category not in categories:
                categories[tc.category] = []
            categories[tc.category].append(tc)
        
        for category, tests in categories.items():
            print(f"📁 {category.upper()}")
            for tc in tests:
                difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(tc.difficulty, "⚪")
                print(f"   {difficulty_emoji} {tc.name}")
                print(f"      Input: {tc.user_input[:60]}...")
                print(f"      Expected tools: {', '.join(tc.expected_tools)}")
            print()
            
    except ImportError as e:
        print(f"❌ Could not import test cases: {e}")


def create_dataset(dataset_name: str):
    """Create evaluation dataset"""
    print(f"\n📊 Creating Dataset: {dataset_name}\n")
    
    try:
        from agent.evaluation import create_evaluation_dataset, STANDARD_TEST_CASES
        
        dataset_id = create_evaluation_dataset(dataset_name)
        
        if dataset_id:
            print(f"✅ Dataset created successfully!")
            print(f"   ID: {dataset_id}")
            print(f"   Examples: {len(STANDARD_TEST_CASES)}")
            print(f"\n   View at: https://smith.langchain.com/")
        else:
            print("❌ Failed to create dataset")
            print("   Check LangSmith configuration with --status")
            
    except Exception as e:
        print(f"❌ Error creating dataset: {e}")


def run_evaluation(dataset_name: str, experiment_name: str):
    """Run evaluation"""
    print(f"\n🧪 Running Evaluation\n")
    print(f"   Dataset: {dataset_name}")
    print(f"   Experiment: {experiment_name}")
    print()
    
    try:
        from agent.evaluation import run_evaluation as eval_run
        
        print("⏳ Running evaluation (this may take a while)...")
        result = eval_run(
            dataset_name=dataset_name,
            experiment_name=experiment_name
        )
        
        if result and result.get("status") == "complete":
            print(f"\n✅ Evaluation complete!")
            print(f"   View results at: https://smith.langchain.com/")
        else:
            print(f"\n❌ Evaluation failed: {result}")
            
    except Exception as e:
        print(f"❌ Error running evaluation: {e}")


def quick_test(query: str):
    """Quick test a single query"""
    print(f"\n🧬 Quick Test\n")
    print(f"   Query: {query}\n")
    
    try:
        from agent.workflow import get_workflow
        from agent.evaluation import quick_evaluate_response
        
        print("⏳ Running agent...")
        workflow = get_workflow()
        result = workflow.run(
            user_input=query,
            session_id="quick_test"
        )
        
        response = result.get("response", "")
        tools_used = [
            tr.get("tool", "")
            for tr in result.get("tool_results", [])
            if tr.get("success")
        ]
        
        print("\n📝 Response:")
        print("-" * 50)
        print(response[:500] + "..." if len(response) > 500 else response)
        print("-" * 50)
        
        print(f"\n🔧 Tools Used: {', '.join(tools_used) if tools_used else 'None'}")
        
        # Quick evaluation
        print("\n📊 Evaluation:")
        eval_result = quick_evaluate_response(
            user_input=query,
            response=response,
            tools_used=tools_used
        )
        
        for key, value in eval_result.items():
            if isinstance(value, dict):
                score = value.get("score", 0)
                emoji = "✅" if score >= 0.7 else "⚠️" if score >= 0.4 else "❌"
                print(f"   {emoji} {key}: {score:.2f}")
            elif key == "overall_score":
                emoji = "✅" if value >= 0.7 else "⚠️" if value >= 0.4 else "❌"
                print(f"\n   {emoji} Overall Score: {value:.2f}")
                
    except Exception as e:
        print(f"❌ Error running quick test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()






