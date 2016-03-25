# the equivalent of a circular size limited list
# also known as ring buffer, pops the oldest data item
# to make room for newest data item when max size is reached
# uses the double ended queue available in Python24
 
from collections import deque
 
class RingBuffer(deque):
	"""
	inherits deque, pops the oldest data to make room
	for the newest data when size is reached
	"""
	def __init__(self, size):
		deque.__init__(self)
		self.size = size
		
	def full_append(self, item):
		deque.append(self, item)
		# full, pop the oldest item, left most item
		self.popleft()
		
	def append(self, item):
		deque.append(self, item)
		# max size reached, append becomes full_append
		if len(self) == self.size:
			self.append = self.full_append
	
	def get(self):
		"""returns a list of size items (newest items)"""
		return list(self)
	
# testing
if __name__ == '__main__':
	size = 5
	ring = RingBuffer(size)
	for x in range(9):
		ring.append(x)
		print ring.get()  # test
 
"""
notice that the left most item is popped to make room
result =
[0]
[0, 1]
[0, 1, 2]
[0, 1, 2, 3]
[0, 1, 2, 3, 4]
[1, 2, 3, 4, 5]
[2, 3, 4, 5, 6]
[3, 4, 5, 6, 7]
[4, 5, 6, 7, 8]
"""