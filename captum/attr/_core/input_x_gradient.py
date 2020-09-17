#!/usr/bin/env python3
from typing import Any, Callable

from captum.log import log_usage

from ..._utils.common import _format_input, _format_output, _is_tuple
from ..._utils.gradient import apply_gradient_requirements, undo_gradient_requirements
from ..._utils.typing import TargetType, TensorOrTupleOfTensorsGeneric
from .._utils.attribution import GradientAttribution


class InputXGradient(GradientAttribution):
    r"""
    A baseline approach for computing the attribution. It multiplies input with
    the gradient with respect to input.
    https://arxiv.org/abs/1605.01713
    """

    def __init__(self, forward_func: Callable) -> None:
        r"""
        Args:

            forward_func (callable):  The forward function of the model or any
                          modification of it
        """
        GradientAttribution.__init__(self, forward_func)

    @log_usage()
    def attribute(
        self,
        inputs: TensorOrTupleOfTensorsGeneric,
        target: TargetType = None,
        additional_forward_args: Any = None,
    ) -> TensorOrTupleOfTensorsGeneric:
        r"""
        Args:

            inputs (tensor or tuple of tensors):  Input for which
                        attributions are computed. If forward_func takes a single
                        tensor as input, a single input tensor should be provided.
                        If forward_func takes multiple tensors as input, a tuple
                        of the input tensors should be provided. It is assumed
                        that for all given input tensors, dimension 0 corresponds
                        to the number of examples (aka batch size), and if
                        multiple input tensors are provided, the examples must
                        be aligned appropriately.
            target (int, tuple, tensor or list, optional):  Output indices for
                        which gradients are computed (for classification cases,
                        this is usually the target class).
                        If the network returns a scalar value per example,
                        no target index is necessary.
                        For general 2D outputs, targets can be either:

                        - a single integer or a tensor containing a single
                          integer, which is applied to all input examples

                        - a list of integers or a 1D tensor, with length matching
                          the number of examples in inputs (dim 0). Each integer
                          is applied as the target for the corresponding example.

                        For outputs with > 2 dimensions, targets can be either:

                        - A single tuple, which contains #output_dims - 1
                          elements. This target index is applied to all examples.

                        - A list of tuples with length equal to the number of
                          examples in inputs (dim 0), and each tuple containing
                          #output_dims - 1 elements. Each tuple is applied as the
                          target for the corresponding example.

                        Default: None
            additional_forward_args (any, optional): If the forward function
                        requires additional arguments other than the inputs for
                        which attributions should not be computed, this argument
                        can be provided. It must be either a single additional
                        argument of a Tensor or arbitrary (non-tuple) type or a tuple
                        containing multiple additional arguments including tensors
                        or any arbitrary python types. These arguments are provided to
                        forward_func in order following the arguments in inputs.
                        Note that attributions are not computed with respect
                        to these arguments.
                        Default: None

        Returns:
                *tensor* or tuple of *tensors* of **attributions**:
                - **attributions** (*tensor* or tuple of *tensors*):
                            The input x gradient with
                            respect to each input feature. Attributions will always be
                            the same size as the provided inputs, with each value
                            providing the attribution of the corresponding input index.
                            If a single tensor is provided as inputs, a single tensor is
                            returned. If a tuple is provided for inputs, a tuple of
                            corresponding sized tensors is returned.


        Examples::

            >>> # ImageClassifier takes a single input tensor of images Nx3x32x32,
            >>> # and returns an Nx10 tensor of class probabilities.
            >>> net = ImageClassifier()
            >>> # Generating random input with size 2x3x3x32
            >>> input = torch.randn(2, 3, 32, 32, requires_grad=True)
            >>> # Defining InputXGradient interpreter
            >>> input_x_gradient = InputXGradient(net)
            >>> # Computes inputXgradient for class 4.
            >>> attribution = input_x_gradient.attribute(input, target=4)
        """
        # Keeps track whether original input is a tuple or not before
        # converting it into a tuple.
        is_inputs_tuple = _is_tuple(inputs)

        inputs = _format_input(inputs)
        gradient_mask = apply_gradient_requirements(inputs)

        gradients = self.gradient_func(
            self.forward_func, inputs, target, additional_forward_args
        )

        attributions = tuple(
            input * gradient for input, gradient in zip(inputs, gradients)
        )

        undo_gradient_requirements(inputs, gradient_mask)
        return _format_output(is_inputs_tuple, attributions)

    @property
    def multiplies_by_inputs(self):
        return True
