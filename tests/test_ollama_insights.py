import unittest
from unittest.mock import patch, MagicMock
from src.ollama_insights import (
    generate_insights,
    generate_executive_summary,
    _build_campaign_summary,
    check_ollama_available,
)

class TestBuildCampaignSummary(unittest.TestCase):
    def test_basic_summary(self):
        campaigns = [{'name': 'Test', 'impressions': 1000, 'clicks': 50, 'cost_usd': 100}]
        result = _build_campaign_summary(campaigns)
        self.assertIn('1,000', result)
        self.assertIn('Test', result)

    def test_empty_campaigns(self):
        result = _build_campaign_summary([])
        self.assertIn('0 campaigns', result)

class TestCheckOllamaAvailable(unittest.TestCase):
    @patch('src.ollama_insights.requests.get')
    def test_ollama_not_running(self, mock_get):
        mock_get.side_effect = Exception('Connection refused')
        ok, models = check_ollama_available()
        self.assertFalse(ok)
        self.assertEqual(models, [])

    @patch('src.ollama_insights.requests.get')
    def test_ollama_running(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'models': [{'name': 'llama3.1'}]}
        mock_get.return_value = mock_resp
        ok, models = check_ollama_available()
        self.assertTrue(ok)
        self.assertIn('llama3.1', models)

class TestGenerateInsights(unittest.TestCase):
    @patch('src.ollama_insights._try_ollama')
    @patch('src.ollama_insights._try_anthropic')
    @patch('src.ollama_insights._try_openai')
    def test_all_providers_fail(self, mock_openai, mock_anthropic, mock_ollama):
        mock_ollama.return_value = None
        mock_anthropic.return_value = None
        mock_openai.return_value = None
        result = generate_insights([{'name': 'Test', 'impressions': 100}])
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()
