# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from .buckner2011 import from_buckner2011

from .freesurfer import from_freesurfer


def build():
    from .merge import AtlasMerge

    merge = AtlasMerge()

    merge.from_templateflow(
        "Schaefer2018",
        atlas="Schaefer2018",
        desc="400Parcels17Networks"
    )

    from_freesurfer(merge)

    from_buckner2011(merge)

    merge.write("atlas-Schaefer2018Combined_dseg")
