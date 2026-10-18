"""Fragmentos HTTP locales para reproducir un recorte en su rejilla nativa."""
import io
import re
from .acquisition import AcquisitionError
from .common import digest


class RangeFile(io.RawIOBase):
    block_size = 1024**2

    def __init__(self, client, url, name, offline=False):
        super().__init__()
        self.client, self.url, self.name, self.offline = client, url, name, offline
        self.position, self.size, self.version = 0, None, None
        self._block(0)

    def _block(self, number):
        name = f'{self.name}.range-{number}.bin'
        start = number*self.block_size
        stop = start+self.block_size-1
        if self.size is not None:
            stop = min(stop, self.size-1)
        record = self.client.state['files'].get(name)
        if self.offline and not record:
            raise AcquisitionError('Fragmento no disponible localmente')
        if self.offline:
            local = self.client.folder / name
            if not local.is_file() or digest(local) != record['sha256']:
                raise AcquisitionError('Fragmento local alterado; no consultar red')
        path = self.client.fetch(self.url, name, kind='fragment', headers={'Range': f'bytes={start}-{stop}'}, expected_range=(start, stop))
        record = self.client.state['files'][name]
        match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', record.get('content_range') or '')
        if not match:
            raise AcquisitionError('Fragmento sin identidad de rango')
        left, right, size = map(int, match.groups())
        version = record.get('etag') or record.get('last_modified')
        if not version:
            raise AcquisitionError('Fuente remota sin versión HTTP comprobable')
        if self.size is not None and (size != self.size or version != self.version):
            raise AcquisitionError('La versión remota cambió entre fragmentos')
        self.size, self.version = size, version
        data = path.read_bytes()
        if left != start or len(data) != right-left+1:
            raise AcquisitionError('Longitud/posición del fragmento incompatible')
        return data

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        position = offset if whence == 0 else self.position+offset if whence == 1 else self.size+offset
        if position < 0:
            raise ValueError('Posición negativa')
        self.position = position
        return position

    def read(self, size=-1):
        if size < 0 or size > 16*1024**2:
            raise AcquisitionError('Lectura completa/grande del mosaico no admitida')
        size = min(size, max(0, self.size-self.position))
        parts = []
        while size:
            number, offset = divmod(self.position, self.block_size)
            data = self._block(number)
            part = data[offset:offset+size]
            if not part:
                raise AcquisitionError('Fragmento incompleto')
            parts.append(part)
            self.position += len(part)
            size -= len(part)
        return b''.join(parts)
