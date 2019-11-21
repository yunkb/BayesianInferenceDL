import sys
sys.path.append('../')

import matplotlib; matplotlib.use('macosx')
import time
import numpy as np
import matplotlib.pyplot as plt
import dolfin as dl; dl.set_log_level(40)
from utils import nb
from fom.thermal_fin import get_space

resolution = 40
V = get_space(resolution)
z_true = dl.Function(V)
z_true.vector().set_local(np.load('res_x.npy'))
nodal_vals = z_true.vector()[:]
vmax = np.max(nodal_vals)
vmin = np.min(nodal_vals)
z = dl.Function(V)
z.vector().set_local(np.load('res.npy'))
z_ROM = dl.Function(V)
z_ROM.vector().set_local(np.load('res_ROM.npy'))
z_FOM = dl.Function(V)
z_FOM.vector().set_local(np.load('res_FOM.npy'))

plt.figure(figsize=(10,10))
nb.plot(z_true,subplot_loc=221, mytitle="True conductivity", 
        show_axis='on', vmax=vmax, vmin=vmin, colorbar=False)
nb.plot(z_FOM,subplot_loc=222, mytitle="Prediction FOM", 
        show_axis='on', vmax=vmax, vmin=vmin, colorbar=False)
nb.plot(z_ROM,subplot_loc=223, mytitle="Prediction ROM",
        show_axis='on', vmax=vmax, vmin=vmin, colorbar=False)
nb.plot(z,subplot_loc=224, mytitle="Prediction ROM+DL", 
        show_axis='on', vmax=vmax, vmin=vmin, colorbar=False)
plt.savefig('z_tr_z_map.png', dpi=200)

plt.figure(figsize=(10,10))
nb.plot(z_true,subplot_loc=111, mytitle="True conductivity", 
        show_axis='on', vmax=vmax, vmin=vmin, colorbar=True)
plt.savefig('z_true_.png', dpi=200)