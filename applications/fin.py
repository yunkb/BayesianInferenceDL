import matplotlib
matplotlib.use('macosx')
import matplotlib.pyplot as plt
from dolfin import *
import mshr
import numpy as np
from forward_solve import forward 
from error_optimization import optimize
from model_constr_adaptive_sampling import sample

# Create a fin geometry
geometry = mshr.Rectangle(Point(2.5, 0.0), Point(3.5, 4.0)) \
        + mshr.Rectangle(Point(0.0, 0.75), Point(2.5, 1.0)) \
        + mshr.Rectangle(Point(0.0, 1.75), Point(2.5, 2.0)) \
        + mshr.Rectangle(Point(0.0, 2.75), Point(2.5, 3.0)) \
        + mshr.Rectangle(Point(0.0, 3.75), Point(2.5, 4.0)) \
        + mshr.Rectangle(Point(3.5, 0.75), Point(6.0, 1.0)) \
        + mshr.Rectangle(Point(3.5, 1.75), Point(6.0, 2.0)) \
        + mshr.Rectangle(Point(3.5, 2.75), Point(6.0, 3.0)) \
        + mshr.Rectangle(Point(3.5, 3.75), Point(6.0, 4.0)) \

mesh = mshr.generate_mesh(geometry, 40)

V = FunctionSpace(mesh, 'CG', 1)
dofs = len(V.dofmap().dofs())

##########################################################3
# Basis initialization with dummy solves and POD
##########################################################3
samples = 5
Y = np.zeros((samples, dofs))
for i in range(0,samples):

    if i%2 == 0:
        m = interpolate(Expression("0.1 +s*exp(-(pow(x[0] - c_x, 2) + pow(x[1]-c, 2)) / 0.02)", degree=2, s=2.0, c=0.03*i, c_x =0.5 + 0.01*i), V)
    else:
        m = interpolate(Expression("c*x[0] + 0.1", degree=2, c=2.0*i), V)

    w = forward(m, V)[0]
    Y[i,:] = w.vector()[:]

K = np.dot(Y, Y.T)
e,v = np.linalg.eig(K)

U = np.zeros((2, dofs))
for i in range(2):
    e_i = v[:,i].real
    U[i,:] = np.sum(np.dot(np.diag(e_i), Y),0)

basis = U.T
z_0 = Function(V)
z_0.vector().set_local(np.random.uniform(0.1, 10, dofs))
basis = sample(basis, z_0, optimize, forward, V)

print("Computer basis with shape {}".format(basis.shape))
