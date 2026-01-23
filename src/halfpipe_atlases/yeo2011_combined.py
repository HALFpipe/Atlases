# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from zipfile import ZipFile

import pandas as pd
from halfpipe import resource as hr

from .buckner2011 import from_buckner2011
from .freesurfer_subcortical import from_freesurfer_subcortical
from .merge import AtlasMerge

yeo2011_zip = "Yeo_JNeurophysiol11_MNI152.zip"
yeo2011_zip_url = f"https://surfer.nmr.mgh.harvard.edu/pub/data/{yeo2011_zip}"

extra_resources = dict()
extra_resources[yeo2011_zip] = yeo2011_zip_url

hr.online_resources.update(extra_resources)


def from_yeo2011(merge: AtlasMerge, prefix: str | None = "Yeo2011") -> None:
    temp = Path(mkdtemp())

    atlas_member = "Yeo_JNeurophysiol11_MNI152/Yeo2011_17Networks_MNI152_FreeSurferConformed1mm_LiberalMask.nii.gz"
    atlas_path = temp / atlas_member

    # read coordinates

    yeo2011_zip_file = hr.get(yeo2011_zip)
    with ZipFile(yeo2011_zip_file, "r") as zip_file_handle:
        zip_file_handle.extract(member=atlas_member, path=temp)
        with zip_file_handle.open(
            "Yeo_JNeurophysiol11_MNI152/Yeo2011_17Networks_ColorLUT.txt",
            "r",
        ) as atlas_table_file_handle:
            labels_frame = pd.read_table(
                atlas_table_file_handle,
                sep=r"\s+",
                comment="#",
                index_col=0,
                names=["name", "r", "g", "b", "a"],
            )

    labels = labels_frame.loc[1:].name

    merge.from_file(prefix, atlas_path, labels, space="MNI152NLin6Asym")

    rmtree(temp, ignore_errors=True)


def build():
    merge = AtlasMerge()

    from_yeo2011(merge)
    from_freesurfer_subcortical(merge)
    from_buckner2011(merge)

    merge.write("atlas-Yeo2011Combined_dseg")


if __name__ == "__main__":
    build()
