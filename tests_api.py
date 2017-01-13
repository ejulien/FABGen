# common test API


def expect_eq(a, b):
	if a != b:
		raise ValueError('expect_eq: %s!=%b' % (repr(a), repr(b)))
