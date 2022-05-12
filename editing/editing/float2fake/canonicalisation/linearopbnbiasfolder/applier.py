import torch.fx as fx

from quantlib.editing.editing.editors.nnmodules import NodesMap
from quantlib.editing.editing.editors.nnmodules import NNSequentialPattern
from quantlib.editing.editing.editors.nnmodules import NNModuleApplier


class LinearOpBNBiasApplier(NNModuleApplier):

    def __init__(self, pattern: NNSequentialPattern):
        super(LinearOpBNBiasApplier, self).__init__(pattern)

    def _apply(self, g: fx.GraphModule, ap: NodesMap, id_: str) -> fx.GraphModule:
        """Absorb the bias of the linear operation into the mean of the
        following batch normalisation.

        Since we can perform this operation agnostically of instance-specific
        properties of the parameters arrays (e.g., their sizes), we can
        share the logic of this ``Applier`` amongst all the bias folding
        ``Rewriter``s.

        """

        # get handles on matched `nn.Module`s
        name_to_match_module = self.pattern.name_to_match_module(nodes_map=ap, data_gm=g)
        module_linear        = name_to_match_module['linear']
        module_bn            = name_to_match_module['bn']

        # modify matched `nn.Module`s in-place
        bias                         = module_linear.bias.data.detach().clone()
        module_linear.bias           = None
        module_bn.running_mean.data -= bias

        return g
