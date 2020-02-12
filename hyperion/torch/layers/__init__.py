"""
 Copyright 2019 Johns Hopkins University  (Author: Jesus Villalba)
 Apache 2.0  (http://www.apache.org/licenses/LICENSE-2.0)
"""
from __future__ import absolute_import

from .dropout import Dropout1d
from .global_pool import *

from .activation_factory import ActivationFactory
from .pool_factory import GlobalPool1dFactory

from .margin_losses import CosLossOutput, ArcLossOutput

from .audio_feats import *
from .audio_feats_factory import AudioFeatsFactory

from .mvn import MeanVarianceNorm
