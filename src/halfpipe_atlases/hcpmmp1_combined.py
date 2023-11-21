# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from .buckner2011 import from_buckner2011
from .freesurfer_subcortical import from_freesurfer_subcortical
from .hcpmmp1 import from_hcpmmp1
from .merge import AtlasMerge


def build() -> None:
    merge = AtlasMerge()
    from_hcpmmp1(merge)
    merge.lateralize()
    from_freesurfer_subcortical(merge)
    from_buckner2011(merge)

    merge.write("atlas-HCPMM1Combined_dseg")
