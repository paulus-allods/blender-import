from struct import error, pack, unpack
import zlib
import io

class Blob:

    def __init__(self, localId, size):
        self.localId = localId
        self.size = size

class BinParser:

    def __init__(self, path):
        self.path = path
        self._blobs = []
        self._read_blobs()

    def _read_blobs(self):
        content = io.BytesIO(zlib.decompress(open(self.path, 'rb').read()))
        while True:
            try:
                localId, size = unpack('II',content.read(8))
                assert localId == len(self._blobs)
                value = content.read(size)
                self._blobs.append(value)
            except error:
                break
        content.close()

    def get_buffer(self, blob):
        assert(len(self._blobs[blob.localId]) == blob.size)
        return self._blobs[blob.localId]
