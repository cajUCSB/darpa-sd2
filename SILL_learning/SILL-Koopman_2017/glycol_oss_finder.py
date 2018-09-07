import numpy as np
from scipy import linalg
import pickle
from scipy import optimize, integrate
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter

from mpl_toolkits.mplot3d import Axes3D


font = {'family' : 'Dejavu Sans',
        'weight' : 'bold',
        'size'   : 14}

matplotlib.rc('font', **font)


def logistic(x, center, alpha):
    """
    :param x: float, function input
    :param center: float, parameter
    :param alpha: float, parameter
    :return: 
    """
    #if center > 1e2:
        #print(center, x)
    return 1./(1 + np.exp(-alpha * (x - center)))


def mv_logistic(x, mu, alpha, l, n):  # n==len(x) must be true!
    """
    Product of logistic functions
    :param x: array, function input
    :param mu: array, function parameter
    :param alpha: float, parameter
    :param l: int, index of a matrix
    :param n: len(x)
    :return: 
    """
    return np.prod([logistic(x[j], mu[l, j], alpha) for j in range(n)])


def Lambda_T(x, mu, alpha, n, N_L):  # n==len(x) must be true!
    """
    Vector of product of logistic functions
    :param x: 
    :param mu: 
    :param alpha: 
    :param n: 
    :param N_L: 
    :return: 
    """
    return np.array([mv_logistic(x, mu, alpha, l, n) for l in range(N_L)])


def mv_log_prime(x, mu, alpha, l, n, func):
    """
    The derivative of the lth logistic product.
    :param x: 
    :param mu: 
    :param alpha: 
    :param l: 
    :param n: 
    :param func: a function from R^n to R^n
    :return: 
    """
    return mv_logistic(x, mu, alpha, l, n) * alpha * sum([(1 - logistic(x[i], mu[l, i], alpha)) * func(x)[i] for i in range(n)])


def lsq_rest_of_K(points, N_L, n, alpha, func, mu):
    """
    Calculates the bottom N_L rows of the Koopman operator assuming that the centers have already been chosen.
    Does so with a least squares method.
    :param points: 
    :param N_L: 
    :param n: 
    :param alpha: 
    :param func: 
    :param mu: a matrix 
    :param initer: 
    :return: 
    """
    len_points = len(points)
    W = np.zeros([N_L, N_L+n+1])
    A = np.array([np.hstack([np.ones(1), points[i], [mv_logistic(points[i], mu, alpha, j, n) for j in range(N_L)]]) for i in range(len_points)])
    for row in range(N_L):
        b = np.array([mv_log_prime(points[i], mu, alpha, row, n, func) for i in range(len_points)])
        W[row, :] = np.linalg.lstsq(A, b)[0]
    return W #np.hstack([np.zeros([N_L, n + 1]), W])


# Now we test the code above and try to learn then simulate the behavior of our operator.
# We use nonlinear system class to do so.

class NonlinearSystem:
    """
    Class for a non-linear system,
    Methods: 
    """
    def __init__(self, func, n, alpha, starting_vals, N_L, mu, k):
        """
        :param func: function discribing system evolution, R^n to R^n
        element's derivative.
        :param alpha: 
        :param starting_vals: array discribing the initial condition of the system.
        """
        self.n = n
        self.x0 = starting_vals
        self.f = func
        self.m = N_L
        self.alpha = alpha
        self.koop = k
        self.mu = mu
        self.ksim = None
        self.nsim = None
        self.npm = self.m + self.n


    def lift_state(self):
        """
        :return: the lifted state.
        """
        return np.hstack([1, self.x0, Lambda_T(self.x0, self.mu, self.alpha, self.n, self.m)])


    def simulate_koop(self, times):
        """
        runs a simulation for the koopman operator state
        :param times: array of times to show the state behavior at.
        :return: an array of the behavior of the system...
        """
        ex0 = self.lift_state()
        '''
        # print("Initial state: ", ex0)
        K = self.koop
        outputs = []
        for time_point in times:
            outputs.append(linalg.expm(K * time_point).dot(ex0))
        self.ksim = np.asarray(outputs)'''
        self.ksim = integrate.odeint(lambda x, t: self.koop.dot(x), ex0, times)

    def simulate_reg(self, times):
        """
        runs a simulation of the normal system to use for comparison.
        :param times: 
        :return: 
        """
        self.nsim = integrate.odeint(lambda x, t: self.f(x), self.x0, times)#, tcrit=np.array([0.5, 0.0097]))

    def plot(self, title, times, ax1, ax2, ax3, ax4, koopman=True, formula=True, indx=0, ):
        """
        Plots the most recent simulation results
        :return: 
        """
        color = [np.random.rand(), (np.random.rand()+.7)/2, np.random.rand()]
        #print("[INFO] indx, ", indx)
        if koopman and formula:
            # We plot the two simulations side by side
            ax1.plot(times, self.ksim.T[indx+1], color=color, label="x1 with the Koopman Operator")
            ax2.plot(times, self.nsim.T[indx], ms=2, color=color, label="x1 by the Dynamics Formula")
            # plt.legend()
            plt.title(title)
            ax3.plot(times, self.ksim.T[indx + 2], color=color, label="x2 with the Koopman Operator")
            ax4.plot(times, self.nsim.T[indx+1], ms=2, color=color, label="x2 by the Dynamics Formula")
            plt.ylim(-.2, 4)


n = 7
J = 2.5
A = 4
N = 1
K1 = .52
kap = 13
phi = .1
q = 4
k = 1.8
k1 = 100
k2 = 6
k3 = 16
k4 = 100
k5 = 1.28
k6 = 12

def f(y):
    """
    This the the system for the glycolic oscillator.
    :param y: array of floats, the state. 
    :return: an array of floats, the system derivative.
    """
    dy0 = J - (k1 * y[0] * y[5] / (1 + (y[5] / K1) ** q))
    dy1 = 2 * (k1 * y[0] * y[5] / (1 + (y[5] / K1) ** q)) - k2 * y[1] * (N - y[4]) - k6 * y[1] * y[4]
    dy2 = k2 * y[1] * (N - y[4]) - k3 * y[2] * (A - y[5])
    dy3 = k3 * y[2] * (A - y[5]) - k4 * y[3] * y[4] - kap * (y[3] - y[6])
    dy4 = k2 * y[1] * (N - y[4]) - k4 * y[3] * y[4] - k6 * y[1] * y[4]
    dy5 = -2 * (k1 * y[0] * y[5] / (1 + (y[5] / K1) ** q)) + 2 * k3 * y[2] * (A - y[5]) - k5 * y[5]
    dy6 = phi * kap * (y[3] - y[6]) - k * y[6]
    return np.array([dy0, dy1, dy2, dy3, dy4, dy5, dy6])

best_error = False
best_error_so_far = np.inf
# n = 2  # This is the number of centers
for mu_spacing in np.linspace(.01, 4.1, 40)[::-1]:
    for alpha in np.linspace(.7, 20.8, 40)[::-1]:
        nan_flag = False
        space = 1.8
        size = 4
        # Test this
        mu_space = mu_spacing
        mu_size = 4.1
        # alpha = .4
        # We now set the parameters for the simulation and learning problem.
        ranges = np.arange(size-size-.1, size, space)
        arrays = [ranges for i in range(n)]
        point_mesh = np.array(np.meshgrid(*arrays))
        points = [np.ndarray.flatten((point_mesh[i])) for i in range(n)]
        points = [[points[j][i] for j in range(n)] for i in range(len(ranges)**n)]

        mu_ranges = np.arange(mu_size-mu_size-.1, mu_size, mu_space)
        mu_arrays = [mu_ranges for i in range(n)]
        mu_point_mesh = np.array(np.meshgrid(*mu_arrays))
        mu_points = [np.ndarray.flatten((mu_point_mesh[i])) for i in range(n)]
        Mu = np.array([[mu_points[j][i] for j in range(n)] for i in range(len(mu_ranges)**2)])
        # We now set the parameters for the simulation and learning problem.

        N_L = len(Mu)  # This is the number of logistic functions
        x0 = np.array([1.45, .5])
        len_pts = len(points)
        basis_func = lambda x: np.hstack([np.array([1]), x, Lambda_T(x, Mu, alpha, n, N_L)]).T
        print("[INFO]: length of points: ", len(points))
        basis_func_mat = np.transpose(np.array([basis_func(x) for x in points]))
        # print("First three rows of the basis_func_mat: ", basis_func_mat[0:3, :])
        target_f = np.transpose(np.array([f(x) for x in points]))
        # print("[INFO]: target_f", target_f)
        # print("[INFO]: basis_func_mat.rank " + repr(np.linalg.matrix_rank(basis_func_mat)));
        try:
            print("[INFO] bbT.shape " +  repr(np.shape( np.dot(basis_func_mat, np.transpose(basis_func_mat)))));
            inv_basis_func_mat = np.dot(np.transpose(basis_func_mat),  np.linalg.inv( np.dot(basis_func_mat, np.transpose(basis_func_mat)) ) )
        except:
            print("[WARNING]: inverse of basis functions (evaluated over points) is ill-posed, consider rank")
            inv_basis_func_mat = np.linalg.pinv(basis_func_mat)

        K_upper_half = np.dot(target_f, inv_basis_func_mat)

        lsq_upper_err = np.linalg.norm(target_f - np.dot(K_upper_half,basis_func_mat),'fro')/(target_f.shape[0]*target_f.shape[1])

        #print("Least squares error for K: " + repr( lsq_upper_err));

        K_top = K_upper_half
        #K_top[0,:] = np.hstack([np.zeros(1), np.zeros(1), np.ones(1), np.zeros(N_L)])

        K_bot = lsq_rest_of_K(points, N_L, n, alpha, f, Mu)
        lsq_lower_error = np.linalg.norm([np.array([mv_log_prime(points[i], Mu, alpha, l, n, f) for l in range(N_L)]) - K_bot.dot(basis_func(points[i])) for i in range(len_pts)], ord=1) / float(len_pts)
        K = np.vstack([np.zeros(n+N_L+1), K_top, K_bot])

        if (lsq_upper_err + lsq_lower_error) < best_error_so_far:
            best_error_so_far = (lsq_upper_err + lsq_lower_error)
            best_error = True
            best_K = K
            best_mu = Mu
            best_alpha = alpha

        if best_error:
            example = NonlinearSystem(f, n, best_alpha, x0, N_L, best_mu, best_K)
            times = np.linspace(0, 15, 60)
            g, axis = plt.subplots(2, 2, sharey=True)
            (ax1, ax2), (ax3, ax4) = axis
            for row in np.abs(np.random.randn(7, n)):
                example.x0 = row  # Set different initial conditions
                example.simulate_koop(times)
                example.simulate_reg(times)
                if np.isnan(example.ksim).any():  # Check if Nan is in the simulation
                    nan_flag = True
                example.plot("State 1 and 2, n-step prediction, N_L={0}, alpha={1}, g-spacing={2}, g-size={3}".format(str(N_L), str(round(alpha, 2)),
                                                                                                str(space), str(size)), times, ax1, ax2, ax3, ax4, indx=0)
            if nan_flag:
                print("[WARNING]: nan detected in the koopman simulation!")
            filename = "best_x1x2_multistep_gyc"
            plt.savefig("{0}.eps".format(filename))
            plt.close()
            for row in np.abs(np.random.randn(7, n)):
                example.x0 = row  # Set different initial conditions
                example.simulate_koop(times)
                example.simulate_reg(times)
                if np.isnan(example.ksim).any():  # Check if Nan is in the simulation
                    nan_flag = True
                example.plot("State 3 and 4, n-step prediction, N_L={0}, alpha={1}, g-spacing={2}, g-size={3}".format(str(N_L), str(round(alpha, 2)),
                                                                                                str(space), str(size)), times, ax1, ax2, ax3, ax4, indx=2)
            if nan_flag:
                print("[WARNING]: nan detected in the koopman simulation!")
            filename = "best_x3x4_multistep_gyc"
            plt.savefig("{0}.eps".format(filename))
            plt.close()
            for row in np.abs(np.random.randn(7, n)):
                example.x0 = row  # Set different initial conditions
                example.simulate_koop(times)
                example.simulate_reg(times)
                if np.isnan(example.ksim).any():  # Check if Nan is in the simulation
                    nan_flag = True
                example.plot("State 5 and 6, n-step prediction, N_L={0}, alpha={1}, g-spacing={2}, g-size={3}".format(str(N_L), str(round(alpha, 2)),
                                                                                                str(space), str(size)), times, ax1, ax2, ax3, ax4, indx=4)
            if nan_flag:
                print("[WARNING]: nan detected in the koopman simulation!")
            filename = "best_x5x6_multistep_gyc"
            plt.savefig("{0}.eps".format(filename))
            plt.close()
            for row in np.abs(np.random.randn(7, n)):
                example.x0 = row  # Set different initial conditions
                example.simulate_koop(times)
                example.simulate_reg(times)
                if np.isnan(example.ksim).any():  # Check if Nan is in the simulation
                    nan_flag = True
                example.plot("State 6 and 7, n-step prediction, N_L={0}, alpha={1}, g-spacing={2}, g-size={3}".format(str(N_L), str(round(alpha, 2)),
                                                                                                str(space), str(size)), times, ax1, ax2, ax3, ax4, indx=5)
            if nan_flag:
                print("[WARNING]: nan detected in the koopman simulation!")
            filename = "best_x6x7_multistep_gyc"
            plt.savefig("{0}.eps".format(filename))
            plt.close()
            with open('best_vars.pickle','wb') as pickle_obj:
                pickle.dump([best_K, Mu, alpha], pickle_obj)

            print("alpha: ", alpha)
            print("mu_spacing, epsilon: ", mu_space)
            print("Least squares error for K, wrt f: " + repr( lsq_upper_err))
            print("Error of the derivative terms: " + repr(lsq_lower_error) + "\n")
            print("Number of data points: ", basis_func_mat.shape)
            print("There are ", len(Mu), " multivariate sigmoid functions.")
        best_error = False

print("Best Mu", best_mu.shape)
print("Best K", best_K)
print("Best alpha", best_alpha)