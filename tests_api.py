# common test API


def expect_eq(a, b):
	assert a == b, 'expect_eq: %s!=%s' % (repr(a), repr(b))

def expect_neq(a, b):
	assert a != b, 'expect_neq: %s==%s' % (repr(a), repr(b))
