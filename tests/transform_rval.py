import lib


def bind_test(gen):
	gen.start('my_test')

	lib.bind_defaults(gen)

	# inject test code in the wrapper
	gen.add_include('memory', True)
	gen.add_include('string', True)

	gen.insert_binding_code('''\
struct A {
	virtual std::string GetType() const = 0;
	int GetBaseValue() const { return 12; }
};

struct B : A {
	std::string GetType() const override { return "B"; }
	int b{3};
};

struct C : A {
	std::string GetType() const override { return "C"; }
	int c{7};
};

static std::unique_ptr<A> b(new B);
static std::unique_ptr<A> c(new C);

A *get_b() { return b.get(); }
A *get_c() { return c.get(); }
''')

	def A_rval_transform(gen, conv, expr, var_out, ownership):
		src = 'if ((%s)->GetType() == "C")\n' % expr
		src += gen.rval_from_c_ptr(gen.get_conv('C'), var_out, '((C*)%s)' % expr, ownership)
		src += 'else if ((%s)->GetType() == "B")\n' % expr
		src += gen.rval_from_c_ptr(gen.get_conv('B'), var_out, '((B*)%s)' % expr, ownership)
		src += 'else\n'
		src += gen.rval_from_c_ptr(conv, var_out, expr, ownership)
		return src

	A = gen.begin_class('A', noncopyable=True)
	A.add_feature('rval_transform', A_rval_transform)
	gen.bind_method(A, 'GetType', 'std::string', [])
	gen.bind_method(A, 'GetBaseValue', 'int', [])
	gen.end_class(A)

	B = gen.begin_class('B')
	gen.add_base(B, A)
	gen.bind_member(B, 'int b')
	gen.end_class(B)

	C = gen.begin_class('C')
	gen.add_base(C, A)
	gen.bind_member(C, 'int c')
	gen.end_class(C)

	gen.bind_function('get_b', 'A *', [], {})
	gen.bind_function('get_c', 'A *', [], {})

	gen.finalize()
	return gen.get_output()


test_python = '''\
import my_test

B = my_test.get_b()
assert B.b == 3
assert B.GetBaseValue() == 12

C = my_test.get_c()
assert C.c == 7
assert C.GetBaseValue() == 12
'''

test_lua = '''\
my_test = require "my_test"

B = my_test.get_b()
assert(B.b == 3)
assert(B:GetBaseValue() == 12)

C = my_test.get_c()
assert(C.c == 7)
assert(C:GetBaseValue() == 12)
'''

test_go = '''\
package mytest

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// Test ...
func Test(t *testing.T) {
	B := GetB()
	assert.Equal(t, CastAToB(B).GetB(), int32(3), "should be the same.")
	assert.Equal(t, B.GetBaseValue(), int32(12), "should be the same.")

	C := GetC()
	assert.Equal(t, CastAToC(C).GetC(), int32(7), "should be the same.")
	assert.Equal(t, C.GetBaseValue(), int32(12), "should be the same.")
}
'''