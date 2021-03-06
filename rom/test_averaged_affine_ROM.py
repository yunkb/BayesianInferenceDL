from forward_solve import Fin
from thermal_fin import get_space
from averaged_affine_ROM import AffineROMFin
from gaussian_field import make_cov_chol
import dolfin as dl
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('macosx')
from dl_model import load_parametric_model_avg
from tensorflow.keras.optimizers import Adam, RMSprop, Adadelta


V = get_space(40)
model = load_parametric_model_avg('elu', Adam, 0.0003, 5, 58, 200, 2000, V.dim())
chol = make_cov_chol(V, length=1.6)
k_pt = dl.Function(V)
norm = np.random.randn(len(chol))
nodal_vals = np.exp(0.5 * chol.T @ norm)
k_pt.vector().set_local(nodal_vals)

solverROM = AffineROMFin(V)
w_A = solverROM.forward(k_pt)

solver = Fin(V)
w_F, y, A, B, C = solver.forward(k_pt)

p = dl.plot(w_A)
plt.colorbar(p)
plt.savefig('plots/avg_aff_rom_w_A.png')
plt.clf()

p = dl.plot(w_F)
plt.colorbar(p)
plt.savefig('plots/avg_aff_rom_w_F.png')
plt.clf()

avg_fom_err = np.sqrt(np.mean(np.square(w_A.vector()[:] - w_F.vector()[:])))
print("RMSE of Averaging FOM: {}".format(avg_fom_err))

phi = np.loadtxt('data/basis_five_param.txt',delimiter=",")
solverROM.set_reduced_basis(phi)

w_R = solverROM.forward_reduced(k_pt)
w_R_func = dl.Function(V)
w_R_func.vector().set_local(np.dot(phi,w_R))

p = dl.plot(w_R_func)
plt.colorbar(p)
plt.savefig('plots/avg_aff_rom_w_R.png')
plt.clf()

avg_rom_err = np.sqrt(np.mean(np.square(w_R_func.vector()[:] - w_F.vector()[:])))
print("RMSE of Averaging ROM: {}".format(avg_rom_err))

qoi_F = solver.qoi_operator(w_F)
qoi_A = solverROM.qoi(w_A)
qoi_R = solverROM.qoi_reduced(w_R)

print("qoi_F: {}".format(qoi_F))
print("qoi_A: {}".format(qoi_A))
print("qoi_R: {}".format(qoi_R))

k_true = dl.Function(V)
norm = np.random.randn(len(chol))
nodal_vals = np.exp(0.5 * chol.T @ norm)
k_true.vector().set_local(nodal_vals)
w = solverROM.forward(k_true)
data = solverROM.qoi(w)
solverROM.set_data(data)
solverROM.set_dl_model(model)

grad = solverROM.grad(k_pt)

qoi_0 = solverROM.qoi(w_A)
Pi_0 = np.square(qoi_0 - data).sum()/2

# Number of successive finite difference epsilons
n_eps = 15
eps = 1e-2*np.power(2., -np.arange(n_eps))
err_grad = np.zeros(n_eps)

k = dl.Function(V)

# Compute FOM adjoint method based gradient
k_hat = dl.Function(V).vector()
k_hat.set_local(np.random.randn(V.dim()))
k_hat.apply("")
dir_grad = np.dot(grad, k_hat[:])

for i in range(n_eps):
    k.assign(k_pt)
    k.vector().axpy(eps[i], k_hat) #uh = uh + eps[i]*dir

    w = solverROM.forward(k)
    qoi_plus = solverROM.qoi(w)
    Pi_plus = np.square(qoi_plus - data).sum()/2

    # Error b/w finite diff approx to gradient at given eps and adj
    err_grad[i] = abs( (Pi_plus - Pi_0)/eps[i] - dir_grad )

plt.loglog(eps, err_grad, "-ob", label="Error Grad")
plt.loglog(eps, (.5*err_grad[0]/eps[0])*eps, "-.k", label="First Order")
plt.title("Finite difference check of the first variation FOM")
plt.xlabel("eps")
plt.ylabel("Error grad")
plt.legend(loc = "upper left")
plt.savefig("plots/fom_grad_check.png", dpi=200)
plt.clf()

grad_r = solverROM.grad_reduced(k_pt)

w_R = solverROM.forward_reduced(k_pt)
qoi_0 = solverROM.qoi_reduced(w_R)
Pi_0 = np.square(qoi_0 - data).sum()/2

# Number of successive finite difference epsilons
n_eps = 15
eps = 1e-2*np.power(2., -np.arange(n_eps))
err_grad = np.zeros(n_eps)

k = dl.Function(V)

# Compute FOM adjoint method based gradient
k_hat = dl.Function(V).vector()
k_hat.set_local(np.random.randn(V.dim()))
k_hat.apply("")
dir_grad = np.dot(grad_r, k_hat[:])

for i in range(n_eps):
    k.assign(k_pt)
    k.vector().axpy(eps[i], k_hat) #uh = uh + eps[i]*dir

    w_R = solverROM.forward_reduced(k)
    qoi_plus = solverROM.qoi_reduced(w_R)
    Pi_plus = np.square(qoi_plus - data).sum()/2

    # Error b/w finite diff approx to gradient at given eps and adj
    fd_grad = (Pi_plus - Pi_0)/eps[i]
    err_grad[i] = abs(fd_grad - dir_grad)

plt.loglog(eps, err_grad, "-ob", label="Error Grad")
plt.loglog(eps, (.5*err_grad[0]/eps[0])*eps, "-.k", label="First Order")
plt.title("Finite difference check of the first variation ROM")
plt.xlabel("eps")
plt.ylabel("Error grad")
plt.legend(loc = "upper left")
plt.savefig("plots/rom_grad_check.png", dpi=200)
plt.clf()

grad_t = solverROM.grad_romml(k_pt)


w_R = solverROM.forward_reduced(k_pt)
qoi_0 = solverROM.qoi_reduced(w_R)
e_NN = model.predict([[k_pt.vector()[:]]])[0]

Pi_0 = np.square(qoi_0 + e_NN - data).sum()/2

# Number of successive finite difference epsilons
n_eps = 15
eps = 1e-2*np.power(2., -np.arange(n_eps))
err_grad = np.zeros(n_eps)

k = dl.Function(V)

# Compute FOM adjoint method based gradient
k_hat = dl.Function(V).vector()
k_hat.set_local(np.random.randn(V.dim()))
k_hat.apply("")
dir_grad = np.dot(grad_t, k_hat[:])
pis = []
pis.append(Pi_0)
print("ROMML directional grad: {}".format(dir_grad))

for i in range(n_eps):
    k.assign(k_pt)
    k.vector().axpy(eps[i], k_hat) #uh = uh + eps[i]*dir

    w_R = solverROM.forward_reduced(k)
    qoi_plus = solverROM.qoi_reduced(w_R)
    e_NN = model.predict([[k.vector()[:]]])[0]
    qoi_tilde_plus = qoi_plus + e_NN
    Pi_plus = np.square(qoi_tilde_plus - data).sum()/2
    pis.append(Pi_plus)

    # Error b/w finite diff approx to gradient at given eps and adj
    fd_grad = (Pi_plus - Pi_0)/eps[i]
    print("ROMML fd directional grad: {} for eps: {}".format(fd_grad, eps[i]))
    err_grad[i] = abs(fd_grad - dir_grad)

plt.loglog(eps, err_grad, "-ob", label="Error Grad")
plt.loglog(eps, (.5*err_grad[0]/eps[0])*eps, "-.k", label="First Order")
plt.title("Finite difference check of the first variation ROMML")
plt.xlabel("eps")
plt.ylabel("Error grad")
plt.legend(loc = "upper left")
plt.savefig("plots/romml_grad_check.png", dpi=200)
plt.clf()
