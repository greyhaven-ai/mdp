"""
Documentation and examples specifically formatted for LLM consumption.

This module provides documentation strings, examples, and schemas that
can be accessed by LLMs to understand how to interact with the MCP server.
"""

import json
import os

# Path to schema files
SCHEMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                          "docs", "specification")

# Load schemas for documentation if available
def load_schema(filename):
    """Load a schema file from the specification directory."""
    path = os.path.join(SCHEMA_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

# Main server documentation
SERVER_DOCUMENTATION = """
# MDP Document Server

This MCP server provides access to MDP (Markdown Data Pack) documents.
MDP documents combine structured metadata with markdown content.

## Available Tools

This server provides the following tools for working with documents:

1. `create_document` - Create a new document
2. `update_document` - Update an existing document
3. `delete_document` - Delete a document
4. `search_documents` - Search for documents
5. `fetch_context` - Fetch context for a query

## Available Resources

- `mdp://docs/{doc_id}` - Get document content
- `mdp://docs/{doc_id}/metadata` - Get document metadata
- `mdp://collections/list` - List all documents

## Document Format

MDP documents follow this format:

```
---
title: Document Title
author: Author Name
tags: [tag1, tag2]
... other metadata ...
---

Document content in Markdown format...
```

The metadata section uses YAML syntax and is separated from the content by `---`.
"""

# Tool documentation
TOOL_DOCUMENTATION = {
    "create_document": {
        "name": "create_document",
        "description": "Create a new MDP document",
        "input_schema": {
            "type": "object",
            "required": ["content"],
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The document content in MDP format"
                }
            }
        },
        "output_schema": {
            "type": "object",
            "required": ["doc_id", "message"],
            "properties": {
                "doc_id": {
                    "type": "string",
                    "description": "The UUID of the created document"
                },
                "message": {
                    "type": "string",
                    "description": "Status message"
                }
            }
        },
        "examples": [
            {
                "input": {
                    "content": """---
title: Example Document
tags: [example, documentation]
---

This is an example document."""
                },
                "output": {
                    "doc_id": "123e4567-e89b-12d3-a456-426614174000", 
                    "message": "Document created: 123e4567-e89b-12d3-a456-426614174000"
                }
            }
        ]
    },
    "update_document": {
        "name": "update_document",
        "description": "Update an existing MDP document",
        "input_schema": {
            "type": "object",
            "required": ["doc_id", "content"],
            "properties": {
                "doc_id": {
                    "type": "string",
                    "description": "Document ID to update"
                },
                "content": {
                    "type": "string",
                    "description": "The updated document content in MDP format"
                },
                "metadata": {
                    "type": "object",
                    "description": "Document metadata (optional)"
                }
            }
        },
        "output_schema": {
            "type": "object",
            "required": ["message"],
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Status message"
                }
            }
        },
        "examples": [
            {
                "input": {
                    "doc_id": "123e4567-e89b-12d3-a456-426614174000",
                    "content": """---
title: Updated Document
tags: [example, updated]
---

This document has been updated."""
                },
                "output": {
                    "message": "Document updated: 123e4567-e89b-12d3-a456-426614174000"
                }
            }
        ]
    },
    "delete_document": {
        "name": "delete_document",
        "description": "Delete an MDP document by ID",
        "input_schema": {
            "type": "object",
            "required": ["doc_id"],
            "properties": {
                "doc_id": {
                    "type": "string",
                    "description": "ID of the document to delete"
                }
            }
        },
        "output_schema": {
            "type": "object",
            "required": ["message"],
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Status message"
                }
            }
        },
        "examples": [
            {
                "input": {
                    "doc_id": "123e4567-e89b-12d3-a456-426614174000"
                },
                "output": {
                    "message": "Document deleted: 123e4567-e89b-12d3-a456-426614174000"
                }
            }
        ]
    },
    "search_documents": {
        "name": "search_documents",
        "description": "Search for documents matching a query string",
        "input_schema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10
                }
            }
        },
        "output_schema": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Document title"
                    },
                    "uuid": {
                        "type": "string",
                        "description": "Document UUID"
                    },
                    "tags": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Document tags"
                    }
                }
            }
        },
        "examples": [
            {
                "input": {
                    "query": "example",
                    "max_results": 5
                },
                "output": [
                    {
                        "title": "Example Document",
                        "uuid": "123e4567-e89b-12d3-a456-426614174000",
                        "tags": ["example", "documentation"]
                    }
                ]
            }
        ]
    },
    "fetch_context": {
        "name": "fetch_context",
        "description": "Fetch relevant document context based on a query",
        "input_schema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to fetch context for"
                },
                "doc_ids": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Optional list of document IDs to search within"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 5
                }
            }
        },
        "output_schema": {
            "type": "string",
            "description": "Relevant document content that matches the query"
        },
        "examples": [
            {
                "input": {
                    "query": "example documentation",
                    "max_results": 3
                },
                "output": "# Example Document\n\nThis is an example document that explains documentation."
            }
        ]
    }
}

# Examples of complete workflows for LLMs
LLM_WORKFLOW_EXAMPLES = [
    {
        "title": "Creating and retrieving a document",
        "steps": [
            {
                "user": "I want to create a new document about climate change",
                "llm_thought": "I should use the create_document tool to create a new document with climate change content.",
                "llm_action": "create_document",
                "llm_action_input": {
                    "content": """---
title: Climate Change Overview
author: AI Assistant
tags: [climate, environment, science]
---

# Climate Change Overview

Climate change refers to long-term shifts in temperatures and weather patterns. 
These shifts may be natural, but since the 1800s, human activities have been 
the main driver of climate change, primarily due to the burning of fossil fuels.
"""
                },
                "action_result": {
                    "doc_id": "98765432-abcd-5678-efgh-987654321012",
                    "message": "Document created: 98765432-abcd-5678-efgh-987654321012"
                },
                "llm_response": "I've created a new document about climate change for you. The document includes an overview of what climate change is and mentions human activities as the main driver since the 1800s. The document has been saved with the ID 98765432-abcd-5678-efgh-987654321012."
            },
            {
                "user": "Can you show me the document I just created?",
                "llm_thought": "I need to use the resource endpoint to retrieve the document content using its ID.",
                "llm_action": "read_resource",
                "llm_action_input": {
                    "resource_path": "mdp://docs/98765432-abcd-5678-efgh-987654321012"
                },
                "action_result": """---
title: Climate Change Overview
author: AI Assistant
tags: [climate, environment, science]
uuid: 98765432-abcd-5678-efgh-987654321012
---

# Climate Change Overview

Climate change refers to long-term shifts in temperatures and weather patterns. 
These shifts may be natural, but since the 1800s, human activities have been 
the main driver of climate change, primarily due to the burning of fossil fuels.""",
                "llm_response": "Here's the document you created about climate change:\n\n# Climate Change Overview\n\nClimate change refers to long-term shifts in temperatures and weather patterns. These shifts may be natural, but since the 1800s, human activities have been the main driver of climate change, primarily due to the burning of fossil fuels."
            }
        ]
    },
    {
        "title": "Searching and updating documents",
        "steps": [
            {
                "user": "Find me documents about climate",
                "llm_thought": "I should use the search_documents tool to find documents related to climate.",
                "llm_action": "search_documents",
                "llm_action_input": {
                    "query": "climate",
                    "max_results": 5
                },
                "action_result": [
                    {
                        "title": "Climate Change Overview",
                        "uuid": "98765432-abcd-5678-efgh-987654321012",
                        "tags": ["climate", "environment", "science"]
                    }
                ],
                "llm_response": "I found 1 document about climate:\n\n- Climate Change Overview (Document ID: 98765432-abcd-5678-efgh-987654321012)\n\nWould you like me to show you the content of this document?"
            },
            {
                "user": "Update that document to include information about mitigation strategies",
                "llm_thought": "I need to first get the current document, then update it with additional information about mitigation strategies.",
                "llm_actions": [
                    {
                        "action": "read_resource",
                        "input": {
                            "resource_path": "mdp://docs/98765432-abcd-5678-efgh-987654321012"
                        },
                        "result": """---
title: Climate Change Overview
author: AI Assistant
tags: [climate, environment, science]
uuid: 98765432-abcd-5678-efgh-987654321012
---

# Climate Change Overview

Climate change refers to long-term shifts in temperatures and weather patterns. 
These shifts may be natural, but since the 1800s, human activities have been 
the main driver of climate change, primarily due to the burning of fossil fuels."""
                    },
                    {
                        "action": "update_document",
                        "input": {
                            "doc_id": "98765432-abcd-5678-efgh-987654321012",
                            "content": """---
title: Climate Change Overview
author: AI Assistant
tags: [climate, environment, science, mitigation]
uuid: 98765432-abcd-5678-efgh-987654321012
---

# Climate Change Overview

Climate change refers to long-term shifts in temperatures and weather patterns. 
These shifts may be natural, but since the 1800s, human activities have been 
the main driver of climate change, primarily due to the burning of fossil fuels.

## Mitigation Strategies

Several approaches can help mitigate climate change:

1. **Renewable Energy** - Transitioning to solar, wind, and hydroelectric power
2. **Energy Efficiency** - Reducing energy consumption through better technology
3. **Carbon Capture** - Removing CO2 from the atmosphere
4. **Sustainable Transportation** - Electric vehicles and public transit
5. **Policy Changes** - Carbon pricing and emissions regulations"""
                        },
                        "result": {
                            "message": "Document updated: 98765432-abcd-5678-efgh-987654321012"
                        }
                    }
                ],
                "llm_response": "I've updated the Climate Change Overview document to include a new section about mitigation strategies. The document now covers five key approaches to mitigate climate change:\n\n1. Renewable Energy\n2. Energy Efficiency\n3. Carbon Capture\n4. Sustainable Transportation\n5. Policy Changes\n\nI've also added 'mitigation' as a tag to the document."
            }
        ]
    }
]

def get_server_documentation():
    """Get the main server documentation."""
    return SERVER_DOCUMENTATION

def get_tool_documentation(tool_name=None):
    """
    Get documentation for tools.
    
    Args:
        tool_name: Optional name of a specific tool
        
    Returns:
        Tool documentation in a structured format
    """
    if tool_name and tool_name in TOOL_DOCUMENTATION:
        return TOOL_DOCUMENTATION[tool_name]
    return TOOL_DOCUMENTATION

def get_workflow_examples():
    """Get examples of complete LLM workflows."""
    return LLM_WORKFLOW_EXAMPLES

def get_documentation_markdown():
    """Get complete documentation in markdown format."""
    doc = [SERVER_DOCUMENTATION, "\n\n## Tool Documentation\n"]
    
    for tool_name, tool_doc in TOOL_DOCUMENTATION.items():
        doc.append(f"### {tool_name}\n")
        doc.append(f"{tool_doc['description']}\n")
        
        doc.append("**Input:**\n")
        doc.append("```json\n")
        doc.append(json.dumps(tool_doc["input_schema"], indent=2))
        doc.append("\n```\n")
        
        doc.append("**Output:**\n")
        doc.append("```json\n")
        doc.append(json.dumps(tool_doc["output_schema"], indent=2))
        doc.append("\n```\n")
        
        doc.append("**Example:**\n")
        if tool_doc["examples"]:
            example = tool_doc["examples"][0]
            doc.append("Input:\n")
            doc.append("```json\n")
            doc.append(json.dumps(example["input"], indent=2))
            doc.append("\n```\n")
            doc.append("Output:\n")
            doc.append("```json\n")
            doc.append(json.dumps(example["output"], indent=2))
            doc.append("\n```\n")
    
    return "\n".join(doc) 