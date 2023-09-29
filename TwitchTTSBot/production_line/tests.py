import unittest
import asyncio
from buffer import Buffer
from single_buffer import SingleBuffer
from producer import Producer
from entries import PrimitiveBufferEntry

class ProductionLineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._loop = asyncio.get_event_loop()

    def test_forward(self):
        """
        In this test we'll place some Buffers. By their definition,
        they should just forward all the elements to the right-most
        buffer.
        The last one will be able to only hold 1 element, so the
        final result should be 0-<added elements-1>-1
        """
        final = SingleBuffer()
        almost_final = Buffer(connection=final)
        first = Buffer(connection=almost_final)

        num_insertions = 5
        for _ in range(num_insertions):
            self._loop.run_until_complete(first.enqueue(PrimitiveBufferEntry(None)))

        self.assertEqual(len(final._list), 1)
        self.assertEqual(len(almost_final._list), num_insertions-1)
        self.assertEqual(len(first._list), 0)

    def test_element_insertion(self):
        inserting = 'Hello World'

        buffer = Buffer()
        self._loop.run_until_complete(buffer.enqueue(PrimitiveBufferEntry(inserting)))

        self.assertEqual(len(buffer._list), 1)
        self.assertTrue(isinstance(buffer._list[0].element, str))
        self.assertEqual(buffer._list[0].element, inserting)

if __name__ == '__main__':
    unittest.main()