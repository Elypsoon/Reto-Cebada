"""Adquisición explícita: límites persistentes y originales publicados tras validar."""
from pathlib import Path
import time
import requests
from .common import ROOT, safe, save, read, digest, now


class AcquisitionError(ValueError):
    pass


class Client:
    def __init__(self, folder=None, session=None, max_bytes=4 * 1024**3, max_seconds=2700, attempts=3):
        self.folder = safe(folder or ROOT / 'data/external/access')
        self.folder.mkdir(parents=True, exist_ok=True)
        self.receipt = self.folder / 'manifest.json'
        self.session = session or requests.Session()
        self.max_bytes, self.max_seconds, self.attempts = max_bytes, max_seconds, attempts
        self.state = read(self.receipt) if self.receipt.exists() else {'bytes': 0, 'seconds': 0., 'events': [], 'files': {}}
        self.state['limits'] = {'bytes': max_bytes, 'seconds': max_seconds, 'attempts_per_request': attempts}

    def remaining(self):
        if self.state['bytes'] >= self.max_bytes or self.state['seconds'] >= self.max_seconds:
            raise AcquisitionError('Presupuesto de adquisición agotado')

    def fetch(self, url, name, kind='metadata', expected_sha256=None, headers=None, validator=None, expected_range=None):
        if not url.startswith('https://'):
            raise AcquisitionError('Se requiere HTTPS')
        target = safe(self.folder / name)
        if target.parent != self.folder or target.suffix == '.partial':
            raise AcquisitionError('Nombre de descarga inválido')
        previous = self.state['files'].get(name)
        if previous and target.is_file() and digest(target) == previous['sha256']:
            if previous['url'] != url or (expected_sha256 and previous['sha256'] != expected_sha256):
                raise AcquisitionError('Caché incompatible con consulta/hash')
            if validator:
                validator(target)
            return target
        if target.exists():
            raise AcquisitionError('Archivo existente sin caché íntegra')
        if (ROOT/'registry/frozen-protocol.json').exists():
            raise AcquisitionError('Adquisición nueva prohibida después de congelar')
        last = None
        for attempt in range(self.attempts):
            self.remaining()
            started = time.perf_counter()
            event = {'url': url, 'name': name, 'kind': kind, 'attempt': attempt + 1, 'at': now(), 'bytes': 0}
            part = target.with_suffix(target.suffix + '.partial')
            try:
                request_headers = {'Accept-Encoding': 'identity', **(headers or {})}
                with self.session.get(url, stream=True, timeout=(15, min(90, max(1, self.max_seconds-self.state['seconds']))), headers=request_headers) as response:
                    event.update(status_code=response.status_code, content_type=response.headers.get('Content-Type'),
                                 last_modified=response.headers.get('Last-Modified'), etag=response.headers.get('ETag'),
                                 content_encoding=response.headers.get('Content-Encoding'), body_byte_basis='requests_decoded_body',
                                 content_range=response.headers.get('Content-Range'))
                    response.raise_for_status()
                    if expected_range is not None:
                        import re
                        match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', event['content_range'] or '')
                        if response.status_code != 206 or not match:
                            raise AcquisitionError('Servicio no respeta HTTP Range; no descargar el mosaico global')
                        left, right, total = map(int, match.groups())
                        if (left, right) != (expected_range[0], min(expected_range[1], total-1)):
                            raise AcquisitionError('Rango recibido incompatible')
                    size = response.headers.get('Content-Length')
                    if size and int(size) > self.max_bytes-self.state['bytes']:
                        raise AcquisitionError('Archivo excede presupuesto restante')
                    with part.open('wb') as f:
                        for chunk in response.iter_content(1024 * 256):
                            if not chunk:
                                continue
                            if time.perf_counter()-started+self.state['seconds'] >= self.max_seconds or self.state['bytes']+len(chunk) > self.max_bytes:
                                raise AcquisitionError('Presupuesto agotado durante descarga')
                            f.write(chunk)
                            event['bytes'] += len(chunk)
                            self.state['bytes'] += len(chunk)
                    encoded = response.headers.get('Content-Encoding', 'identity') not in ['', 'identity']
                    if size and not encoded and part.stat().st_size != int(size):
                        raise AcquisitionError('Descarga truncada')
                    event['content_length_verified'] = bool(size and not encoded)
                if not part.stat().st_size:
                    raise AcquisitionError('Respuesta vacía')
                if kind == 'raster':
                    start = part.open('rb').read(16)
                    if start.lstrip().startswith((b'<', b'{')) or 'text/html' in (event['content_type'] or ''):
                        raise AcquisitionError('Respuesta HTML/JSON en lugar de ráster')
                    import rasterio
                    with rasterio.open(part) as src:
                        if src.crs is None or src.nodata is None or src.count != 1:
                            raise AcquisitionError('Ráster sin CRS/NoData o banda única')
                if validator:
                    validator(part)
                sha = digest(part)
                if expected_sha256 and sha != expected_sha256:
                    raise AcquisitionError('Hash de descarga incompatible')
                part.replace(target)
                self.state['files'][name] = {'url': url, 'sha256': sha, 'bytes': event['bytes'], 'kind': kind,
                                             'at': now(), 'validated': True, 'etag': event['etag'],
                                             'last_modified': event['last_modified'], 'content_range': event['content_range']}
                event['status'] = 'downloaded'
                return target
            except (requests.RequestException, OSError, ValueError) as error:
                last = type(error).__name__ + ': ' + str(error).split('\n')[0][:180]
                event.update(status='rejected', error=last)
                if part.exists():
                    rejected = self.folder / f'{name}.rejected-{len(self.state["events"])}'
                    part.replace(rejected)
                    event['rejected_file'] = rejected.name
                # Authentication and deterministic data errors do not improve by retrying.
                if event.get('status_code') in [400, 401, 403, 404] or isinstance(error, AcquisitionError):
                    break
            finally:
                duration = time.perf_counter()-started
                event['seconds'] = duration
                self.state['seconds'] += duration
                self.state['events'].append(event)
                save(self.receipt, self.state)
            if attempt + 1 < self.attempts:
                delay = min(2**attempt, max(0, self.max_seconds-self.state['seconds']))
                time.sleep(delay)
                self.state['seconds'] += delay
                save(self.receipt, self.state)
        raise AcquisitionError(last or 'No se pudo recuperar la fuente')
