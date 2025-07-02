"""Integration tests for DocNav MCP Server with real document scenarios."""

import pytest
import asyncio
from pathlib import Path
from docnav.server import DocNavMCPServer
from docnav.tools import DocNavTools
from docnav.navigator import DocumentNavigator


class TestIntegrationScenarios:
    """Integration tests using real document scenarios."""
    
    @pytest.fixture
    def large_document_content(self):
        """Large document content for testing scalability."""
        return """# MANTRA DEX Findings & Analysis Report

## Table of Contents

- [Overview](#overview)
- [About C4](#about-c4)
- [Summary](#summary)
- [Scope](#scope)
- [Severity Criteria](#severity-criteria)
- [High Risk Findings (12)](#high-risk-findings-12)
- [Medium Risk Findings (19)](#medium-risk-findings-19)

## Overview

This report contains security findings from the MANTRA DEX audit conducted by Code4rena.

### About This Audit

The audit was conducted over a period of 4 weeks with multiple security researchers.

## Summary

The MANTRA DEX protocol allows users to create and manage decentralized exchange pools.

### Key Findings

- 12 High risk issues identified
- 19 Medium risk issues found
- Multiple areas for improvement

## Scope

The audit covered the following components:

### Smart Contracts

- Pool management contracts
- Token factory contracts
- Farm management system
- Stableswap implementation

### Libraries

- Mathematical libraries
- Utility functions
- Helper contracts

## Severity Criteria

Issues are classified based on their potential impact:

### High Risk

Issues that can lead to:
- Loss of funds
- Protocol manipulation
- Denial of service

### Medium Risk

Issues that can cause:
- Unexpected behavior
- Limited fund loss
- Degraded user experience

### Low Risk

Issues that represent:
- Best practice violations
- Minor optimizations
- Documentation improvements

## High Risk Findings (12)

### H-01: Protocol allows creating broken tri-crypto CPMM pools

**Description**: The protocol validation logic has a flaw that allows creation of pools that cannot function properly.

**Impact**: High - Can lead to unusable pools and locked funds.

**Proof of Concept**:
```solidity
// Example of problematic pool creation
function createBrokenPool() {
    // Missing validation allows this
    pool.create(invalidParams);
}
```

**Recommendation**: Add proper validation for pool parameters.

### H-02: Logical error in validate_fees_are_paid

**Description**: Fee validation logic contains errors that can be exploited.

**Impact**: High - Users can bypass fees or cause DoS.

### H-03: Multi-token stableswap pools allow 0 liquidity

**Description**: Stableswap pools can be created with zero liquidity for some tokens.

**Impact**: High - Creates unusable pools.

## Medium Risk Findings (19)

### M-01: create_pool edge cases

**Description**: Edge cases in pool creation can cause issues.

**Impact**: Medium - Can prevent pool creation or allow underpayment.

### M-02: Penalty fee distribution issues

**Description**: Penalty fees may not be distributed correctly.

**Impact**: Medium - Unfair reward distribution.

## Detailed Analysis

### Pool Management System

The pool management system is the core component responsible for:

1. **Pool Creation**: Validating parameters and creating new pools
2. **Liquidity Management**: Adding and removing liquidity
3. **Fee Collection**: Managing trading and protocol fees
4. **Reward Distribution**: Distributing rewards to liquidity providers

#### Pool Creation Process

```mermaid
graph TD
    A[User Request] --> B[Validate Parameters]
    B --> C[Check Fees]
    C --> D[Create Pool]
    D --> E[Initialize Liquidity]
    E --> F[Emit Events]
```

#### Liquidity Management

The system supports multiple liquidity provision methods:

- **Balanced Deposits**: Equal value deposits
- **Single-sided Deposits**: Deposit only one token
- **Proportional Withdrawals**: Maintain pool ratios

### Token Factory Integration

The protocol integrates with Cosmos SDK's tokenfactory module:

#### Features

- **Dynamic Token Creation**: Create new tokens on demand
- **Metadata Management**: Store token information
- **Supply Control**: Mint and burn tokens as needed

#### Security Considerations

1. **Malicious Tokens**: Attackers can create tokens with malicious behavior
2. **Metadata Manipulation**: Token metadata can be misleading
3. **Supply Attacks**: Unlimited minting can cause issues

### Farm Management System

The farming system provides incentives for liquidity providers:

#### Components

- **Farm Creation**: Set up new incentive programs
- **Reward Calculation**: Compute user rewards
- **Distribution Logic**: Handle reward payouts
- **Emergency Controls**: Emergency unlock mechanisms

#### Known Issues

Several issues were identified in the farming system:

1. **Past Epoch Farms**: Farms can be set to start in past epochs
2. **Reward Calculation**: Division by zero vulnerabilities
3. **Emergency Penalties**: Incorrect penalty calculations

### Stableswap Implementation

The stableswap algorithm enables efficient trading between pegged assets:

#### Algorithm Details

The implementation uses a modified constant product formula optimized for stable assets.

#### Identified Problems

1. **Decimal Handling**: Improper handling of different decimal places
2. **Slippage Protection**: Inadequate slippage checks
3. **Invariant Maintenance**: Broken invariant calculations

## Recommendations

### Immediate Actions Required

1. **Fix High Risk Issues**: Address all high-risk findings immediately
2. **Review Fee Logic**: Completely audit fee calculation and validation
3. **Test Pool Creation**: Comprehensive testing of pool creation edge cases

### Medium-term Improvements

1. **Enhanced Validation**: Implement stricter parameter validation
2. **Better Error Handling**: Improve error messages and handling
3. **Documentation**: Update documentation to reflect security considerations

### Long-term Considerations

1. **Formal Verification**: Consider formal verification for critical components
2. **Bug Bounty Program**: Establish ongoing security incentives
3. **Regular Audits**: Schedule periodic security reviews

## Conclusion

The MANTRA DEX protocol shows promise but requires significant security improvements before production deployment. The identified issues range from critical fund-loss vulnerabilities to user experience problems.

### Key Takeaways

1. **Security First**: Security must be prioritized over feature delivery
2. **Comprehensive Testing**: Edge cases need thorough testing
3. **Community Review**: Consider additional security reviews

### Next Steps

1. Address all high-risk findings
2. Implement recommended mitigations
3. Conduct additional testing
4. Consider follow-up audit

---

*This report was generated using automated analysis tools and manual review. All findings should be verified and tested before implementing fixes.*
"""
    
    @pytest.fixture
    def tools(self):
        """Create DocNavTools instance for testing."""
        return DocNavTools()
    
    @pytest.mark.asyncio
    async def test_large_document_processing(self, tools, large_document_content):
        """Test processing of large, complex documents."""
        # Load the large document
        result = await tools.load_document_text(
            large_document_content, 
            "security_report", 
            "markdown"
        )
        
        assert result["success"] is True
        assert result["document"]["id"] == "security_report"
        assert result["document"]["headings_count"] > 20  # Should have many headings
    
    @pytest.mark.asyncio
    async def test_comprehensive_navigation(self, tools, large_document_content):
        """Test comprehensive navigation through complex document."""
        # Load document
        await tools.load_document_text(large_document_content, "report", "markdown")
        
        # Get structured outline
        outline_result = tools.get_outline("report", max_depth=4, format="structured")
        assert outline_result["success"] is True
        assert len(outline_result["outline"]) > 15  # Many sections
        
        # Find a specific section to navigate to
        h1_sections = [
            item for item in outline_result["outline"] 
            if item["level"] == 1
        ]
        assert len(h1_sections) > 0
        
        # Navigate to first H1 section
        first_section = h1_sections[0]
        nav_result = tools.navigate_section("report", first_section["id"])
        assert nav_result["success"] is True
        assert nav_result["navigation"]["current"]["id"] == first_section["id"]
    
    @pytest.mark.asyncio
    async def test_complex_search_scenarios(self, tools, large_document_content):
        """Test search functionality with complex scenarios."""
        # Load document
        await tools.load_document_text(large_document_content, "report", "markdown")
        
        # Search for technical terms
        search_tests = [
            ("High Risk", "Should find high risk findings"),
            ("stableswap", "Should find stableswap related content"),
            ("protocol", "Should find protocol references"),
            ("validation", "Should find validation issues"),
            ("liquidity", "Should find liquidity management content")
        ]
        
        for query, description in search_tests:
            result = tools.search_document("report", query, max_results=5)
            assert result["success"] is True, f"Failed: {description}"
            assert result["total_results"] > 0, f"No results for: {query}"
            
            # Check result quality
            for search_result in result["results"]:
                assert query.lower() in search_result["content"].lower()
                assert search_result["node_id"] is not None
                assert search_result["section_title"] is not None
    
    @pytest.mark.asyncio
    async def test_section_extraction_accuracy(self, tools, large_document_content):
        """Test accurate section content extraction."""
        # Load document
        await tools.load_document_text(large_document_content, "report", "markdown")
        
        # Get outline to find sections
        outline = tools.get_outline("report", format="structured")
        sections = outline["outline"]
        
        # Test extracting different section types
        for section in sections[:5]:  # Test first 5 sections
            result = tools.get_section("report", section["id"])
            assert result["success"] is True
            
            section_data = result["section"]
            assert section_data["id"] == section["id"]
            assert section_data["title"] == section["title"]
            assert section_data["level"] == section["level"]
            assert len(section_data["content"]) > 0
    
    @pytest.mark.asyncio
    async def test_multi_document_management(self, tools):
        """Test managing multiple documents simultaneously."""
        documents = {
            "doc1": "# Document 1\n## Section A\nContent A",
            "doc2": "# Document 2\n## Section B\nContent B", 
            "doc3": "# Document 3\n## Section C\nContent C"
        }
        
        # Load multiple documents
        for doc_id, content in documents.items():
            result = await tools.load_document_text(content, doc_id)
            assert result["success"] is True
        
        # List all documents
        list_result = tools.list_documents()
        assert list_result["success"] is True
        assert list_result["total_documents"] == 3
        
        # Verify each document is accessible
        for doc_id in documents.keys():
            outline = tools.get_outline(doc_id)
            assert doc_id.split("doc")[1] in outline  # Should contain document number
    
    @pytest.mark.asyncio
    async def test_performance_with_deep_hierarchy(self, tools):
        """Test performance with deeply nested document structure."""
        # Create document with deep hierarchy
        deep_content = "# Level 1\n"
        for i in range(2, 8):  # Create levels 2-7
            deep_content += "#" * i + f" Level {i}\n"
            deep_content += f"Content for level {i}.\n\n"
            
            # Add subsections
            for j in range(1, 4):
                deep_content += "#" * (i + 1) + f" Level {i}.{j}\n"
                deep_content += f"Subsection {j} content.\n\n"
        
        # Load and test
        result = await tools.load_document_text(deep_content, "deep_doc")
        assert result["success"] is True
        
        # Get full outline
        outline = tools.get_outline("deep_doc", max_depth=8, format="structured")
        assert outline["success"] is True
        assert len(outline["outline"]) > 20  # Should have many sections
        
        # Test navigation at different levels
        deep_sections = [s for s in outline["outline"] if s["level"] >= 5]
        if deep_sections:
            nav_result = tools.navigate_section("deep_doc", deep_sections[0]["id"])
            assert nav_result["success"] is True
    
    @pytest.mark.asyncio
    async def test_error_handling_scenarios(self, tools):
        """Test error handling in various scenarios."""
        # Test operations on non-existent document
        error_tests = [
            ("get_outline", lambda: tools.get_outline("nonexistent")),
            ("get_section", lambda: tools.get_section("nonexistent", "h1_0")),
            ("search", lambda: tools.search_document("nonexistent", "query")),
            ("navigate", lambda: tools.navigate_section("nonexistent", "h1_0")),
            ("stats", lambda: tools.get_document_stats("nonexistent"))
        ]
        
        for test_name, test_func in error_tests:
            result = test_func()
            assert "error" in result, f"Expected error for {test_name}"
            assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio 
    async def test_edge_case_content(self, tools):
        """Test handling of edge case content."""
        edge_cases = [
            ("empty", ""),
            ("only_headings", "# H1\n## H2\n### H3"),
            ("no_headings", "Just plain text\nWith multiple lines\nAnd no structure"),
            ("special_chars", "# Heading with émojis 🚀\n## Spëcial chàrs\nContent with ñ"),
            ("code_heavy", "# Code\n```python\ndef test():\n    pass\n```\n## More\n```\ncode block\n```")
        ]
        
        for name, content in edge_cases:
            result = await tools.load_document_text(content, name)
            
            if content:  # Non-empty content should load successfully
                assert result["success"] is True, f"Failed to load {name}"
                
                # Test basic operations
                outline = tools.get_outline(name)
                assert isinstance(outline, str) or "error" in outline
            else:  # Empty content handling
                # Should either succeed with empty result or provide helpful error
                assert "success" in result or "error" in result


class TestRealWorldUsage:
    """Test real-world usage patterns and scenarios."""
    
    @pytest.fixture
    def navigator(self):
        """Create navigator for real-world testing."""
        return DocumentNavigator()
    
    @pytest.mark.asyncio
    async def test_technical_documentation_workflow(self, navigator):
        """Test typical technical documentation workflow."""
        # Load API documentation
        api_doc = """# API Documentation

## Authentication
All API requests require authentication.

### API Keys
Generate API keys in the dashboard.

### Token Authentication  
Use bearer tokens for requests.

## Endpoints

### User Management
Manage user accounts and profiles.

#### GET /users
Retrieve user list.

#### POST /users
Create new user.

#### PUT /users/{id}
Update user information.

#### DELETE /users/{id}
Delete user account.

### Data Operations

#### GET /data
Retrieve data records.

#### POST /data  
Create new data record.

## Rate Limiting
API calls are rate limited.

### Limits
- 1000 requests per hour
- 10000 requests per day

### Headers
Check rate limit headers.

## Error Handling
Standard HTTP error codes.

### Common Errors
- 400: Bad Request
- 401: Unauthorized  
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error
"""
        
        # Load document
        await navigator.load_document_from_text("api_doc", api_doc)
        
        # Typical workflow: Get overview, find specific endpoints, check details
        
        # 1. Get document overview
        outline = navigator.get_outline("api_doc", max_depth=3)
        assert "Authentication" in outline
        assert "Endpoints" in outline
        assert "Error Handling" in outline
        
        # 2. Search for specific functionality
        user_endpoints = navigator.search_document("api_doc", "GET /users")
        assert "GET /users" in user_endpoints
        
        # 3. Navigate to specific section
        compass = navigator.get_document("api_doc")
        endpoint_section = None
        for node in compass.index.values():
            if node.type == "heading" and "User Management" in node.title:
                endpoint_section = node.id
                break
        
        if endpoint_section:
            nav_context = navigator.navigate("api_doc", endpoint_section)
            assert "User Management" in nav_context
            assert "Current:" in nav_context
    
    @pytest.mark.asyncio
    async def test_research_paper_analysis(self, navigator):
        """Test analyzing research paper structure."""
        paper_content = """# Efficient Document Navigation Using Tree Structures

## Abstract
This paper presents a novel approach to document navigation using DOM-like tree structures.

## 1. Introduction
Document navigation is a critical component of information retrieval systems.

### 1.1 Problem Statement
Current navigation systems lack efficient hierarchical traversal.

### 1.2 Contributions
Our main contributions include:
- Novel tree structure approach
- Efficient indexing algorithm  
- Comprehensive evaluation

## 2. Related Work
Previous work in document navigation falls into several categories.

### 2.1 Traditional Approaches
Traditional systems use linear navigation.

### 2.2 Tree-based Methods
Some systems employ tree structures.

## 3. Methodology
Our approach consists of three main components.

### 3.1 Document Parsing
Documents are parsed into hierarchical structures.

### 3.2 Index Construction
We build efficient indices for fast lookup.

### 3.3 Navigation Interface
The interface provides intuitive navigation.

## 4. Evaluation
We evaluated our system on multiple datasets.

### 4.1 Datasets
Three datasets were used for evaluation.

### 4.2 Metrics  
Performance was measured using standard metrics.

### 4.3 Results
Our approach outperforms baselines.

## 5. Conclusion
The proposed system demonstrates significant improvements.

## References
[1] Smith, J. Document Navigation. 2020.
[2] Jones, A. Tree Structures. 2021.
"""
        
        # Load research paper
        await navigator.load_document_from_text("paper", paper_content)
        
        # Research workflow: Navigate sections, find methodology, check results
        
        # 1. Get paper structure
        outline = navigator.get_outline("paper", max_depth=2)
        assert "Abstract" in outline
        assert "Methodology" in outline
        assert "Evaluation" in outline
        
        # 2. Jump to methodology section
        methodology_results = navigator.search_document("paper", "Methodology")
        assert len(methodology_results) > 0
        
        # 3. Check evaluation section
        evaluation_results = navigator.search_document("paper", "evaluation")
        assert "evaluation" in evaluation_results.lower()
        
        # 4. Navigate between related sections
        compass = navigator.get_document("paper")
        method_node = None
        for node in compass.index.values():
            if node.type == "heading" and "Methodology" in node.title:
                method_node = node.id
                break
        
        if method_node:
            nav_info = navigator.navigate("paper", method_node)
            assert "Methodology" in nav_info
            # Should show navigation to other sections


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])