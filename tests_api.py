# common test API


def expect_eq(a, b):
	if a != b:
		raise ValueError('expect_eq: %s!=%s' % (repr(a), repr(b)))

def expect_neq(a, b):
	if a == b:
		raise ValueError('expect_neq: %s==%s' % (repr(a), repr(b)))
