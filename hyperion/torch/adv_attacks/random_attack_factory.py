"""
 Copyright 2020 Johns Hopkins University  (Author: Jesus Villalba)
 Apache 2.0  (http://www.apache.org/licenses/LICENSE-2.0)
"""
import math
import torch
from .attack_factory import AttackFactory as AF

class RandomAttackFactory(object):

    def __init__(self, attack_types, 
                 min_eps=1e-5, max_eps=0.1,
                 min_snr=30, max_snr=60,
                 min_alpha=1e-5, max_alpha=0.02,
                 norms=[float('inf')], 
                 random_eps=False,
                 min_num_random_init=0, max_num_random_init=3,
                 min_confidence=0, max_confidence=1,
                 min_lr=1e-3, max_lr=1e-2,
                 min_binary_search_steps=9, max_binary_search_steps=9,
                 min_iter=5, max_iter=10,
                 abort_early=True,
                 min_c=1e-3, max_c=1e-2,
                 reduce_c=False, 
                 c_incr_factor=2,
                 tau_decr_factor=0.9,
                 indep_channels=False,
                 norm_time=False,
                 time_dim=None,
                 use_snr=False,
                 loss=None,
                 targeted=False,
                 range_min=None, range_max=None,
                 eps_scale=1):

        self.attack_types = attack_types
        self.min_eps = min_eps
        self.max_eps = max_eps
        self.min_snr = min_snr
        self.max_snr = max_snr
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        self.norms = norms
        self.random_eps = random_eps
        self.min_num_random_init = min_num_random_init 
        self.max_num_random_init = max_num_random_init 
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence
        self.min_lr = min_lr
        self.max_lr = max_lr
        self.min_binary_search_steps = min_binary_search_steps
        self.max_binary_search_steps = max_binary_search_steps
        self.abort_early = abort_early
        self.min_iter = min_iter
        self.max_iter = max_iter
        self.min_c = min_c
        self.max_c = max_c
        self.reduce_c = reduce_c
        self.c_incr_factor = c_incr_factor
        self.tau_decr_factor = tau_decr_factor
        self.indep_channels = indep_channels
        self.norm_time = norm_time
        self.time_dim = time_dim
        self.use_snr = use_snr
        self.loss = loss
        self.targeted = targeted
        self.range_min = range_min
        self.range_max = range_max
        self.eps_scale = eps_scale


    @staticmethod
    def _choice(n):
        return torch.randint(low=0, high=n, size=(1,)).item()


    @staticmethod
    def _randint(min_val, max_val):
        return torch.randint(low=min_val, high=max_val+1, size=(1,)).item()


    @staticmethod
    def _uniform(min_val, max_val):
        return (max_val - min_val) * torch.rand(size=(1,)).item() + min_val


    @staticmethod
    def _log_uniform(min_val, max_val):
        log_x = (math.log(max_val) - math.log(min_val)) * torch.rand(size=(1,)).item() + math.log(min_val)
        return math.exp(log_x)


    def _sample_attack_args(self):
        attack_args = {}
        attack_idx = self._choice(len(self.attack_types))
        attack_args['attack_type'] = self.attack_types[attack_idx]
        eps = self._log_uniform(self.min_eps, self.max_eps) 
        attack_args['eps'] = eps
        attack_args['alpha'] = self._log_uniform(
            min(eps, self.min_alpha), 
            min(eps, self.max_alpha))
        attack_args['norm'] = self.norms[self._choice(len(self.norms))]
        attack_args['random_eps'] = self.random_eps
        attack_args['num_random_init'] = self._randint(
            self.min_num_random_init, self.max_num_random_init)
        attack_args['confidence'] = self._uniform(
            self.min_confidence, self.max_confidence) 
        attack_args['lr'] = self._uniform(self.min_lr, self.max_lr) 
        attack_args['binary_search_steps'] = self._randint(
            self.min_binary_search_steps, self.max_binary_search_steps)
        attack_args['max_iter'] = self._randint(self.min_iter, self.max_iter)
        attack_args['abort_early'] = self.abort_early
        attack_args['c'] = self._uniform(self.min_c, self.max_c) 
        attack_args['reduce_c'] = self.reduce_c
        attack_args['c_incr_factor'] = self.c_incr_factor
        attack_args['tau_decr_factor'] = self.tau_decr_factor
        attack_args['indep_channels'] = self.indep_channels
        attack_args['norm_time'] = self.norm_time
        attack_args['time_dim'] = self.time_dim
        attack_args['use_snr'] = self.use_snr
        attack_args['targeted'] = self.targeted
        attack_args['range_min'] = self.range_min
        attack_args['range_max'] = self.range_max
        attack_args['eps_scale'] = self.eps_scale
        
        return attack_args


    def sample_attack(self, model=None):
        attack_args = self._sample_attack_args()
        attack_args['model'] = model
        return AF.create(**attack_args)


    @staticmethod
    def filter_args(prefix=None, **kwargs):
        if prefix is None:
            p = ''
        else:
            p = prefix + '_'

        if p + 'no_abort' in kwargs:
            kwargs[p + 'abort_early'] = not kwargs[p + 'no_abort']

        if p + 'norms' in kwargs:
            kwargs[p + 'norms'] = [float(a) for a in kwargs[p + 'norms']]

        valid_args = ('attack_types', 
                      'min_eps', 'max_eps', 
                      'min_snr', 'max_snr', 
                      'norms', 'random_eps', 
                      'min_num_random_init', 'max_num_random_init',
                      'min_alpha', 'max_alpha', 
                      'min_confidence', 'max_confidence',
                      'min_lr', 'max_lr', 
                      'min_binary_search_steps', 'max_binary_search_steps',
                      'min_iter', 'max_iter', 'abort_early',
                      'min_c', 'max_c', 'reduce_c', 
                      'c_incr_factor', 'tau_decr_factor',
                      'indep_channels', 'use_snr', 'norm_time',
                      'targeted')

        args = dict((k, kwargs[p+k])
                    for k in valid_args if p+k in kwargs)

        return args



    @staticmethod
    def add_argparse_args(parser, prefix=None):
        
        if prefix is None:
            p1 = '--'
        else:
            p1 = '--' + prefix + '-'

        parser.add_argument(
            p1+'attack-types', type=str.lower, default=['fgsm'], nargs='+',
            choices=['fgsm', 'snr-fgsm', 'rand-fgsm', 'iter-fgsm', 'cw-l0', 'cw-l2', 'cw-linf', 'pgd'], 
            help=('Attack types'))

        parser.add_argument(
            p1+'norms', type=float, default=[float('inf')], nargs='+',
            choices=[float('inf'), 1, 2],  help=('Attack perturbation norms'))

        parser.add_argument(
            p1+'min-eps', default=1e-5, type=float,
            help=('attack min epsilon, upper bound for the perturbation norm'))

        parser.add_argument(
            p1+'max-eps', default=0.1, type=float,
            help=('attack max epsilon, upper bound for the perturbation norm'))

        parser.add_argument(
            p1+'min-snr', default=30, type=float,
            help=('min upper bound for the signal-to-noise ratio of the perturbed signal'))

        parser.add_argument(
            p1+'max-snr', default=60, type=float,
            help=('max upper bound for the signal-to-noise ratio of the perturbed signal'))

        parser.add_argument(
            p1+'min-alpha', default=1e-5, type=float,
            help=('min alpha for iter and rand fgsm attack'))

        parser.add_argument(
            p1+'max-alpha', default=0.02, type=float,
            help=('max alpha for iter and rand fgsm attack'))

        parser.add_argument(
            p1+'random-eps', default=False, action='store_true',
            help=('use random epsilon in PGD attack'))

        parser.add_argument(
            p1+'min-confidence', default=0, type=float,
            help=('min confidence for carlini-wagner attack'))

        parser.add_argument(
            p1+'max-confidence', default=1, type=float,
            help=('max confidence for carlini-wagner attack'))

        parser.add_argument(
            p1+'min-lr', default=1e-3, type=float,
            help=('min learning rate for attack optimizers'))

        parser.add_argument(
            p1+'max-lr', default=1e-2, type=float,
            help=('max learning rate for attack optimizers'))

        parser.add_argument(
            p1+'min-binary-search-steps', default=9, type=int,
            help=('min num bin. search steps in carlini-wagner-l2 attack'))

        parser.add_argument(
            p1+'max-binary-search-steps', default=9, type=int,
            help=('max num bin. search steps in carlini-wagner-l2 attack'))

        parser.add_argument(
            p1+'min-iter', default=5, type=int,
            help=('min maximum. num. of optim iters in attack'))

        parser.add_argument(
            p1+'max-iter', default=10, type=int,
            help=('max maximum num. of optim iters in attack'))

        parser.add_argument(
            p1+'min-c', default=1e-3, type=float,
            help=('min initial weight of constraint function f in carlini-wagner attack'))

        parser.add_argument(
            p1+'max-c', default=1e-2, type=float,
            help=('max initial weight of constraint function f in carlini-wagner attack'))

        parser.add_argument(
            p1+'reduce-c', default=False, action='store_true',
            help=('allow to reduce c in carline-wagner-l0/inf attack'))

        parser.add_argument(
            p1+'c-incr-factor', default=2, type=float,
            help=('factor to increment c in carline-wagner-l0/inf attack'))

        parser.add_argument(
            p1+'tau-decr-factor', default=0.75, type=float,
            help=('factor to reduce tau in carline-wagner-linf attack'))

        parser.add_argument(
            p1+'indep-channels', default=False, action='store_true',
            help=('consider independent input channels in carline-wagner-l0 attack'))

        parser.add_argument(
            p1+'no-abort', default=False, action='store_true',
            help=('do not abort early in optimizer iterations'))

        parser.add_argument(
            p1+'min-num-random-init', default=1, type=int,
            help=('min number of random initializations in PGD attack'))

        parser.add_argument(
            p1+'max-num-random-init', default=5, type=int,
            help=('max number of random initializations in PGD attack'))

        parser.add_argument(
            p1+'targeted', default=False, action='store_true',
            help='use targeted attack intead of non-targeted')

        parser.add_argument(
            p1+'use-snr', default=False, action='store_true',
            help=('In carlini-wagner attack maximize SNR instead of minimize perturbation norm'))

        parser.add_argument(
            p1+'norm-time', default=False, action='store_true',
            help=('normalize norm by number of samples in time dimension'))
