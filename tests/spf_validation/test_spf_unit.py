import pytest
import asyncio
from email.message import EmailMessage
from unittest.mock import patch, MagicMock, AsyncMock
from your_spf_script import check_spf, SPFStatus, extract_email

@pytest.fixture
def valid_email():
    msg = EmailMessage()
    msg['From'] = "test@gmail.com"
    msg['Received'] = "from mail.example.com ([192.168.1.100])"
    return msg

@pytest.mark.asyncio
async def test_valid_spf():
    msg = EmailMessage()
    msg['From'] = "test@gmail.com"
    msg['Received'] = "from mail.example.com ([192.168.1.100])"
    
    # Mock the DNS and SPF check
    with patch('dns.resolver.resolve') as mock_dns, \
         patch('spf.check2') as mock_spf:
        
        # Mock DNS response
        mock_txt = MagicMock()
        mock_txt.to_text.return_value = '"v=spf1 include:_spf.google.com ~all"'
        mock_dns.return_value = [mock_txt]
        
        # Mock SPF result
        mock_spf.return_value = ('pass', 'explanation')
        
        result = await check_spf(msg)
        assert result == SPFStatus.VALID

@pytest.mark.asyncio
async def test_invalid_spf():
    # Similar to above but with 'fail' result
    pass

@pytest.mark.asyncio
async def test_no_ip():
    msg = EmailMessage()
    msg['From'] = "test@gmail.com"
    # No Received header with IP
    
    result = await check_spf(msg)
    assert result == SPFStatus.NO_IP

def test_extract_email():
    assert extract_email("John <john@example.com>") == "john@example.com"
    assert extract_email("simple@example.com") == "simple@example.com"