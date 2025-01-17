# llm-claude-3-caching

[![PyPI](https://img.shields.io/pypi/v/llm-claude-3.svg)](https://pypi.org/project/llm-claude-3/)
[![Changelog](https://img.shields.io/github/v/release/simonw/llm-claude-3?include_prereleases&label=changelog)](https://github.com/simonw/llm-claude-3/releases)
[![Tests](https://github.com/simonw/llm-claude-3/actions/workflows/test.yml/badge.svg)](https://github.com/simonw/llm-claude-3/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/llm-claude-3/blob/main/LICENSE)

A version of the llm-claude-3 plugin that supports caching. Forked from an older version, this branch does not support images or attachements.

## Installation

Install this plugin in the same environment as [LLM](https://llm.datasette.io/).
```bash
git clone -b prompt-caching https://github.com/irthomasthomas/llm-claude-3-caching.git
cd llm-claude-3-caching
llm install -e .
```
## Usage

First, set [an API key](https://console.anthropic.com/settings/keys) for Claude 3:
```bash
llm keys set claude
# Paste key here
```

Run `llm models` to list the models, and `llm models --options` to include a list of their options.

Run prompts like this:
```bash
llm -m claude-3.5-sonnet-cache 'Fun facts about pelicans' -o cache_prompt 1
llm -m claude-3-opus-cache 'Fun facts about squirrels' -o cache_prompt 1
llm -m claude-3-sonnet-cache 'Fun facts about walruses' -o cache_prompt 1
llm -m claude-3-haiku-cache 'Fun facts about armadillos' -o cache_prompt 1
```

## Prompt Caching

This plugin now supports Anthropic's Prompt Caching feature, which can significantly improve performance and reduce costs for certain types of queries.

### How It Works

Prompt Caching allows you to store and reuse context within your prompt. This is especially useful for:

- Prompts with many examples
- Large amounts of context or background information
- Repetitive tasks with consistent instructions
- Long multi-turn conversations

The cache has a 5-minute lifetime, refreshed each time the cached content is used.

### Usage

To enable Prompt Caching, use the following options:

- `-o cache_prompt 1`: Enables caching for the user prompt.
- `-o cache_system 1`: Enables caching for the system prompt.

Example:
```bash
llm -m claude-3-sonnet -o cache_prompt 1 'Analyze this text: [long text here]'
llm -m claude-3-sonnet -o cache_prompt 1 -o cache_system 1 'Analyze this text: [long text here]' --system '[long system prompt here]'

llm -c # continues from cached prompt, if available
```

### Benefits

Based on comprehensive testing across all models:

| Model | Cost Reduction Range | Average Reduction |
|-------|---------------------|-------------------|
| Claude 3 Haiku | 78.1% - 99.1% | 92.0% |
| Claude 3 Opus | 78.1% - 99.0% | 91.9% |
| Claude 3.5 Sonnet | 91.2% - 99.0% | 95.2% |

Example cost reductions:
- Short queries (e.g., "What is the capital of France?")
  - Haiku: $0.000016 → $0.000003 (78.1% reduction)
  - Opus: $0.000960 → $0.000210 (78.1% reduction)
  - Sonnet: $0.000477 → $0.000042 (91.2% reduction)
- Detailed queries (e.g., "Tell me about the Eiffel Tower")
  - Haiku: $0.000428 → $0.000004 (99.1% reduction)
  - Opus: $0.024840 → $0.000240 (99.0% reduction)
  - Sonnet: $0.004653 → $0.000048 (99.0% reduction)

Additional benefits:
- Reduced latency: Improved response times by over 2x
- Improved consistency: Maintained response quality across cached queries
- Zero output token costs for cached responses

### Caching Behavior

- The system checks if the prompt prefix is already cached from a recent query.
- If found, it uses the cached version, reducing processing time and costs.
- Otherwise, it processes the full prompt and caches the prefix for future use.

### Supported Models

Prompt Caching is currently supported on:

- Claude 3.5 Sonnet
- claude 3.5 Haiku
- Claude 3 Haiku
- Claude 3 Opus

### Performance Tracking

You can monitor cache performance using these fields in the API response:

- `cache_creation_input_tokens`: Number of tokens written to the cache when creating a new entry.
- `cache_read_input_tokens`: Number of tokens retrieved from the cache for this request.
  
## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:
```bash
cd llm-claude-3
python3 -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
llm install -e '.[test]'
```
To run the tests:
```bash
pytest
```
