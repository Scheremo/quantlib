from collections import OrderedDict
import torch.fx as fx
from typing import List

from .modulewisedescription import ModuleWiseDescription
from .modulewisedescription import NameToModule
from .applicationpoint import NodeWithPartition
from quantlib.editing.editing.editors import Finder


class ModuleWiseFinder(Finder):

    def __init__(self, modulewisedescription: ModuleWiseDescription):

        if not isinstance(modulewisedescription, ModuleWiseDescription):
            raise TypeError

        super(ModuleWiseFinder, self).__init__()
        self._modulewisedescription = modulewisedescription

    @property
    def modulewisedescription(self) -> ModuleWiseDescription:
        return self._modulewisedescription

    def find(self, g: fx.GraphModule) -> List[NodeWithPartition]:

        # initialise the ouptut data structure
        aps: List[NodeWithPartition] = []

        # prepare the data structure on which we support the search
        name_to_module = NameToModule(g.named_modules())
        name_to_node = OrderedDict([(n.target, n) for n in g.graph.nodes if n.target in name_to_module.keys()])  # to pull-back matches from `(str, nn.Module)` objects to `fx.Node`s

        # loop over partitions
        for id_, (n2mfilter, _) in self.modulewisedescription.items():
            # find the `nn.Module`s that match the partition's filter
            partition_n2m = n2mfilter(name_to_module)
            # pull-back the mapping to the `fx.Node`s and attach partition information
            partition_nwp = [NodeWithPartition(name_to_node[name], id_) for name in partition_n2m.keys()]
            # add the annotated `fx.Node`s to the list of application points
            aps.extend(partition_nwp)

        return aps

    def check_aps_commutativity(self, aps: List[NodeWithPartition]) -> bool:
        return len(aps) == len(set(ap.node for ap in aps))  # each `fx.Node` should appear at most once
