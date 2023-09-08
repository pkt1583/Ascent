class OperationRegistry:
    _instance = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if self._instance:
            raise TypeError("OperationRegistry should be accessed using the get_instance() method.")

        self.operations = []

    def add_operation(self, *operations):
        self.operations.extend(operations) if operations else None

    def get_operations(self):
        return self.operations
