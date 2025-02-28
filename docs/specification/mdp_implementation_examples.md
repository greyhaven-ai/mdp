---
title: "MDP Implementation Examples"
version: "1.0.0"
author: "Datapack Team"
published_date: "2024-10-18"
status: "Draft"
---

# MDP Implementation Examples

This document provides implementation examples for working with MDP files in various programming languages.

## Python

The reference implementation of MDP is available as a Python package:

```bash
pip install mdp
```

### Reading MDP Files

```python
from mdp import read_mdp

# Read an MDP file
doc = read_mdp("document.mdp")

# Access metadata
title = doc.metadata["title"]
author = doc.metadata.get("author", "Unknown")
tags = doc.metadata.get("tags", [])

# Access content
content = doc.content

# Access file path (if available)
file_path = doc.path
```

### Writing MDP Files

```python
from mdp import write_mdp

# Create metadata
metadata = {
    "title": "My Document",
    "author": "Your Name",
    "created_at": "2024-10-18",
    "tags": ["example", "documentation"]
}

# Create content
content = """# My Document

This is an example of creating an MDP document programmatically.

## Section

Content goes here.
"""

# Write to file
doc = write_mdp("new_document.mdp", metadata, content)
```

### Working with Relationships

```python
from mdp.utils import find_related_documents

# Find all related documents
related_docs = find_related_documents(doc)

# Find documents with specific relationship type
parent_docs = find_related_documents(doc, relationship_type="parent")

# Process related documents
for related in related_docs:
    print(f"Related document: {related.metadata['title']}")
```

### Collections

```python
from mdp.utils import find_collection_members, create_collection

# Find all members of a collection
collection_docs = find_collection_members(
    directory="./documents/",
    collection_name="Tutorial Series",
    recursive=True
)

# Create a new collection
documents = [
    {
        "filename": "intro.mdp",
        "metadata": {
            "title": "Introduction",
            "author": "Your Name",
            "created_at": "2024-10-18"
        },
        "content": "# Introduction\n\nThis is the introduction."
    },
    {
        "filename": "chapter1.mdp",
        "metadata": {
            "title": "Chapter 1",
            "author": "Your Name",
            "created_at": "2024-10-18"
        },
        "content": "# Chapter 1\n\nThis is chapter 1."
    }
]

collection = create_collection(
    directory="./new_collection/",
    collection_name="Tutorial Series",
    collection_id="tutorial-2024",
    documents=documents
)
```

### Batch Processing

```python
from mdp.utils import find_mdp_files, batch_convert_to_mdp

# Find all MDP files in a directory
mdp_files = find_mdp_files("./documents/", recursive=True)

# Convert multiple markdown files to MDP
converted = batch_convert_to_mdp(
    source_directory="./markdown_files/",
    target_directory="./mdp_files/",
    file_extensions=[".md", ".markdown"],
    recursive=True,
    metadata={
        "author": "Conversion Script",
        "converted_at": "2024-10-18"
    }
)
```

### Manual Parsing and Generation

For more control, you can implement MDP parsing and generation directly:

```python
import yaml
import re
from pathlib import Path

def read_mdp_manual(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract YAML frontmatter
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if frontmatter_match:
        yaml_str = frontmatter_match.group(1)
        metadata = yaml.safe_load(yaml_str)
        markdown_content = content[frontmatter_match.end():]
    else:
        metadata = {}
        markdown_content = content
    
    return metadata, markdown_content

def write_mdp_manual(file_path, metadata, content):
    yaml_str = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"---\n{yaml_str}---\n\n{content}")
    
    return {
        "path": Path(file_path),
        "metadata": metadata,
        "content": content
    }
```

## JavaScript

While the JavaScript implementation is still in development, here's how you might work with MDP files in Node.js:

```javascript
const fs = require('fs');
const yaml = require('js-yaml');
const path = require('path');

// Read an MDP file
function readMdp(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  
  // Extract YAML frontmatter using regex
  const match = content.match(/^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/);
  
  if (match) {
    const [_, yamlStr, markdownContent] = match;
    const metadata = yaml.load(yamlStr);
    
    return {
      path: path.resolve(filePath),
      metadata,
      content: markdownContent
    };
  } else {
    // No frontmatter found, treat entire content as markdown
    return {
      path: path.resolve(filePath),
      metadata: {},
      content
    };
  }
}

// Write an MDP file
function writeMdp(filePath, metadata, content) {
  const yamlStr = yaml.dump(metadata);
  const mdpContent = `---\n${yamlStr}---\n\n${content}`;
  
  fs.writeFileSync(filePath, mdpContent, 'utf-8');
  
  return {
    path: path.resolve(filePath),
    metadata,
    content
  };
}

// Example usage
const doc = readMdp('document.mdp');
console.log('Title:', doc.metadata.title);
console.log('Content:', doc.content);

const newDoc = writeMdp('new_document.mdp', {
  title: 'New Document',
  author: 'Node.js User',
  created_at: '2024-10-18'
}, '# New Document\n\nCreated with Node.js');
```

## Ruby

A simple implementation in Ruby:

```ruby
require 'yaml'

# Read an MDP file
def read_mdp(file_path)
  content = File.read(file_path)
  
  # Extract YAML frontmatter
  if content =~ /^---\s*\n(.*?)\n---\s*\n(.*)/m
    yaml_str = $1
    markdown_content = $2
    metadata = YAML.safe_load(yaml_str)
  else
    metadata = {}
    markdown_content = content
  end
  
  {
    path: File.expand_path(file_path),
    metadata: metadata,
    content: markdown_content
  }
end

# Write an MDP file
def write_mdp(file_path, metadata, content)
  yaml_str = metadata.to_yaml
  mdp_content = "---\n#{yaml_str}---\n\n#{content}"
  
  File.write(file_path, mdp_content)
  
  {
    path: File.expand_path(file_path),
    metadata: metadata,
    content: content
  }
end

# Example usage
doc = read_mdp('document.mdp')
puts "Title: #{doc[:metadata]['title']}"

new_doc = write_mdp('new_document.mdp', {
  'title' => 'Ruby Document',
  'author' => 'Ruby User',
  'created_at' => '2024-10-18'
}, "# Ruby Document\n\nCreated with Ruby")
```

## Go

A basic implementation in Go:

```go
package main

import (
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"regexp"

	"gopkg.in/yaml.v3"
)

type MDPFile struct {
	Path     string
	Metadata map[string]interface{}
	Content  string
}

// Read an MDP file
func ReadMDP(filePath string) (*MDPFile, error) {
	content, err := ioutil.ReadFile(filePath)
	if err != nil {
		return nil, err
	}

	// Extract YAML frontmatter
	re := regexp.MustCompile(`(?s)^---\s*\n(.*?)\n---\s*\n(.*)$`)
	matches := re.FindSubmatch(content)

	mdpFile := &MDPFile{
		Path:     filepath.Abs(filePath),
		Metadata: make(map[string]interface{}),
	}

	if len(matches) == 3 {
		// Parse YAML frontmatter
		yamlStr := matches[1]
		err = yaml.Unmarshal(yamlStr, &mdpFile.Metadata)
		if err != nil {
			return nil, err
		}
		mdpFile.Content = string(matches[2])
	} else {
		// No frontmatter found, treat entire content as markdown
		mdpFile.Content = string(content)
	}

	return mdpFile, nil
}

// Write an MDP file
func WriteMDP(filePath string, metadata map[string]interface{}, content string) (*MDPFile, error) {
	yamlBytes, err := yaml.Marshal(metadata)
	if err != nil {
		return nil, err
	}

	mdpContent := fmt.Sprintf("---\n%s---\n\n%s", string(yamlBytes), content)
	err = ioutil.WriteFile(filePath, []byte(mdpContent), 0644)
	if err != nil {
		return nil, err
	}

	absPath, _ := filepath.Abs(filePath)
	return &MDPFile{
		Path:     absPath,
		Metadata: metadata,
		Content:  content,
	}, nil
}

func main() {
	// Example usage
	doc, err := ReadMDP("document.mdp")
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Title: %v\n", doc.Metadata["title"])

	metadata := map[string]interface{}{
		"title":      "Go Document",
		"author":     "Go User",
		"created_at": "2024-10-18",
	}
	content := "# Go Document\n\nCreated with Go"

	newDoc, err := WriteMDP("new_document.mdp", metadata, content)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Created document: %s\n", newDoc.Path)
}
```

## Integration Patterns

### Web Applications

```javascript
// Express.js route that serves MDP content as HTML
const express = require('express');
const fs = require('fs');
const yaml = require('js-yaml');
const marked = require('marked');
const app = express();

app.get('/docs/:docId', (req, res) => {
  const docPath = `./documents/${req.params.docId}.mdp`;
  
  try {
    const content = fs.readFileSync(docPath, 'utf-8');
    const match = content.match(/^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/);
    
    if (match) {
      const [_, yamlStr, markdownContent] = match;
      const metadata = yaml.load(yamlStr);
      const htmlContent = marked.parse(markdownContent);
      
      res.render('document', {
        title: metadata.title,
        metadata: metadata,
        content: htmlContent
      });
    } else {
      res.status(400).send('Invalid MDP document format');
    }
  } catch (error) {
    res.status(404).send('Document not found');
  }
});

app.listen(3000);
```

### Content Management Systems

```python
# Django model for MDP documents
from django.db import models
import yaml
import markdown

class MDPDocument(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100, blank=True)
    created_at = models.DateField()
    updated_at = models.DateField(auto_now=True)
    tags = models.JSONField(default=list)
    content = models.TextField()
    
    def get_metadata(self):
        """Get document metadata as a dictionary"""
        return {
            'title': self.title,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': self.tags,
        }
    
    def to_mdp(self):
        """Convert to MDP format"""
        yaml_str = yaml.dump(self.get_metadata())
        return f"---\n{yaml_str}---\n\n{self.content}"
    
    def to_html(self):
        """Convert content to HTML"""
        return markdown.markdown(self.content)
    
    @classmethod
    def from_mdp(cls, mdp_content):
        """Create a document from MDP content"""
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", mdp_content, re.DOTALL)
        if match:
            yaml_str = match.group(1)
            content = match.group(2)
            metadata = yaml.safe_load(yaml_str)
            
            return cls(
                title=metadata.get('title', ''),
                author=metadata.get('author', ''),
                created_at=metadata.get('created_at'),
                tags=metadata.get('tags', []),
                content=content
            )
        return None
```

## Best Practices

1. **Always validate** required metadata fields
2. **Handle encoding** properly (use UTF-8)
3. **Preserve formatting** in the markdown content
4. **Generate UUIDs** for documents without them
5. **Use ISO 8601** for date fields (YYYY-MM-DD)
6. **Implement graceful fallbacks** for missing fields
7. **Support custom fields** with the `x_` prefix
8. **Properly escape** YAML special characters
9. **Maintain relationship integrity** when modifying documents
10. **Include file paths** in errors for better debugging

## Common Issues and Solutions

### Invalid YAML

```python
try:
    metadata = yaml.safe_load(yaml_str)
except yaml.YAMLError as e:
    print(f"Invalid YAML in frontmatter: {e}")
    # Fallback to empty metadata
    metadata = {}
```

### Missing Required Fields

```python
def validate_metadata(metadata):
    if "title" not in metadata:
        raise ValueError("MDP document must have a title")
    
    # Additional validation...
    return metadata
```

### Handling Relationships

```python
def validate_relationships(relationships):
    for rel in relationships:
        if "type" not in rel:
            raise ValueError("Relationship missing required 'type' field")
            
        if rel["type"] not in ["parent", "child", "related", "reference"]:
            raise ValueError(f"Invalid relationship type: {rel['type']}")
            
        # Check for at least one identifier
        if not any(k in rel for k in ["id", "path", "uri", "cid"]):
            raise ValueError("Relationship missing identifier (id, path, uri, or cid)")
    
    return relationships
``` 