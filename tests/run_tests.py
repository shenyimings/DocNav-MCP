"""Test runner script for DocNav system with comprehensive reporting."""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from docnav.navigator import DocumentCompass, DocumentNavigator
from docnav.tools import DocNavTools
from docnav.server import DocNavMCPServer


class TestRunner:
    """Comprehensive test runner for DocNav system."""
    
    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "performance": {},
            "test_details": []
        }
    
    def log_test(self, test_name: str, status: str, duration: float, details: str = ""):
        """Log test result."""
        self.results["test_details"].append({
            "name": test_name,
            "status": status,
            "duration": duration,
            "details": details
        })
        
        if status == "PASS":
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
            self.results["errors"].append(f"{test_name}: {details}")
        
        print(f"[{status}] {test_name} ({duration:.3f}s)")
        if details and status == "FAIL":
            print(f"    {details}")
    
    def test_basic_functionality(self):
        """Test basic DocumentCompass functionality."""
        start_time = time.time()
        
        try:
            # Create sample document
            sample_doc = """# Introduction
This is a test document for validating basic functionality.

## Getting Started  
Instructions for getting started.

### Prerequisites
- Python 3.8+
- Required packages

### Installation
1. Clone repository
2. Install dependencies  
3. Run setup

## Advanced Usage
More complex scenarios.

### Configuration
System configuration options.

### Troubleshooting
Common issues and solutions.

# Conclusion
Summary and next steps.
"""
            
            # Test DocumentCompass creation
            compass = DocumentCompass(sample_doc, "markdown")
            assert compass.root is not None
            assert len(compass.index) > 0
            
            # Test outline generation
            outline = compass.get_outline(max_depth=3)
            assert "Introduction" in outline
            assert "Getting Started" in outline
            assert "Conclusion" in outline
            
            # Test section retrieval
            intro_node = None
            for node in compass.index.values():
                if node.type == "heading" and node.title == "Introduction":
                    intro_node = node
                    break
            
            assert intro_node is not None
            content = compass.get_section(intro_node.id)
            assert "Introduction" in content
            
            # Test search functionality
            results = compass.search("installation")
            assert len(results) > 0
            
            # Test navigation context
            context = compass.get_navigation_context(intro_node.id)
            assert context.current["title"] == "Introduction"
            
            duration = time.time() - start_time
            self.log_test("Basic Functionality", "PASS", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Basic Functionality", "FAIL", duration, str(e))
    
    async def test_navigator_interface(self):
        """Test DocumentNavigator high-level interface."""
        start_time = time.time()
        
        try:
            navigator = DocumentNavigator()
            
            # Test loading from text
            content = """# Test Document
This is for testing the navigator interface.

## Section 1
Content for section 1.

## Section 2
Content for section 2.
"""
            
            await navigator.load_document_from_text("test_doc", content)
            assert "test_doc" in navigator.loaded_documents
            
            # Test outline interface
            outline = navigator.get_outline("test_doc")
            assert "Test Document" in outline
            
            # Test search interface  
            search_result = navigator.search_document("test_doc", "section")
            assert "section" in search_result.lower()
            
            # Test navigation interface
            compass = navigator.get_document("test_doc")
            section_id = None
            for node in compass.index.values():
                if node.type == "heading" and node.level == 2:
                    section_id = node.id
                    break
            
            if section_id:
                nav_result = navigator.navigate("test_doc", section_id)
                assert "Current:" in nav_result
            
            duration = time.time() - start_time
            self.log_test("Navigator Interface", "PASS", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Navigator Interface", "FAIL", duration, str(e))
    
    async def test_tools_integration(self):
        """Test DocNavTools integration."""
        start_time = time.time()
        
        try:
            tools = DocNavTools()
            
            # Test document loading
            content = """# Tools Test
Testing the tools integration.

## Features
- Document loading
- Content extraction
- Search capabilities

## Examples  
Various examples of usage.
"""
            
            result = await tools.load_document_text(content, "tools_test")
            assert result["success"] is True
            
            # Test outline retrieval
            outline_result = tools.get_outline("tools_test", format="structured")
            assert outline_result["success"] is True
            assert len(outline_result["outline"]) > 0
            
            # Test section extraction
            sections = outline_result["outline"]
            if sections:
                section_result = tools.get_section("tools_test", sections[0]["id"])
                assert section_result["success"] is True
            
            # Test search
            search_result = tools.search_document("tools_test", "features")
            assert search_result["success"] is True
            
            # Test statistics
            stats_result = tools.get_document_stats("tools_test")
            assert stats_result["success"] is True
            
            duration = time.time() - start_time
            self.log_test("Tools Integration", "PASS", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Tools Integration", "FAIL", duration, str(e))
    
    def test_performance_benchmark(self):
        """Test performance with larger documents."""
        start_time = time.time()
        
        try:
            # Create a larger document for performance testing
            large_content = "# Performance Test Document\n\n"
            
            # Generate multiple sections with subsections
            for i in range(1, 21):  # 20 main sections
                large_content += f"## Section {i}\n"
                large_content += f"This is the content for section {i}.\n\n"
                
                # Add subsections
                for j in range(1, 6):  # 5 subsections each
                    large_content += f"### Subsection {i}.{j}\n"
                    large_content += f"Content for subsection {i}.{j} with some searchable text.\n"
                    large_content += "Additional paragraph with more content to search.\n\n"
            
            # Performance metrics
            parse_start = time.time()
            compass = DocumentCompass(large_content, "markdown")
            parse_time = time.time() - parse_start
            
            # Test outline generation performance
            outline_start = time.time()
            outline = compass.get_outline(max_depth=3)
            outline_time = time.time() - outline_start
            
            # Test search performance
            search_start = time.time()
            results = compass.search("searchable")
            search_time = time.time() - search_start
            
            # Store performance metrics
            self.results["performance"] = {
                "document_size": len(large_content),
                "node_count": len(compass.index),
                "parse_time": parse_time,
                "outline_time": outline_time,
                "search_time": search_time,
                "search_results": len(results)
            }
            
            # Validate results
            assert len(compass.index) > 100  # Should have many nodes
            assert len(results) > 50  # Should find many matches
            assert parse_time < 1.0  # Should parse quickly
            assert search_time < 0.5  # Should search quickly
            
            duration = time.time() - start_time
            self.log_test("Performance Benchmark", "PASS", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Performance Benchmark", "FAIL", duration, str(e))
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        start_time = time.time()
        
        try:
            # Test empty document
            empty_compass = DocumentCompass("", "markdown")
            assert empty_compass.root is not None
            
            # Test document with only headings
            heading_only = "# H1\n## H2\n### H3\n#### H4"
            heading_compass = DocumentCompass(heading_only, "markdown")
            headings = [n for n in heading_compass.index.values() if n.type == "heading"]
            assert len(headings) == 4
            
            # Test document with no headings
            no_headings = "Just plain text\nWith multiple lines\nNo structure"
            plain_compass = DocumentCompass(no_headings, "markdown")
            paragraphs = [n for n in plain_compass.index.values() if n.type == "paragraph"]
            assert len(paragraphs) > 0
            
            # Test malformed headings
            malformed = "# Good Heading\n#Bad heading\n## Another Good One"
            malformed_compass = DocumentCompass(malformed, "markdown")
            headings = [n for n in malformed_compass.index.values() if n.type == "heading"]
            assert len(headings) >= 2  # Should parse good headings
            
            # Test very deep nesting
            deep_content = ""
            for level in range(1, 8):
                deep_content += "#" * level + f" Level {level}\n"
                deep_content += f"Content for level {level}.\n\n"
            
            deep_compass = DocumentCompass(deep_content, "markdown")
            deep_headings = [n for n in deep_compass.index.values() if n.type == "heading"]
            assert len(deep_headings) == 7
            
            duration = time.time() - start_time
            self.log_test("Edge Cases", "PASS", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Edge Cases", "FAIL", duration, str(e))
    
    async def test_real_document_scenario(self):
        """Test with a realistic document scenario."""
        start_time = time.time()
        
        try:
            # Simulate a real technical document
            real_doc = """# API Documentation v2.1

## Overview
This document describes the REST API for our service.

### Version Information
- Version: 2.1
- Base URL: https://api.example.com
- Authentication: Bearer Token

## Authentication
All requests require proper authentication.

### Getting Access Tokens
1. Register your application
2. Obtain client credentials
3. Request access token

### Using Tokens
Include the token in the Authorization header:
```
Authorization: Bearer your-token-here
```

## Endpoints

### User Management

#### GET /api/users
Retrieve a list of users.

**Parameters:**
- limit (optional): Number of results (default: 10)
- offset (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "users": [...],
  "total": 150,
  "limit": 10,
  "offset": 0
}
```

#### POST /api/users  
Create a new user account.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword"
}
```

#### PUT /api/users/{id}
Update user information.

#### DELETE /api/users/{id}
Delete a user account.

### Data Management

#### GET /api/data
Retrieve data records.

#### POST /api/data
Create new data record.

## Rate Limiting
API requests are rate limited to prevent abuse.

### Limits
- 1000 requests per hour per user
- 10000 requests per hour for premium accounts

### Rate Limit Headers
- X-RateLimit-Limit: Total limit
- X-RateLimit-Remaining: Remaining requests
- X-RateLimit-Reset: Reset time

## Error Handling
The API uses standard HTTP status codes.

### Common Status Codes
- 200: Success
- 400: Bad Request - Invalid parameters
- 401: Unauthorized - Authentication required
- 403: Forbidden - Access denied
- 404: Not Found - Resource not found
- 429: Too Many Requests - Rate limit exceeded
- 500: Internal Server Error

### Error Response Format
```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "The 'limit' parameter must be between 1 and 100",
    "details": {...}
  }
}
```

## SDKs and Libraries
Official SDKs are available for popular languages.

### JavaScript/Node.js
```javascript
const ApiClient = require('@company/api-client');
const client = new ApiClient('your-token');
```

### Python
```python
from company_api import Client
client = Client(token='your-token')
```

### PHP
```php
use Company\ApiClient;
$client = new ApiClient('your-token');
```

## Examples
Common usage examples and patterns.

### Creating a User
```javascript
const newUser = await client.users.create({
  username: 'johndoe',
  email: 'john@example.com'
});
```

### Searching Data
```javascript
const results = await client.data.search({
  query: 'important data',
  limit: 50
});
```

## Changelog
Recent changes and updates.

### Version 2.1 (2024-01-15)
- Added new data endpoints
- Improved error handling
- Updated rate limiting

### Version 2.0 (2023-12-01)
- Complete API redesign
- Breaking changes in authentication
- New endpoint structure

## Support
For support and questions:
- Email: api-support@company.com
- Documentation: https://docs.company.com
- Status Page: https://status.company.com
"""
            
            navigator = DocumentNavigator()
            await navigator.load_document_from_text("api_docs", real_doc)
            
            # Test comprehensive navigation
            outline = navigator.get_outline("api_docs", max_depth=3)
            assert "Authentication" in outline
            assert "Endpoints" in outline
            assert "Error Handling" in outline
            
            # Test specific searches
            auth_results = navigator.search_document("api_docs", "authentication")
            assert "authentication" in auth_results.lower()
            
            endpoint_results = navigator.search_document("api_docs", "POST /api/users")
            assert "POST" in endpoint_results
            
            # Test navigation between sections
            compass = navigator.get_document("api_docs")
            endpoint_section = None
            for node in compass.index.values():
                if node.type == "heading" and "Endpoints" in node.title:
                    endpoint_section = node.id
                    break
            
            if endpoint_section:
                nav_context = navigator.navigate("api_docs", endpoint_section)
                assert "Endpoints" in nav_context
            
            duration = time.time() - start_time
            self.log_test("Real Document Scenario", "PASS", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Real Document Scenario", "FAIL", duration, str(e))
    
    async def run_all_tests(self):
        """Run all tests and generate report."""
        print("DocNav System Test Suite")
        print("=" * 50)
        print()
        
        # Run synchronous tests
        self.test_basic_functionality()
        self.test_performance_benchmark()
        self.test_edge_cases()
        
        # Run asynchronous tests  
        await self.test_navigator_interface()
        await self.test_tools_integration()
        await self.test_real_document_scenario()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report."""
        print()
        print("Test Results Summary")
        print("=" * 50)
        print(f"Total Tests: {self.results['passed'] + self.results['failed']}")
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        
        if self.results["failed"] > 0:
            print("\nFailed Tests:")
            for error in self.results["errors"]:
                print(f"  - {error}")
        
        if self.results["performance"]:
            print("\nPerformance Metrics:")
            perf = self.results["performance"]
            print(f"  Document Size: {perf['document_size']:,} characters")
            print(f"  Nodes Created: {perf['node_count']:,}")
            print(f"  Parse Time: {perf['parse_time']:.3f}s")
            print(f"  Outline Time: {perf['outline_time']:.3f}s")
            print(f"  Search Time: {perf['search_time']:.3f}s")
            print(f"  Search Results: {perf['search_results']}")
        
        print("\nDetailed Test Results:")
        for test in self.results["test_details"]:
            status_icon = "✓" if test["status"] == "PASS" else "✗"
            print(f"  {status_icon} {test['name']}: {test['duration']:.3f}s")
        
        # Overall status
        print()
        if self.results["failed"] == 0:
            print("🎉 All tests passed! DocNav system is working correctly.")
        else:
            print(f"❌ {self.results['failed']} test(s) failed. Please review the errors above.")
        
        return self.results["failed"] == 0


async def main():
    """Main test execution function."""
    runner = TestRunner()
    success = await runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())