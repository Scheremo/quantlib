import numpy as np
import torch.nn as nn
import onnx

import quantlib.newediting.editing as qle


class DORYAnnotator(qle.onnxexport.ONNXAnnotator):

    def __init__(self, requant_bits: int = 32):

        backendname = 'DORY'
        super(DORYAnnotator, self).__init__(backendname)

        self._requant_bits = requant_bits

    def _annotate(self,
                  network:      nn.Module,
                  onnxproto:    onnx.ModelProto):

        def get_onnxnode_attr_by_name(node: onnx.NodeProto, name: str) -> onnx.AttributeProto:
            return next(iter([a for a in node.attribute if a.name == name]))

        # Define backend-specific supported ONNX nodes. The nodes belonging to
        # different node classes will be annotated using a class-specific logic.
        dory_onnxnode_op_types = {
            'linear': {'Conv', 'Gemm'},
            'mul':    {'Mul'},
            'add':    {'Add'},
            'clip':   {'Clip'},
        }

        for n in onnxproto.graph.node:

            op_type = n.op_type
            annotations = []

            if op_type in dory_onnxnode_op_types['linear']:
                op_name = n.input[1].rsplit('.', 1)[0]
                pytorch_module = network.get_submodule(op_name)
                if isinstance(pytorch_module, (nn.Linear, nn.Conv1d, nn.Conv2d, nn.Conv3d)):
                    weight_bits = 8   # TODO: VERIFY THAT THE MODULE IS INDEED QUANTISED, and find a way to retrieve the number of levels
                    bias_bits   = 32  # TODO: document this choice
                    annotations.append(onnx.helper.make_attribute(key='weight_bits', value=weight_bits))
                    annotations.append(onnx.helper.make_attribute(key='bias_bits',   value=bias_bits))

            elif op_type in dory_onnxnode_op_types['mul']:
                mul_bits = self._requant_bits
                annotations.append(onnx.helper.make_attribute(key='mult_bits', value=mul_bits))

            elif op_type in dory_onnxnode_op_types['add']:
                is_requant_add = all(i.isnumeric() for i in n.input)
                if is_requant_add:
                    add_bits = self._requant_bits
                else:
                    add_bits = 8  # TODO: document this choice
                annotations.append(onnx.helper.make_attribute(key='add_bits', value=add_bits))

            elif op_type in dory_onnxnode_op_types['clip']:
                clip_lo = get_onnxnode_attr_by_name(n, 'min').f
                clip_hi = get_onnxnode_attr_by_name(n, 'max').f
                assert np.log2(clip_hi + 1.0) % 1.0 < 1e-6  # TODO: document this choice
                n_levels = clip_hi - clip_lo + 1.0
                output_bits = int(np.round(np.log2(n_levels)))
                annotations.append(onnx.helper.make_attribute(key='out_bits', value=output_bits))

            else:  # the backend does not require special handling for this node type
                pass

            n.attribute.extend(annotations)

        # # partition the nodes of the ONNX graph according to the singleton partition over the ONNX node types
        # onnx_op_type_2_onnxproto_nodes = dict()
        # for n in onnxproto.graph.node:
        #     try:
        #         onnx_op_type_2_onnxproto_nodes[n.op_type].add(n)
        #     except KeyError:
        #         onnx_op_type_2_onnxproto_nodes[n.op_type] = set(n)
        #
        # # elevate the partition by grouping together singletons that are treated equally by the backend
        # dory_onnxnode_op_type_2_onnxproto_nodes = {
        #     k: set.union(*[onnx_op_type_2_onnxproto_nodes[op_type] for op_type in op_types]) for k, op_types in dory_onnxnode_op_types.items()
        # }
        #
        # # annotate the nodes in each partition
        #
        # # 1. 'linear'
        # linear_nodes = dory_onnxnode_op_type_2_onnxproto_nodes['linear']
        # for n in linear_nodes:
        #     pass
        #
        # # 2. 'mul'
        # mul_nodes = dory_onnxnode_op_type_2_onnxproto_nodes['mul']
        # for n in mul_nodes:
        #     pass
        #
        # # 3. 'add'
        # add_nodes = dory_onnxnode_op_type_2_onnxproto_nodes['add']
        # for n in add_nodes:
        #     pass
        #
        # # 4. 'clip'
        # clip_nodes = dory_onnxnode_op_type_2_onnxproto_nodes['clip']
        # for n in clip_nodes:
        #     pass
