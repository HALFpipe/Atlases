# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import zipfile
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp

import pandas as pd
from halfpipe import resource as hr

from .merge import AtlasMerge

ukbiobank_zip = "bmri_group_means.zip"
ukbiobank_zip_url = f"https://biobank.ndph.ox.ac.uk/ukb/ukb/docs/{ukbiobank_zip}"

extra_resources = dict()
extra_resources[ukbiobank_zip] = ukbiobank_zip_url

hr.online_resources.update(extra_resources)


def from_ukbiobank(merge: AtlasMerge, prefix: str | None = "Brainnetome") -> None:
    temporary_directory = Path(mkdtemp())

    ukbiobank_zip_file = hr.get(ukbiobank_zip)

    masks: dict[str, str] = {
        "Shapes": "1",
        "Faces": "2",
        "Faces-Shapes": "5",
        "Faces-Shapes in amygdala": "5a",
    }

    with zipfile.ZipFile(ukbiobank_zip_file, "r") as zip_file_handle:
        zip_base_path = (
            zipfile.Path(root=zip_file_handle)
            / "UKBiobank_BrainImaging_GroupMeanTemplates"
        )
        for mask_name, mask_id in masks.items():
            zip_mask_path = zip_base_path / f"tfMRI_mask{mask_id}.nii.gz"
            mask_path = zip_file_handle.extract(
                zip_mask_path.at, path=temporary_directory
            )
            merge.from_file(
                in_prefix=None,
                in_atlas_path=mask_path,
                in_labels=pd.Series(data=[mask_name], index=[1], dtype=object),
                space="MNI152NLin6Asym",
            )

    rmtree(temporary_directory, ignore_errors=True)


def build() -> None:
    from .merge import AtlasMerge

    merge = AtlasMerge()

    from_ukbiobank(merge, prefix=None)

    merge.write("atlas-UKBiobankTFMRI_dseg", allow_overlaps=True)
