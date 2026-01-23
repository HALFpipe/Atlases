# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from pathlib import Path
from tempfile import mkdtemp
from zipfile import ZipFile
import pandas as pd
from halfpipe import resource as hr

from .merge import AtlasMerge

buckner2011_zip = "Buckner_JNeurophysiol11_MNI152.zip"
buckner2011_zip_url = (
    "https://surfer.nmr.mgh.harvard.edu/pub/data/Buckner_JNeurophysiol11_MNI152.zip"
)
buckner2011_17networks_atlas = (
    "Buckner_JNeurophysiol11_MNI152/"
    "Buckner2011_17Networks_MNI152_FreeSurferConformed1mm_LooseMask.nii.gz"
)
buckner2011_17networks_labels = (
    "Buckner_JNeurophysiol11_MNI152/Buckner2011_17Networks_ColorLUT.txt"
)


extra_resources = dict()
extra_resources[buckner2011_zip] = buckner2011_zip_url
hr.online_resources.update(extra_resources)


def from_buckner2011(merge: AtlasMerge, prefix: str | None = "Buckner2011") -> None:
    temp = Path(mkdtemp())
    zip_file = hr.get(buckner2011_zip)

    with ZipFile(zip_file, "r") as zip_file_handle:
        zip_file_handle.extract(
            member=buckner2011_17networks_atlas,
            path=temp,
        )
        zip_file_handle.extract(
            member=buckner2011_17networks_labels,
            path=temp,
        )

    in_labels_file = str(temp / buckner2011_17networks_labels)

    in_labels_df = pd.read_table(
        in_labels_file, index_col=0, sep=r"\s+", names=["name", "r", "g", "b", "a"]
    )

    assert isinstance(in_labels_df, pd.DataFrame)
    in_labels = in_labels_df["name"]

    merge.from_file(
        prefix, temp / buckner2011_17networks_atlas, in_labels, space="MNI152NLin6Asym"
    )


def build() -> None:
    merge = AtlasMerge()

    from_buckner2011(merge, prefix=None)

    merge.write("atlas-Buckner2011_dseg")
