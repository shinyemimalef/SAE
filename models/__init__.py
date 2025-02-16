from .layers import *
from .BASE import GenerativeAE, HybridAE
from .VAE import VAE, VecVAE, VAEBase
from .SAE import SAE, VecSAE, XSAE
from .ESAE import ESAE, VecESAE, EHybridAE
from .AE import ConvAE, VecAE, XAE
from .RSAE import RSAE, VecRSAE, RHybridAE, RAE, VecRAE
from .CAE import CausalAE, XCSAE, XCAE

models_switch = {"BetaVAE":VAE,
                 "BaseSAE":SAE,
                 "ESAE":ESAE,
                 "RSAE":RSAE,
                 "RAE":RAE,
                 "AE": ConvAE,
                 "XAE": XAE,
                 "XSAE": XSAE,
                 "XCAE": XCAE,
                 "XCSAE": XCSAE,
                 "VecVAE":VecVAE,
                 "VecSAE":VecSAE,
                 "VecESAE":VecESAE,
                 "VecRSAE":VecRSAE,
                 "VecRAE":VecRAE,
                 "VecAE": VecAE}
