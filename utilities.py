__version__ = "2.0.0"

import MyUtilities.common

#Utility Classes
class Utilities_Base(MyUtilities.common.Container, MyUtilities.common.EtcFunctions):
	def __init__(self, *args, **kwargs):
		"""Utility functions that everyone gets."""

		MyUtilities.common.Container.__init__(self, *args, **kwargs)

class Utilities_Container(Utilities_Base):
	def __init__(self, parent):
		"""Utility functions that only container classes get."""

		#Internal Variables
		if (not hasattr(self, "parent")): self.parent = parent
		if (not hasattr(self, "root")): self.root = self.parent
		
		#Initialize Inherited Modules
		Utilities_Base.__init__(self)

	def __str__(self):
		"""Gives diagnostic information on this when it is printed out."""

		output = Utilities_Base.__str__(self)
		if (len(self) > 0):
			output += f"-- Children: {len(self)}\n"
		return output

	def add(self, label = None):
		"""Adds a new child.
		If a child with the given label already exists, it will simply return the child instead of making a new one.

		Example Input: add()
		"""

		if (label in self):
			return self[label]
		return self.Child(self, label)

	def remove(self, child = None):
		"""Removes a child.

		child (str) - Which child to remove. Can be a children_class handle
			- If None: Will select the current child

		Example Input: remove()
		Example Input: remove(0)
		"""

		if (child is None):
			child = self.current
		elif (not isinstance(child, self.Child)):
			child = self[child]
		
		child.remove()

	def select(self, child = None):
		"""Selects a particular child.

		child (str) - Which child to select. Can be a children_class handle
			- If None: Will select the default child

		Example Input: select()
		Example Input: select(0)
		"""

		if (child is None):
			child = list(self)[0]
		elif (not isinstance(child, self.Child)):
			child = self[child]
		
		self.current = child

class Utilities_Child(Utilities_Base):
	def __init__(self, parent, label):
		"""Utility functions that only child classes get."""

		#Internal Variables
		if (not hasattr(self, "label")): self.label = label
		if (not hasattr(self, "parent")): self.parent = parent
		if (not hasattr(self, "root")): self.root = self.parent.root

		#Nest in parent
		if (self.label is None):
			self.label = 0
			while True:
				if (self.label not in self.parent):
					break
				self.label += 1
		self.parent[self.label] = self

		#Initialize Inherited Modules
		Utilities_Base.__init__(self)

	def __str__(self):
		"""Gives diagnostic information on this when it is printed out."""

		output = Utilities_Base.__str__(self)
		return output

	def rename(self, value):
		"""Renames this child to the new label.

		value (str) - The new label for this child

		Example Input: rename("Guest")
		"""

		del self.parent[self.label]
		
		self.label = value
		self.parent[value] = self

	def remove(self):
		"""Removes the rows in the database corresponding to this child.

		Example Input: remove()
		"""

		#Remove Child
		del self.parent[self.label]

		#Account for current selection
		if (self.parent.current == self):
			self.parent.select()

	def select(self):
		"""Selects this child.

		Example Input: select()
		"""

		self.parent.select(self)