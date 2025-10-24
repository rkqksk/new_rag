"""
MCP Protocol Integration Tests for Plugin System

Tests that RAG Orchestrator MCP tools work correctly through MCP protocol
"""

import pytest
import json
import asyncio
from typing import Dict, Any

# Import MCP server and handler
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mcp_servers"))

try:
    from rag_orchestrator import RAGOrchestratorServer, handle_request
    MCP_SERVER_AVAILABLE = True
except ImportError:
    MCP_SERVER_AVAILABLE = False
    pytest.skip("RAG Orchestrator MCP server not available", allow_module_level=True)


@pytest.fixture
async def rag_server():
    """Initialize RAG Orchestrator server"""
    server = RAGOrchestratorServer()
    yield server
    await server.shutdown()


@pytest.fixture
def sample_manufacturing_document():
    """Sample manufacturing document for testing"""
    return {
        "content": """
        Standard Operating Procedure: Injection Molding

        Equipment: Injection molding machine (Model XY-500)
        Material: ABS plastic resin

        Process Parameters:
        - Mold temperature: 220°C
        - Injection pressure: 150 MPa
        - Cooling time: 30 seconds
        """,
        "filename": "injection_molding_sop.pdf"
    }


class TestMCPToolsList:
    """Test MCP tools/list endpoint"""

    @pytest.mark.asyncio
    async def test_tools_list_endpoint(self, rag_server):
        """Test that tools/list returns correct tool definitions"""
        request = {
            "method": "tools/list",
            "params": {}
        }

        response = await handle_request(rag_server, request)

        # Verify response structure
        assert "tools" in response
        assert isinstance(response["tools"], list)
        assert len(response["tools"]) >= 5  # At least basic tools + plugin tools

        # Find plugin tools
        tool_names = [tool["name"] for tool in response["tools"]]

        assert "process_document" in tool_names, "process_document tool missing"
        assert "get_plugin_info" in tool_names, "get_plugin_info tool missing"

    @pytest.mark.asyncio
    async def test_process_document_tool_schema(self, rag_server):
        """Test that process_document tool has correct schema"""
        request = {
            "method": "tools/list",
            "params": {}
        }

        response = await handle_request(rag_server, request)

        # Find process_document tool
        process_doc_tool = None
        for tool in response["tools"]:
            if tool["name"] == "process_document":
                process_doc_tool = tool
                break

        assert process_doc_tool is not None, "process_document tool not found"

        # Verify schema
        assert "description" in process_doc_tool
        assert "inputSchema" in process_doc_tool

        schema = process_doc_tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "document" in schema["properties"]
        assert "required" in schema
        assert "document" in schema["required"]

    @pytest.mark.asyncio
    async def test_get_plugin_info_tool_schema(self, rag_server):
        """Test that get_plugin_info tool has correct schema"""
        request = {
            "method": "tools/list",
            "params": {}
        }

        response = await handle_request(rag_server, request)

        # Find get_plugin_info tool
        plugin_info_tool = None
        for tool in response["tools"]:
            if tool["name"] == "get_plugin_info":
                plugin_info_tool = tool
                break

        assert plugin_info_tool is not None, "get_plugin_info tool not found"

        # Verify schema
        assert "description" in plugin_info_tool
        assert "inputSchema" in plugin_info_tool

        schema = plugin_info_tool["inputSchema"]
        assert schema["type"] == "object"
        # get_plugin_info has no required parameters


class TestMCPToolsCall:
    """Test MCP tools/call endpoint"""

    @pytest.mark.asyncio
    async def test_get_plugin_info_call(self, rag_server):
        """Test calling get_plugin_info through MCP protocol"""
        request = {
            "method": "tools/call",
            "params": {
                "name": "get_plugin_info",
                "arguments": {}
            }
        }

        response = await handle_request(rag_server, request)

        # Verify response structure
        assert "content" in response
        assert isinstance(response["content"], list)
        assert len(response["content"]) > 0

        # Parse the result
        content = response["content"][0]
        assert content["type"] == "text"

        result = json.loads(content["text"])
        assert "success" in result
        assert "plugins_available" in result

        if result["plugins_available"]:
            assert "plugins" in result
            assert "plugin_count" in result
            assert result["plugin_count"] >= 2  # Manufacturing + Packaging

    @pytest.mark.asyncio
    async def test_process_document_call(
        self, rag_server, sample_manufacturing_document
    ):
        """Test calling process_document through MCP protocol"""
        request = {
            "method": "tools/call",
            "params": {
                "name": "process_document",
                "arguments": {
                    "document": sample_manufacturing_document
                }
            }
        }

        response = await handle_request(rag_server, request)

        # Verify response structure
        assert "content" in response
        assert isinstance(response["content"], list)
        assert len(response["content"]) > 0

        # Parse the result
        content = response["content"][0]
        assert content["type"] == "text"

        result = json.loads(content["text"])
        assert "success" in result

        if result["success"]:
            # Verify plugin processing result
            assert "plugin_used" in result
            assert "confidence" in result
            assert "enriched_metadata" in result
            assert "entities" in result
            assert "terminology" in result

            # Verify domain detection
            enriched = result["enriched_metadata"]
            assert "domain" in enriched
            assert enriched["domain"] in ["manufacturing", "packaging"]

    @pytest.mark.asyncio
    async def test_process_document_with_invalid_input(self, rag_server):
        """Test process_document with invalid input"""
        request = {
            "method": "tools/call",
            "params": {
                "name": "process_document",
                "arguments": {
                    "document": {}  # Empty document
                }
            }
        }

        response = await handle_request(rag_server, request)

        # Should handle gracefully
        assert "content" in response
        content = response["content"][0]
        result = json.loads(content["text"])

        # Either fails or has low confidence
        if result["success"]:
            assert result["confidence"] < 0.5
        else:
            assert "error" in result


class TestMCPLegacyProtocol:
    """Test legacy MCP protocol (direct method calls)"""

    @pytest.mark.asyncio
    async def test_legacy_health_check(self, rag_server):
        """Test legacy health_check method"""
        request = {
            "method": "health_check",
            "params": {}
        }

        response = await handle_request(rag_server, request)

        assert "status" in response
        assert response["status"] == "healthy"
        assert "server" in response
        assert "agent_health" in response

    @pytest.mark.asyncio
    async def test_legacy_get_status(self, rag_server):
        """Test legacy get_status method"""
        request = {
            "method": "get_status",
            "params": {}
        }

        response = await handle_request(rag_server, request)

        assert "success" in response
        assert response["success"] is True
        assert "status" in response
        assert "server_info" in response

    @pytest.mark.asyncio
    async def test_legacy_list_capabilities(self, rag_server):
        """Test legacy list_capabilities method"""
        request = {
            "method": "list_capabilities",
            "params": {}
        }

        response = await handle_request(rag_server, request)

        assert "success" in response
        assert response["success"] is True
        assert "capabilities" in response

        capabilities = response["capabilities"]
        assert isinstance(capabilities, dict)


class TestMCPErrorHandling:
    """Test MCP protocol error handling"""

    @pytest.mark.asyncio
    async def test_unknown_method(self, rag_server):
        """Test handling of unknown method"""
        request = {
            "method": "unknown_method_xyz",
            "params": {}
        }

        response = await handle_request(rag_server, request)

        assert "success" in response
        assert response["success"] is False
        assert "error" in response
        assert "Unknown method" in response["error"]

    @pytest.mark.asyncio
    async def test_unknown_tool(self, rag_server):
        """Test handling of unknown tool"""
        request = {
            "method": "tools/call",
            "params": {
                "name": "unknown_tool_xyz",
                "arguments": {}
            }
        }

        response = await handle_request(rag_server, request)

        assert "success" in response
        assert response["success"] is False
        assert "error" in response
        assert "Unknown tool" in response["error"]

    @pytest.mark.asyncio
    async def test_malformed_request(self, rag_server):
        """Test handling of malformed request"""
        # Missing method
        request = {
            "params": {}
        }

        response = await handle_request(rag_server, request)

        # Should handle gracefully
        # Exact response depends on implementation
        assert isinstance(response, dict)


class TestMCPPluginIntegration:
    """Test MCP protocol integration with plugin system"""

    @pytest.mark.asyncio
    async def test_end_to_end_mcp_plugin_flow(
        self, rag_server, sample_manufacturing_document
    ):
        """Test complete flow through MCP protocol"""

        # Step 1: List available tools
        list_request = {
            "method": "tools/list",
            "params": {}
        }
        list_response = await handle_request(rag_server, list_request)

        tool_names = [tool["name"] for tool in list_response["tools"]]
        assert "process_document" in tool_names

        # Step 2: Get plugin info
        info_request = {
            "method": "tools/call",
            "params": {
                "name": "get_plugin_info",
                "arguments": {}
            }
        }
        info_response = await handle_request(rag_server, info_request)
        info_result = json.loads(info_response["content"][0]["text"])

        assert info_result["success"] is True

        # Step 3: Process document
        process_request = {
            "method": "tools/call",
            "params": {
                "name": "process_document",
                "arguments": {
                    "document": sample_manufacturing_document
                }
            }
        }
        process_response = await handle_request(rag_server, process_request)
        process_result = json.loads(process_response["content"][0]["text"])

        # Verify complete flow worked
        assert process_result["success"] is True
        assert "enriched_metadata" in process_result
        assert process_result["enriched_metadata"]["domain"] == "manufacturing"

    @pytest.mark.asyncio
    async def test_concurrent_mcp_calls(self, rag_server):
        """Test handling concurrent MCP calls"""

        # Create multiple documents with substantial manufacturing content
        documents = [
            {
                "content": f"""
                Standard Operating Procedure: CNC Machining Process {i}

                Equipment: CNC Mill (Haas VF-{i+2})
                Material: Aluminum 6061-T6

                Process Parameters:
                - Spindle speed: {3000 + i*500} RPM
                - Feed rate: {500 + i*50} mm/min
                - Depth of cut: {2 + i*0.5}mm per pass
                - Coolant: Water-soluble

                Quality Control:
                - CMM inspection for critical dimensions
                - Surface roughness: Ra < 1.6 μm
                - Tolerances: ±0.05mm
                """,
                "filename": f"doc_{i}.pdf"
            }
            for i in range(3)
        ]

        # Process documents concurrently
        requests = [
            {
                "method": "tools/call",
                "params": {
                    "name": "process_document",
                    "arguments": {"document": doc}
                }
            }
            for doc in documents
        ]

        # Execute concurrently
        responses = await asyncio.gather(*[
            handle_request(rag_server, req)
            for req in requests
        ])

        # Verify all succeeded
        assert len(responses) == 3
        for i, response in enumerate(responses):
            assert "content" in response
            result = json.loads(response["content"][0]["text"])
            if not result["success"]:
                print(f"Response {i} failed: {result}")
            assert result["success"] is True


class TestMCPServerCapabilities:
    """Test MCP server capabilities reporting"""

    @pytest.mark.asyncio
    async def test_server_capabilities_include_plugins(self, rag_server):
        """Test that server capabilities include plugin features"""
        request = {
            "method": "get_status",
            "params": {}
        }

        response = await handle_request(rag_server, request)

        assert "server_info" in response
        server_info = response["server_info"]

        assert "capabilities" in server_info
        capabilities = server_info["capabilities"]

        # Verify plugin capabilities are listed
        expected_plugin_capabilities = [
            "domain_document_processing",
            "plugin_enhanced_rag"
        ]

        for cap in expected_plugin_capabilities:
            assert cap in capabilities, f"Missing capability: {cap}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
