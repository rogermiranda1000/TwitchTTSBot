import unittest
import asyncio
from buffer import Buffer
from single_buffer import SingleBuffer
from producer import Producer
from entries import BufferEntry,PrimitiveBufferEntry
from buffer_observer import BufferObserver

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
            first.enqueue(PrimitiveBufferEntry(None), sync=True)

        self.assertEqual(len(final._list), 1)
        self.assertEqual(len(almost_final._list), num_insertions-1)
        self.assertEqual(len(first._list), 0)

    def test_element_insertion(self):
        inserting = 'Hello World'

        buffer = Buffer()
        buffer.enqueue(PrimitiveBufferEntry(inserting), sync=True)

        self.assertEqual(len(buffer._list), 1)
        self.assertTrue(isinstance(buffer._list[0].element, str))
        self.assertEqual(buffer._list[0].element, inserting)

    def test_producer(self):
        """
        We'll add 10 elements, in a buffer-producer-producer distribution.
        We want to process until we loose 1 element, and 1 is being processed, so
        the final (expected) distribution will be: 7-1-1 (9 in total).

        In order to know when to stop we'll add an observer between producers;
        when it raises 2 ticks we'll know 1 element will be lost, and 1 being processed.
        """
        class SillyProducer(Producer):
            """
            A producer that forwards the input element after 3 seconds
            """
            def __init__(self, sleep_time: int, connection: Buffer = None):
                super().__init__(connection)
                self._sleep_time = sleep_time

            async def process(self, e: BufferEntry):
                print(str(e.element) + " - " + str(self))
                await asyncio.sleep(self._sleep_time)
                await self._done_processing(e)
        
        condition = asyncio.Condition()
        async def notify_condition(_):
            async with condition:
	            condition.notify()
        async def wait_for_condition():
            async with condition:
                await condition.wait() # wait for the lost element
                print("[v] First variable")
                await condition.wait() # wait for the second element
                print("[v] Second variable")
            await asyncio.sleep(0.1) # give some margin

        discard_buffer = SillyProducer(2) # this needs to be faster than the previous one (otherwhise we'll have to add a buffer in between)
        listen_for_discard_buffer_input = BufferObserver(notify_condition, connection=discard_buffer) # each element in `discard_buffer` will increment the counter
        first_producer = SillyProducer(3, connection=listen_for_discard_buffer_input)
        buffer = Buffer(connection=first_producer)

        print(str(discard_buffer))
        print(str(first_producer))

        num_insertions = 10
        for i in range(num_insertions):
            buffer.enqueue(PrimitiveBufferEntry(i))

        self._loop.run_until_complete(wait_for_condition())

        print(str([e.element for e in discard_buffer._list]))
        print(str([e.element for e in first_producer._list]))
        print(str([e.element for e in buffer._list]))

        self.assertEqual(len(discard_buffer._list), 1)
        self.assertEqual(discard_buffer._list[0].element, 1) # the second inserted element is expected to be processed in the last unit
        self.assertEqual(len(first_producer._list), 1)
        self.assertEqual(first_producer._list[0].element, 2) # the third inserted element is expected to be processed in the last unit
        self.assertEqual(len(buffer._list), 7)

if __name__ == '__main__':
    unittest.main()