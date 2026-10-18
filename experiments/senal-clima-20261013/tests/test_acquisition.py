import hashlib
import pytest
from signalclima.acquisition import Client, AcquisitionError
from signalclima.common import ROOT


class Response:
    def __init__(self, chunks, size, kind='application/octet-stream'):
        self.chunks = chunks
        self.status_code = 200
        self.headers = {'Content-Length': str(size), 'Content-Type': kind}
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def raise_for_status(self): pass
    def iter_content(self, size): yield from self.chunks


class Session:
    def __init__(self, response): self.response, self.calls = response, 0
    def get(self, *args, **kwargs):
        self.calls += 1
        return self.response


def client(tmp_path, monkeypatch, response, **kwargs):
    import signalclima.common as common
    monkeypatch.setattr(common, 'ROOT', tmp_path)
    return Client(tmp_path / 'access', Session(response), **kwargs)


def test_truncated_and_html_are_not_published(tmp_path, monkeypatch):
    c = client(tmp_path, monkeypatch, Response([b'abc'], 10), attempts=1)
    with pytest.raises(AcquisitionError, match='truncada'): c.fetch('https://example.org/a', 'a.bin')
    assert not (c.folder / 'a.bin').exists()
    c.session = Session(Response([b'<html>bad</html>'], 16, 'text/html'))
    with pytest.raises(AcquisitionError): c.fetch('https://example.org/a', 'a.tif', 'raster')
    assert not (c.folder / 'a.tif').exists()
    assert c.state['events'][-1]['status'] == 'rejected'


def test_cached_file_checked_and_budget_enforced(tmp_path, monkeypatch):
    c = client(tmp_path, monkeypatch, Response([b'abc'], 3), max_bytes=3)
    p = c.fetch('https://example.org/a', 'a.bin', expected_sha256=hashlib.sha256(b'abc').hexdigest())
    assert c.fetch('https://example.org/a', 'a.bin') == p and c.session.calls == 1
    with pytest.raises(AcquisitionError, match='agotado'): c.fetch('https://example.org/b', 'b.bin')
    p.write_bytes(b'changed')
    with pytest.raises(AcquisitionError, match='íntegra'): c.fetch('https://example.org/a', 'a.bin')


def test_timeout_budget_before_request(tmp_path, monkeypatch):
    c = client(tmp_path, monkeypatch, Response([b'a'], 1), max_seconds=0)
    with pytest.raises(AcquisitionError, match='agotado'): c.fetch('https://example.org/a', 'a.bin')
    assert c.session.calls == 0
