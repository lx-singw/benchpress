class BoundaryChecker:
    def __init__(self, min_val: int, max_val: int):
        self.min_val = min_val
        self.max_val = max_val

    def check(self, value: int) -> bool:
        # Deliberate bug in base code: uses > instead of >= for upper bound
        return self.min_val <= value < self.max_val
