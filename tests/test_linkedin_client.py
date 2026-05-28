"""Unit tests for src/linkedin_client.py"""

import unittest
from unittest.mock import patch, MagicMock

from src.linkedin_client import (
    LinkedInClient, INDUSTRY_V2, FIELDS_BATCH1, FIELDS_BATCH2,
    LinkedInAPIError, LinkedInAuthError, LinkedInRateLimitError,
)


class TestLinkedInClientInit(unittest.TestCase):
    """Tests for LinkedInClient.__init__()."""

    def test_init_sets_token(self):
        client = LinkedInClient(access_token='test_token', account_id='12345')
        self.assertEqual(client.access_token, 'test_token')

    def test_init_sets_account_id(self):
        client = LinkedInClient(access_token='test_token', account_id='12345')
        self.assertEqual(client.account_id, '12345')

    def test_rest_headers(self):
        client = LinkedInClient(access_token='my_token', account_id='999')
        headers = client._rest_headers
        self.assertEqual(headers['Authorization'], 'Bearer my_token')
        self.assertIn('LinkedIn-Version', headers)
        self.assertIn('X-Restli-Protocol-Version', headers)

    def test_v2_headers(self):
        client = LinkedInClient(access_token='my_token', account_id='999')
        headers = client._v2_headers
        self.assertEqual(headers['Authorization'], 'Bearer my_token')
        self.assertNotIn('LinkedIn-Version', headers)
        self.assertIn('X-Restli-Protocol-Version', headers)

    def test_rate_limit_delay_default(self):
        client = LinkedInClient(access_token='t', account_id='1')
        self.assertEqual(client.rate_limit_delay, 0.2)

    def test_max_retries_default(self):
        client = LinkedInClient(access_token='t', account_id='1')
        self.assertEqual(client.max_retries, 2)

    def test_custom_rate_limit_delay(self):
        client = LinkedInClient(access_token='t', account_id='1', rate_limit_delay=0.5)
        self.assertEqual(client.rate_limit_delay, 0.5)

    def test_request_count_starts_zero(self):
        client = LinkedInClient(access_token='t', account_id='1')
        self.assertEqual(client._request_count, 0)


class TestIndustryV2Map(unittest.TestCase):
    """Tests for the INDUSTRY_V2 constant."""

    def test_has_entries(self):
        self.assertGreater(len(INDUSTRY_V2), 0)

    def test_keys_are_strings(self):
        for key in list(INDUSTRY_V2.keys())[:10]:
            self.assertIsInstance(key, str)

    def test_values_are_strings(self):
        for val in list(INDUSTRY_V2.values())[:10]:
            self.assertIsInstance(val, str)

    def test_specific_entry(self):
        self.assertIn("150", INDUSTRY_V2)
        self.assertEqual(INDUSTRY_V2["150"], "Horticulture")


class TestFieldConstants(unittest.TestCase):
    """Tests for FIELDS_BATCH1 and FIELDS_BATCH2."""

    def test_batch1_is_string(self):
        self.assertIsInstance(FIELDS_BATCH1, str)

    def test_batch2_is_string(self):
        self.assertIsInstance(FIELDS_BATCH2, str)

    def test_batch1_has_impressions(self):
        self.assertIn('impressions', FIELDS_BATCH1)

    def test_batch1_has_clicks(self):
        self.assertIn('clicks', FIELDS_BATCH1)

    def test_batch2_has_video_views(self):
        self.assertIn('videoViews', FIELDS_BATCH2)

    def test_batch1_comma_separated(self):
        fields = FIELDS_BATCH1.split(',')
        self.assertGreater(len(fields), 5)

    def test_batch2_comma_separated(self):
        fields = FIELDS_BATCH2.split(',')
        self.assertGreater(len(fields), 3)


class TestExceptionClasses(unittest.TestCase):
    """Tests for custom exception classes."""

    def test_api_error_is_exception(self):
        self.assertTrue(issubclass(LinkedInAPIError, Exception))

    def test_auth_error_is_api_error(self):
        self.assertTrue(issubclass(LinkedInAuthError, LinkedInAPIError))

    def test_rate_limit_error_is_api_error(self):
        self.assertTrue(issubclass(LinkedInRateLimitError, LinkedInAPIError))

    def test_auth_error_status_code(self):
        err = LinkedInAuthError()
        self.assertEqual(err.status_code, 401)

    def test_rate_limit_error_status_code(self):
        err = LinkedInRateLimitError()
        self.assertEqual(err.status_code, 429)

    def test_rate_limit_error_retry_after(self):
        err = LinkedInRateLimitError(retry_after=30)
        self.assertEqual(err.retry_after, 30)


class TestApiGet(unittest.TestCase):
    """Tests for LinkedInClient._api_get() with mocked requests."""

    def setUp(self):
        self.client = LinkedInClient(access_token='test', account_id='123', rate_limit_delay=0)

    @patch('src.linkedin_client.requests.get')
    def test_successful_request(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'elements': []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = self.client._api_get('https://api.linkedin.com/test', {})
        self.assertEqual(result, {'elements': []})

    @patch('src.linkedin_client.requests.get')
    def test_401_raises_auth_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        with self.assertRaises(LinkedInAuthError):
            self.client._api_get('https://api.linkedin.com/test', {}, retries=0)

    @patch('src.linkedin_client.requests.get')
    def test_429_raises_rate_limit_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.headers = {'Retry-After': '1'}
        mock_get.return_value = mock_resp

        with self.assertRaises(LinkedInRateLimitError):
            self.client._api_get('https://api.linkedin.com/test', {}, retries=0)

    @patch('src.linkedin_client.requests.get')
    def test_request_count_increments(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        self.assertEqual(self.client._request_count, 0)
        self.client._api_get('https://api.linkedin.com/test', {})
        self.assertEqual(self.client._request_count, 1)


class TestGetCampaignIds(unittest.TestCase):
    """Tests for LinkedInClient.get_campaign_ids()."""

    def setUp(self):
        self.client = LinkedInClient(access_token='test', account_id='123')

    def test_comma_separated_ids(self):
        result = self.client.get_campaign_ids('100,200,300')
        self.assertEqual(result, ['100', '200', '300'])

    def test_single_id(self):
        result = self.client.get_campaign_ids('12345')
        self.assertEqual(result, ['12345'])

    def test_strips_whitespace(self):
        result = self.client.get_campaign_ids(' 100 , 200 , 300 ')
        self.assertEqual(result, ['100', '200', '300'])

    @patch.object(LinkedInClient, 'list_campaigns')
    def test_all_keyword(self, mock_list):
        mock_list.return_value = [{'id': 1}, {'id': 2}]
        result = self.client.get_campaign_ids('all')
        self.assertEqual(result, ['1', '2'])
        mock_list.assert_called_once_with()

    @patch.object(LinkedInClient, 'list_campaigns')
    def test_active_keyword(self, mock_list):
        mock_list.return_value = [{'id': 10}]
        result = self.client.get_campaign_ids('active')
        self.assertEqual(result, ['10'])
        mock_list.assert_called_once_with(status_filter='ACTIVE')


if __name__ == '__main__':
    unittest.main()
