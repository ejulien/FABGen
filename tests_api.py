# common test API


def expect_eq(a, b):
	if a != b:
		raise ValueError('expect_eq: %s!=%s' % (repr(a), repr(b)))
