import warnings
warnings.filterwarnings("ignore", category = FutureWarning)
warnings.filterwarnings("ignore", category = UserWarning)

import inspect
import numpy as np
import h5py as h5
from scipy import optimize as opt
from functools import update_wrapper


def locate_edges(trace, val_threshold = 0.0005, grd_threshold = -0.0001):
    med = np.median(trace)
    edge = (np.gradient(trace) < grd_threshold)*(trace < med - val_threshold)
    nz = np.nonzero(edge)[0]
    edgelocs = nz[np.diff(nz, prepend= 0)>1]
    return edgelocs


def locate_outliers(data, z = 1, axis = None):
    mu = np.mean(data, axis = axis)
    sig = np.std(data, axis = axis)
    indices = np.nonzero(np.abs(data - mu)>z*sig)
    return indices


class MaximumLikelihoodEstimator():


    def __init__(self, model):

        if callable(model):
            if isinstance(model, Model):
                self._m = model
            else:
                self._m = Model(model)
        
        else:
            raise TypeError("Hypothesis model must be callable.")
        
        self._data = None


    def estimate(self, **kwargs):
        
        if (self._data is None) or (not np.shape(self._data)):
            raise ValueError("No data found: please provide data with the set_data() method before attempting to estimate parameters.")
        
        if not kwargs:
            kwargs = self._m.get_param_defaults()
        
        init_fixes = self._m.get_fixed_params()
        to_release = {name:None for name in self._m.get_param_names() if name not in init_fixes}

        data_fix = {self._m.get_param_names()[0] : np.array(self._data).reshape((1, -1))}
        return_test_fix = {self._m.get_param_names()[0] : np.median(self._data)}
        self._m.fix_params(**return_test_fix)

        fixes = self._m.get_fixed_params()
        inferred_fixes = self._m.get_param_defaults()
        inferred_fixes.update(fixes)
        inferred_fixes = {key : value for key, value in inferred_fixes.items() if not key in kwargs}
        inferred_releases = {key : None for key in kwargs}
        self._m.fix_params(**inferred_fixes)
        self._m.fix_params(**inferred_releases)
        
        param_bounds = [self._m.get_param_bounds()[name] for name in self._m.get_param_names() if name in kwargs]
        init_params = [kwargs[name] for name in self._m.get_param_names() if name in kwargs]
        
        return_shape = np.shape(self._m(*init_params))
        
        self._m.fix_params(**data_fix)
        
        if return_shape:
            minimize_me = lambda args : -np.sum(np.log(self._m(*args)[0]))
        else:
            minimize_me = lambda args : -np.sum(np.log(self._m(*args)))

        result = opt.minimize(minimize_me, init_params, bounds=param_bounds, jac='3-point') ### Should release parameters if this fails
        
        if return_shape:
            cov = self._m(*result.x)[1]
            self._m.fix_params(**to_release)
            free_idxs = [self._m.get_param_names().index(key)-1 for key in kwargs]
            subcov = cov[np.ix_(free_idxs, free_idxs)]
            return result.x, subcov

        self._m.fix_params(**to_release)
        return result.x, result.hess_inv.todense()


    def set_data(self, data):
        self._data = data


class Model():


    def __init__(self, modelfunc):
        
        update_wrapper(self, modelfunc)
        self._func = modelfunc
        argspec = inspect.getfullargspec(modelfunc)
        self._args = argspec.args[:]
        self._argcount = len(self._args)
        self._defaults = list(argspec.defaults[:])
        diff = self._argcount - len(self._defaults)
        if diff:
            self._defaults = [None]*diff + self._defaults
        self._fixed_args = {}
        self._bounds = {arg:(None, None) for arg in self._args}


    def fix_params(self, **kwargs):

        self._fixed_args.update(kwargs)
        released_params = []
        for arg in self._fixed_args:
            if self._fixed_args[arg] is None:
                released_params.append(arg)
        
        for arg in released_params:
            del self._fixed_args[arg]


    def set_defaults(self, **kwargs):

        for key in kwargs:
            self._defaults[self._args.index(key)] = kwargs[key]

    
    def set_bounds(self, **kwargs):
        self._bounds.update(kwargs)


    def __call__(self, *args):

        if len(args) + len(self._fixed_args) != self._argcount:
            raise ValueError("""Unexpected number of arguments:\n
                            {0} fixed through fix_params() method and {1} provided in this call,
                            expected {2} total""".format(len(self._fixed_args), len(args), self._argcount))
        
        indices = list(range(self._argcount))
        complete_args = [np.inf]*self._argcount

        for parname in self._fixed_args:
            idx = self._args.index(parname)
            indices.remove(idx)
            complete_args[idx] = self._fixed_args[parname]

        for idx, arg in enumerate(args):
            complete_args[indices[idx]] = arg

        return self._func(*complete_args)


    def get_param_names(self):
        return self._args[:]


    def get_param_defaults(self):
        return dict(zip(self._args[:], self._defaults[:]))


    def get_fixed_params(self):
        return self._fixed_args.copy()


    def get_param_bounds(self):
        return self._bounds.copy()


@Model
def default_model(x, p = 0.5, q = 0.3, m0 = 803, m1 = 745, s0 = 15., s1 = 15, nbins = 1000):
    
    bins = np.arange(int(nbins))
    uniform = 1/nbins
    early = np.exp(-0.5*((x-m1)/s1)**2.)/np.sum(np.exp(-0.5*(((bins - m1)/s1)**2)))
    late = np.exp(-0.5*((x-m0)/s0)**2.)/np.sum(np.exp(-0.5*(((bins - m0)/s0)**2)))
    prob = np.abs(q)*uniform + np.abs(1-q)*(np.abs(p)*early + np.abs(1-p)*late)
    return prob

default_model.set_bounds(
    p = (0, 1),
    q = (0, 1),
    m0 = (0, 1000),
    m1 = (0, 1000),
    s0 = (1, 50),
    s1 = (1, 50),
    nbins = (1000,1000)
    )

default_model.fix_params(nbins = 1000)


def default_process(filename, p=0.5, q=0.5, m0=795., m1=739., s0=10., s1=20., verbose = True):
    
    mle = MaximumLikelihoodEstimator(default_model)
    
    data = h5.File(filename, 'r', swmr = True)
    scope = data['osc_0'].value
    indy_var = np.array([d[0] for d in data['analysis']])
    data.close()
    
    digitised = {v:[] for v in indy_var}
    all_hits = []
    
    if verbose:
        counttracker = np.zeros(len(scope))
        trace_dist = np.zeros(len(scope[0]))
        timebins = np.arange(len(scope[0]))
    
    for k, trace in enumerate(scope):
        edges = locate_edges(trace).tolist()
        digitised[indy_var[k]] += edges
        all_hits += edges
        if verbose:
            counttracker[k] = len(edges)
            trace_dist[edges] += 1

    mle.set_data(np.array(all_hits).reshape(1, -1))

    popt, pcov = mle.estimate(
        p = p,
        q = q,
        m0 = m0,
        m1 = m1,
        s0 = s0,
        s1 = s1
    )
    
    newfixes = {'q':popt[1],'m0':popt[2], 'm1':popt[3], 's0':popt[4], 's1':popt[5]}
    pnames = default_model.get_param_names()
    
    if verbose:
        for k, val in enumerate(popt):
            print(pnames[k+1]+":\t",val,"\t+/-\t",np.sqrt(pcov[k, k]))
        print("Based on",np.size(all_hits),"data points \n")

    default_model.fix_params(**newfixes)
    
    x = np.sort([v for v in digitised])
    p = np.zeros_like(x)
    sigma = np.zeros_like(x)
    
    for idx, point in enumerate(x):
        mle.set_data(np.array(digitised[point]))
        xpopt, xpcov = mle.estimate(p=0)
        p[idx] = xpopt[0]
        sigma[idx] = np.sqrt(xpcov[0,0])
    
    for k in range(1000):
        for idx, point in enumerate(x):
            if idx in locate_outliers(sigma)[0]:
                mle.set_data(np.array(digitised[point]))
                xpopt, xpcov = mle.estimate(p=np.random.uniform())
                p[idx] = xpopt[0]
                sigma[idx] = np.sqrt(xpcov[0,0])
                
    return x, p, sigma