# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from pathlib import Path

from tempfile import mkdtemp
from zipfile import ZipFile
from shutil import rmtree

import pandas as pd

from halfpipe import resource as hr

brainnetome_zip = "BN_Atlas_for_FSL.zip"
brainnetome_zip_url = (
    (
        "https://pan.cstcloud.cn/s/api/shareDownloadRequest"
        "?fid=86217173499909&password=&shareId=lsqHZSsS3g"
    ),
    "downloadUrl"
)

EXTRA_RESOURCES = dict()
EXTRA_RESOURCES[brainnetome_zip] = brainnetome_zip_url

hr.ONLINE_RESOURCES.update(EXTRA_RESOURCES)


def from_brainnetome(merge):
    temp = Path(mkdtemp())

    brainnetome_zip_file = str(hr.get(brainnetome_zip))

    with ZipFile(brainnetome_zip_file, "r") as zip_fp:
        with zip_fp.open("Brainnetome.lut", "r") as in_labels_fp:
            in_labels_df = pd.read_table(
                in_labels_fp,  # type: ignore
                index_col=0,
                sep=r"\s+",
                names=["r", "g", "b", "name"]
            )

        in_atlas_zip_path = "Brainnetome/BNA-maxprob-thr0-1mm.nii.gz"
        in_atlas_path = zip_fp.extract(in_atlas_zip_path, path=temp)

    merge.from_file(
        "Brainnetome",
        in_atlas_path,
        in_labels_df["name"],
        space="MNI152NLin6Asym"
    )

    rmtree(temp, ignore_errors=True)


def build():
    from .merge import AtlasMerge

    merge = AtlasMerge()

    from_brainnetome(merge)

    merge.write(f"tpl-{merge.template}_atlas-Brainnetome_dseg")
