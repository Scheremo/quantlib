import copy
import torch.fx as fx

from quantlib.editing.editing.editors.optrees import OpTree
from ..qdescription import QDescription, QDescriptionSpecType, resolve_qdescriptionspec
from quantlib.editing.editing.editors import Applier
from quantlib.editing.graphs.nn import HarmonisedAdd


class AddTreeApplier(Applier):

    def __init__(self,
                 qdescriptionspec: QDescriptionSpecType,
                 use_output_scale: bool):

        qdescription = resolve_qdescriptionspec(qdescriptionspec)

        super(AddTreeApplier, self).__init__()
        self._qdescription: QDescription = qdescription
        self._use_output_scale: bool = use_output_scale

    @property
    def qdescription(self) -> QDescription:
        return self._qdescription

    @property
    def use_output_scale(self) -> bool:
        return self._use_output_scale

    def _apply(self, g: fx.GraphModule, ap: OpTree, id_: str) -> fx.GraphModule:

        # create the harmoniser
        new_target = id_
        qgranularity, qrange, qhparamsinitstrategy, (mapping, kwargs) = copy.deepcopy(self.qdescription)
        harmoniser = HarmonisedAdd(n_inputs=len(ap.inbound_frontier),
                                   qgranularityspec=qgranularity,
                                   qrangespec=qrange,
                                   qhparamsinitstrategyspec=qhparamsinitstrategy,
                                   mapping=mapping,
                                   kwargs=kwargs,
                                   use_output_scale=self.use_output_scale)

        # insert the harmoniser in its harmonisation context
        # add the harmoniser to the graph
        g.add_submodule(new_target, harmoniser)
        with g.graph.inserting_before(ap.root):
            new_node = g.graph.call_module(new_target, args=ap.inbound_frontier)
        ap.root.replace_all_uses_with(new_node)  # attach the output to the previous users of the tree's end node
        # remove dead code
        for node in ap.nodes:
            g.graph.erase_node(node)

        return g
