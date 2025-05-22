import pytest
from spill3r import spill3r
import json


def test_listable_known_bucket(monkeypatch):
    def mock_get(url, timeout):
        class MockResponse:
            status_code = 200
            text = "<ListBucketResult>"

        return MockResponse()

    monkeypatch.setattr("requests.get", mock_get)
    assert spill3r.check_bucket_listable("dummy-bucket") is True


def test_not_listable_bucket(monkeypatch):
    def mock_get(url, timeout):
        class MockResponse:
            status_code = 403
            text = "AccessDenied"

        return MockResponse()

    monkeypatch.setattr("requests.get", mock_get)
    assert spill3r.check_bucket_listable("dummy-bucket") is False


def test_writeable_bucket(monkeypatch):
    def mock_put(url, headers, data, timeout):
        class MockResponse:
            status_code = 200

        return MockResponse()

    monkeypatch.setattr("requests.put", mock_put)
    assert spill3r.check_bucket_writeable("dummy-bucket", cleanup=False, dry_run=False) is True


def test_dry_run_writeable():
    assert spill3r.check_bucket_writeable("any-bucket", dry_run=True) is True


def test_writeable_cleanup(monkeypatch):
    def mock_put(url, headers, data, timeout):
        class MockResponse:
            status_code = 201

        return MockResponse()

    def mock_delete(url, timeout):
        class MockResponse:
            status_code = 204

        return MockResponse()

    monkeypatch.setattr("requests.put", mock_put)
    monkeypatch.setattr("requests.delete", mock_delete)
    assert spill3r.check_bucket_writeable("dummy-bucket", cleanup=True, dry_run=False) is True


def test_output_log_format():
    # Simulate a result logging
    spill3r.scan_results.clear()
    spill3r.log_result("example-bucket", listable=True, writeable=False, dry_run=False)

    assert len(spill3r.scan_results) == 1
    result = spill3r.scan_results[0]
    assert result["bucket"] == "example-bucket"
    assert result["listable"] is True
    assert result["writeable"] is False
    assert result["dry_run"] is False
    assert "timestamp" in result

    # Check if it dumps to JSON cleanly
    json_string = json.dumps(spill3r.scan_results, indent=2)
    assert isinstance(json_string, str)
    assert "example-bucket" in json_string
