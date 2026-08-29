from security import BoundaryChecker

def test_within_bounds():
    checker = BoundaryChecker(0, 100)
    assert checker.check(50) is True

def test_lower_bound():
    checker = BoundaryChecker(0, 100)
    assert checker.check(0) is True

def test_upper_bound_inclusive():
    checker = BoundaryChecker(0, 100)
    # Oracle assertion: 100 should be accepted (will fail on initial buggy code to verify early stopping)
    assert checker.check(100) is True

def test_out_of_bounds():
    checker = BoundaryChecker(0, 100)
    assert checker.check(-1) is False
    assert checker.check(101) is False
