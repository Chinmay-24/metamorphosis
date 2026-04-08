"""
Test runner for inference script validation.
Tests that inference.py can be imported and has correct structure without requiring API keys.
"""

import json
import sys
from pathlib import Path


def test_inference_import():
    """Test that inference.py can be imported."""
    print("="*70)
    print("INFERENCE SCRIPT VALIDATION")
    print("="*70)
    
    try:
        # Add project root to path
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Test import
        print("\n[TEST] Importing inference module...")
        import inference
        print("✓ inference module imported successfully")
        
        # Check required functions
        required_functions = ["main", "run_task", "infer_action", "parse_model_output"]
        for func_name in required_functions:
            if hasattr(inference, func_name):
                print(f"✓ Found function: {func_name}")
            else:
                raise AssertionError(f"Missing required function: {func_name}")
        
        # Check structured logging templates
        print("\n[TEST] Validating structured logging templates...")
        templates = [
            ("START_BLOCK_TEMPLATE", inference.START_BLOCK_TEMPLATE),
            ("STEP_BLOCK_TEMPLATE", inference.STEP_BLOCK_TEMPLATE),
            ("END_BLOCK_TEMPLATE", inference.END_BLOCK_TEMPLATE),
        ]
        
        for name, template in templates:
            assert isinstance(template, dict), f"{name} is not a dict"
            assert len(template) > 0, f"{name} is empty"
            # Try to JSON serialize
            json_str = json.dumps(template)
            print(f"✓ {name}: {len(template)} fields, serializable")
        
        # Validate field names in templates
        print("\n[TEST] Validating required fields in templates...")
        
        # START fields
        required_start_fields = ["timestamp", "session_id", "task_level", "description", "model", "api_base"]
        for field in required_start_fields:
            assert field in inference.START_BLOCK_TEMPLATE, f"Missing START field: {field}"
        print(f"✓ START block has all required fields: {', '.join(required_start_fields)}")
        
        # STEP fields
        required_step_fields = ["step_index", "email_id", "email_subject", "action", "reward", 
                               "normalized_reward", "done", "grader_feedback"]
        for field in required_step_fields:
            assert field in inference.STEP_BLOCK_TEMPLATE, f"Missing STEP field: {field}"
        print(f"✓ STEP block has all required fields: {', '.join(required_step_fields)}")
        
        # END fields
        required_end_fields = ["total_steps", "total_reward", "final_score", "task_level", "success"]
        for field in required_end_fields:
            assert field in inference.END_BLOCK_TEMPLATE, f"Missing END field: {field}"
        print(f"✓ END block has all required fields: {', '.join(required_end_fields)}")
        
        # Check environment variable usage
        print("\n[TEST] Validating environment variable configurations...")
        env_vars = ["API_BASE_URL", "MODEL_NAME", "HF_TOKEN"]
        for var in env_vars:
            if hasattr(inference, var):
                value = getattr(inference, var)
                print(f"✓ {var} = {value or '(not set)'}")
            else:
                raise AssertionError(f"Missing environment variable: {var}")
        
        # Test parse_model_output
        print("\n[TEST] Testing JSON parsing...")
        test_json = '{"label": "billing", "priority": "high", "response_template": null, "escalate": false}'
        parsed = inference.parse_model_output(test_json)
        assert parsed["label"] == "billing", "JSON parsing failed"
        print("✓ JSON parsing works correctly")
        
        # Test parse_model_output with markdown
        test_json_md = '```json\n{"label": "technical", "priority": "medium", "response_template": "test", "escalate": true}\n```'
        parsed_md = inference.parse_model_output(test_json_md)
        assert parsed_md["label"] == "technical", "JSON extraction from markdown failed"
        print("✓ JSON extraction from markdown works")
        
        print("\n" + "="*70)
        print("✓ ALL INFERENCE SCRIPT VALIDATION CHECKS PASSED")
        print("="*70)
        return 0
        
    except Exception as e:
        print(f"\n✗ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(test_inference_import())
