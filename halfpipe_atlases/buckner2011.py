# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import pandas as pd

from halfpipe import resource as hr

buckner2011_base_url = (
    "https://surfer.nmr.mgh.harvard.edu/"
    "pub/dist/freesurfer/tutorial_packages/OSX/freesurfer/average/"
    "Buckner_JNeurophysiol11_MNI152/"
)

buckner2011_17networks_atlas = (
    "Buckner2011_17Networks_MNI152_FreeSurferConformed1mm_LooseMask.nii.gz"
)
buckner2011_17networks_labels = "Buckner2011_17Networks_ColorLUT.txt"


EXTRA_RESOURCES = dict()
EXTRA_RESOURCES[buckner2011_17networks_atlas] = (
    f"{buckner2011_base_url}/{buckner2011_17networks_atlas}"
)
EXTRA_RESOURCES[buckner2011_17networks_labels] = (
    f"{buckner2011_base_url}/{buckner2011_17networks_labels}"
)
hr.ONLINE_RESOURCES.update(EXTRA_RESOURCES)


def from_buckner2011(merge):
    in_labels_file = str(hr.get(buckner2011_17networks_labels))

    in_labels_df = pd.read_table(
        in_labels_file,
        index_col=0,
        sep=r"\s+",
        names=["name", "r", "g", "b", "a"]
    )

    assert isinstance(in_labels_df, pd.DataFrame)
    in_labels = in_labels_df["name"]

    merge.from_file(
        "Buckner2011",
        hr.get(buckner2011_17networks_atlas),
        in_labels,
        space="MNI152NLin6Asym"
    )


def build():
    from .merge import AtlasMerge

    merge = AtlasMerge()

    from_buckner2011(merge)

    merge.write(f"tpl-{merge.template}_atlas-Buckner2011_dseg")
