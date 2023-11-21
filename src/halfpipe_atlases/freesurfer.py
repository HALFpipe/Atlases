# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from pathlib import Path
from typing import Callable

import nibabel as nib
import numpy as np
import pandas as pd
from nilearn.image import new_img_like

freesurfer_home = Path(os.environ["FREESURFER_HOME"])


def make_freesurfer_labels(
    atlas_bytes: bytes, filter_function: Callable[[str], bool] | None = None
) -> tuple[nib.nifti1.Nifti1Image, pd.Series]:
    atlas_image = nib.nifti1.Nifti1Image.from_bytes(atlas_bytes)
    atlas = np.asanyarray(atlas_image.dataobj, dtype=np.int32)

    labels_frame = pd.read_table(
        freesurfer_home / "FreeSurferColorLUT.txt",
        sep=r"\s+",
        comment="#",
        index_col=0,
        names=["name", "r", "g", "b", "a"],
    )
    if not isinstance(labels_frame, pd.DataFrame):
        raise TypeError("labels_frame must be a pandas DataFrame")
    labels = labels_frame.name[np.unique(atlas)]

    if filter_function is not None:
        keep = labels.map(filter_function)
        labels = labels.loc[keep]

    keep = np.in1d(atlas, labels.index).reshape(atlas.shape)
    atlas[~keep] = 0

    atlas_image = new_img_like(atlas_image, atlas, copy_header=True)

    return atlas_image, labels
