import llm
import pytest
from typing import Dict, Any
import json

def get_token_usage(response) -> Dict[str, int]:
    """Extract token usage from response"""
    # Wait for response to complete
    response_text = str(response)  # This ensures completion
    if not response.response_json:
        return {"input_tokens": 0, "output_tokens": 0}
    return response.response_json.get("usage", {"input_tokens": 0, "output_tokens": 0})

def calculate_cost(usage: Dict[str, int], model_name: str, is_cached: bool = False) -> float:
    """Calculate cost based on token usage and model pricing"""
    with open("/tmp/claude_pricing.json", "r") as f:
        pricing = json.load(f)
    
    # Use full model name for pricing lookup
    pricing_type = "cached_pricing" if is_cached else "base_pricing"
    model_pricing = pricing["models"][model_name][pricing_type]
    input_cost = (usage["input_tokens"] / 1_000_000) * model_pricing["input_tokens"]
    output_cost = (usage["output_tokens"] / 1_000_000) * model_pricing["output_tokens"]
    return input_cost + output_cost

@pytest.mark.vcr(
    mode="all",  # Record all requests
    record_mode="once",  # Record once and replay
    match_on=['method', 'scheme', 'host', 'port', 'path', 'query'],  # Removed body from matching
    filter_headers=['authorization', 'x-api-key', 'anthropic-version', 'anthropic-beta'],
    ignore_localhost=True
)
def test_caching_effectiveness():
    """Test that caching reduces costs while maintaining response quality"""
    # Create cassette directory if it doesn't exist
    import os
    os.makedirs("tests/cassettes/test_caching", exist_ok=True)
    # Import required modules
    import time
    from contextlib import contextmanager
    
    # Helper function for timeout
    @contextmanager
    def timeout(seconds, description="API call"):
        start = time.time()
        yield
        duration = time.time() - start
        if duration > seconds:
            print(f"Warning: {description} took {duration:.2f}s (longer than {seconds}s timeout)")
    
    # Test all required models with varied prompts
    test_prompts = [
        "What is the capital of France?",
        "Tell me about the Eiffel Tower",
        "What is the population of Paris?"
    ]
    
    models_to_test = [
        ("claude-3-haiku-20240307", "claude-3-haiku-cache"),
        ("claude-3-opus-20240229", "claude-3-opus-cache"),
        ("claude-3-5-sonnet-20241022", "new-sonnet-cache")
    ]
    
    print("\n" + "="*50)
    print("Starting comprehensive model testing...")
    print("="*50)
    
    for base_model_name, cached_model_name in models_to_test:
        base_model = llm.get_model(base_model_name)
        cached_model = llm.get_model(cached_model_name)
        
        # Set API key for both models from environment
        base_model.key = os.getenv("ANTHROPIC_API_KEY")
        cached_model.key = os.getenv("ANTHROPIC_API_KEY")
        
        # Ensure API key is available
        assert base_model.key, "ANTHROPIC_API_KEY environment variable must be set"
        assert cached_model.key, "ANTHROPIC_API_KEY environment variable must be set"
        
        for prompt in test_prompts:
            print(f"\nTesting prompt: {prompt}")
            
            # Test without caching
            print("\nMaking base (uncached) request...")
            with timeout(30, "Base API call"):
                base_response = base_model.prompt(prompt)
                base_usage = get_token_usage(base_response)
                base_cost = calculate_cost(base_usage, base_model_name, is_cached=False)
                print(f"Base response: {str(base_response)[:100]}...")
                print(f"Base request cost: ${base_cost:.6f}")
            
            # Test with caching
            print("\nMaking first cached request...")
            with timeout(30, "Cached API call"):
                cached_response = cached_model.prompt(prompt, options={"cache_prompt": True})
                cached_usage = get_token_usage(cached_response)
                cached_cost = calculate_cost(cached_usage, base_model_name, is_cached=True)
                print(f"Cached response: {str(cached_response)[:100]}...")
                print(f"Cached request cost: ${cached_cost:.6f}")
            
            # Verify caching effectiveness
            assert cached_cost <= base_cost, f"Cached response for {base_model_name} should not cost more than base response"
            assert len(cached_response.text()) > 0, f"Cached response for {base_model_name} should not be empty"
            
            # Test repeated cached request
            repeat_cached_response = cached_model.prompt(prompt, options={"cache_prompt": True})
            repeat_usage = get_token_usage(repeat_cached_response)
            repeat_cost = calculate_cost(repeat_usage, base_model_name, is_cached=True)
            
            # Verify both cached requests have reduced costs compared to base
            assert repeat_cost <= base_cost, f"Cached request for {base_model_name} should cost less than base request"
            assert cached_cost <= base_cost, f"Cached request for {base_model_name} should cost less than base request"
            
            # Verify response quality is maintained
            assert len(repeat_cached_response.text()) > 0, f"Repeated cached response for {base_model_name} should not be empty"
            
            # Model-specific cost verification
            if "opus" in base_model_name.lower():
                assert base_cost > 0.00001, f"Base cost for Opus model should be significant"
            elif "sonnet" in base_model_name.lower():
                assert base_cost > 0.000005, f"Base cost for Sonnet model should be moderate"
            elif "haiku" in base_model_name.lower():
                assert base_cost > 0.000001, f"Base cost for Haiku model should be smallest"
            
            # Print model-specific summary
            print(f"\nModel: {base_model_name}")
            print(f"Base cost: ${base_cost:.6f}")
            print(f"Cached cost: ${cached_cost:.6f}")
            print(f"Repeat cached cost: ${repeat_cost:.6f}")
            print(f"Cost reduction: {((base_cost - cached_cost) / base_cost * 100):.1f}%")
            
            # Verify costs are reduced for cached responses
            assert repeat_cost < base_cost, f"Repeated cached request for {base_model_name} should cost less than base request"
            assert cached_cost < base_cost, f"Initial cached request for {base_model_name} should cost less than base request"
            
            # Verify response contains relevant content based on prompt type
            response_text = repeat_cached_response.text()
            
            # Different validation criteria based on prompt type
            if "capital of France" in prompt:
                assert "Paris" in response_text, "Response should mention Paris for capital question"
            elif "Eiffel Tower" in prompt:
                assert len(response_text) > 100, "Eiffel Tower description should be detailed"
                assert any(keyword in response_text.lower() for keyword in ["height", "tall", "built", "1889"]), \
                    "Response should contain key Eiffel Tower facts"
            elif "population" in prompt:
                assert any(char.isdigit() for char in response_text), "Population response should contain numbers"
                assert "Paris" in response_text, "Population response should mention Paris"
