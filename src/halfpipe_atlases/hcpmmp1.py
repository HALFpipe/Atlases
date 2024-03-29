# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import pandas as pd
from halfpipe import resource as hr

from .merge import AtlasMerge

hcpmmp1_atlas = "HCP-MMP1_on_MNI152_ICBM2009a_nlin_hd.nii.gz"
hcpmmp1_atlas_url = "https://api.figshare.com/v2/file/download/5594360"

hcpmmp1_labels = "HCP-MMP1_on_MNI152_ICBM2009a_nlin.txt"
hcpmmp1_labels_url = "https://api.figshare.com/v2/file/download/5534027"

extra_resources = dict()
extra_resources[hcpmmp1_atlas] = hcpmmp1_atlas_url
extra_resources[hcpmmp1_labels] = hcpmmp1_labels_url

hr.online_resources.update(extra_resources)


def from_hcpmmp1(merge: AtlasMerge, prefix: str | None = "HCPMMP1") -> None:
    in_labels_file = str(hr.get(hcpmmp1_labels))

    in_labels_df = pd.read_table(
        in_labels_file,
        sep=r"\s+",
        index_col=0,
        names=["name"],
    )

    assert isinstance(in_labels_df, pd.DataFrame)
    in_labels = in_labels_df["name"]

    merge.from_file(
        prefix,
        hr.get(hcpmmp1_atlas),
        in_labels,
        space="MNI152NLin2009cAsym",  # actually it's a not c
    )


def build() -> None:
    merge = AtlasMerge()
    from_hcpmmp1(merge, prefix=None)
    merge.lateralize()
    merge.write("atlas-HCPMM1_dseg")
