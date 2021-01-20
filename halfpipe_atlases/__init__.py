# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from .brainnetome import build as brainnetome_build
from .brainnetome_combined import build as brainnetome_combined_build
from .buckner2011 import build as buckner2011_build
from .freesurfer import build as freesurfer_build
from .hcpmmp1 import build as hcpmmp1_build
from .hcpmmp1_combined import build as hcpmmp1_combined_build
from .power2011 import build as power2011_build
from .schaefer2011_combined import build as schaefer2011_combined_build


def build():
    build_fns = [
        value
        for key, value in globals().items()
        if key.endswith("_build")
    ]
    for build_fn in build_fns:
        build_fn()


__all__ = [
    "build",
    "brainnetome_build",
    "brainnetome_combined_build",
    "buckner2011_build",
    "freesurfer_build",
    "hcpmmp1_build",
    "hcpmmp1_combined_build",
    "power2011_build",
    "schaefer2011_combined_build",
]
