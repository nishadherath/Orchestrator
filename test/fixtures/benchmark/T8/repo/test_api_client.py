"""Existing tests for api_client.py. All pass against this PR."""

from unittest.mock import patch, MagicMock

from api_client import cancel_order, create_order, get_order, list_orders


def _fake_response(status_code, json_body=None):
    resp = MagicMock(status_code=status_code)
    resp.json.return_value = json_body or {}
    return resp


def test_get_order_returns_response_on_first_success():
    fake = _fake_response(200, {"id": 42})
    with patch("requests.get", return_value=fake) as mock_get:
        result = get_order(42)
        assert result is fake
        mock_get.assert_called_once()


def test_list_orders_returns_response():
    fake = _fake_response(200, {"orders": []})
    with patch("requests.get", return_value=fake) as mock_get:
        result = list_orders(7)
        assert result is fake
        mock_get.assert_called_once()


def test_create_order_returns_response():
    fake = _fake_response(201, {"id": 99})
    with patch("requests.post", return_value=fake) as mock_post:
        result = create_order(7, [{"sku": "abc", "qty": 1}])
        assert result is fake
        mock_post.assert_called_once()


def test_cancel_order_returns_response():
    fake = _fake_response(204)
    with patch("requests.delete", return_value=fake) as mock_delete:
        result = cancel_order(42)
        assert result is fake
        mock_delete.assert_called_once()


def test_create_order_retries_on_server_error_then_succeeds():
    ok = _fake_response(201, {"id": 100})
    err = _fake_response(503)
    with patch("requests.post", side_effect=[err, err, ok]) as mock_post, \
         patch("time.sleep"):
        result = create_order(7, [{"sku": "abc", "qty": 1}])
        assert result is ok
        assert mock_post.call_count == 3
