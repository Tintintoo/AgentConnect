# Cross-Platform Identity Authentication and End-to-End Encrypted Communication Technology Based on DID
# Author: GaoWei Chang
# Email: chgaowei@gmail.com
# Website: http://pi-unlimited.com
#
# This project is open-sourced under the MIT License. For details, please see the LICENSE file.

import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json
import logging

from agent_connect.meta_protocol.protocol_negotiator import (
    ProtocolNegotiator,
    NegotiationStatus,
    NegotiationResult,
    NegotiatorRole
)
from agent_connect.utils.llm.base_llm import BaseLLM

class TestProtocolNegotiator(unittest.TestCase):
    def setUp(self):
        # Mock LLM client
        self.mock_llm = MagicMock(spec=BaseLLM)
        self.mock_llm.model_name = "gpt-4-turbo-preview"
        self.mock_llm.client = MagicMock()
        
        # Mock capability info callback
        self.mock_capability_callback = AsyncMock()
        
        # Create negotiator instance
        self.negotiator = ProtocolNegotiator(
            llm=self.mock_llm,
            get_capability_info_callback=self.mock_capability_callback
        )

        # Test data
        self.test_requirement = "Create a protocol for user authentication"
        self.test_input = "Username and password in JSON format"
        self.test_output = "Authentication token in JSON format"
        
        # Sample protocol content
        self.sample_protocol = """
# Requirements
User authentication protocol with username/password

# Protocol Flow
1. Client sends credentials
2. Server validates and returns token

# Data Format
## Request Format
{
    "username": "string",
    "password": "string"
}

## Response Format
{
    "token": "string",
    "expires_in": "number"
}

# Error Handling
Standard HTTP status codes
"""

    async def test_generate_initial_protocol(self):
        """Test initial protocol generation"""
        # Mock LLM response
        self.mock_llm.async_generate_response = AsyncMock(
            return_value=self.sample_protocol
        )
        
        # Generate initial protocol
        protocol, status, round_num = await self.negotiator.generate_initial_protocol(
            self.test_requirement,
            self.test_input,
            self.test_output
        )
        
        # Verify results
        self.assertEqual(status, NegotiationStatus.NEGOTIATING)
        self.assertEqual(round_num, 1)
        self.assertEqual(protocol, self.sample_protocol)
        self.assertEqual(self.negotiator.role, NegotiatorRole.REQUESTER)
        
        # Verify negotiation history
        self.assertEqual(len(self.negotiator.negotiation_history), 1)
        self.assertEqual(
            self.negotiator.negotiation_history[0]["candidate_protocols"],
            self.sample_protocol
        )

    async def test_evaluate_as_provider(self):
        """Test protocol evaluation as provider"""
        # Setup initial state
        self.negotiator.role = NegotiatorRole.PROVIDER
        self.negotiator.negotiation_round = 1
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "status": "negotiating",
                        "candidate_protocol": self.sample_protocol,
                        "modification_summary": "Added error handling details"
                    })
                )
            )
        ]
        self.mock_llm.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        
        # Evaluate protocol
        result = await self.negotiator.evaluate_protocol_proposal(
            NegotiationResult(
                status=NegotiationStatus.NEGOTIATING,
                candidate_protocol="",
                modification_summary=""
            ),
            self.sample_protocol
        )
        
        # Verify results
        self.assertEqual(result.status, NegotiationStatus.NEGOTIATING)
        self.assertEqual(result.candidate_protocol, self.sample_protocol)
        self.assertEqual(result.modification_summary, "Added error handling details")
        self.assertEqual(self.negotiator.negotiation_round, 2)

    async def test_evaluate_as_requester(self):
        """Test protocol evaluation as requester"""
        # Setup initial state
        self.negotiator.role = NegotiatorRole.REQUESTER
        self.negotiator.requirement = self.test_requirement
        self.negotiator.input_description = self.test_input
        self.negotiator.output_description = self.test_output
        self.negotiator.negotiation_round = 1
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "status": "accepted",
                        "candidate_protocol": "",
                        "modification_summary": "Protocol accepted"
                    })
                )
            )
        ]
        self.mock_llm.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        
        # Evaluate protocol
        result = await self.negotiator.evaluate_protocol_proposal(
            NegotiationResult(
                status=NegotiationStatus.NEGOTIATING,
                candidate_protocol="",
                modification_summary=""
            ),
            self.sample_protocol
        )
        
        # Verify results
        self.assertEqual(result.status, NegotiationStatus.ACCEPTED)
        self.assertEqual(result.modification_summary, "Protocol accepted")
        self.assertEqual(self.negotiator.negotiation_round, 2)

    async def test_get_capability_info(self):
        """Test capability info retrieval"""
        # Mock callback response
        self.mock_capability_callback.return_value = "System can handle the requirements"
        
        # Get capability info
        result = await self.negotiator.get_capability_info(
            self.test_requirement,
            self.test_input,
            self.test_output
        )
        
        # Verify results
        self.assertEqual(result, "System can handle the requirements")
        self.mock_capability_callback.assert_called_once_with(
            self.test_requirement,
            self.test_input,
            self.test_output
        )

def run_async_test(coro):
    """Helper function to run async tests"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    # Run tests
    unittest.main() 