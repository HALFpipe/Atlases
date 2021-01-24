# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from .hcpmmp1 import from_hcpmmp1

from .freesurfer import from_freesurfer

from .buckner2011 import from_buckner2011


def build():
    from .merge import AtlasMerge

    merge = AtlasMerge()

    from_hcpmmp1(merge)

    merge.lateralise()

    from_freesurfer(merge)

    from_buckner2011(merge)

    merge.lateralise()

    merge.write(f"tpl-{merge.template}_atlas-HCPMM1Combined_dseg")
