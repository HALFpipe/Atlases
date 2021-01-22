# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from pathlib import Path
from tempfile import mkdtemp
from subprocess import call

import nibabel as nib
import pandas as pd
import numpy as np

from nilearn.image import new_img_like

tmp = Path(mkdtemp())


def from_freesurfer(merge):
    freesurfer_home = Path(os.environ["FREESURFER_HOME"])

    rb_date = "2016-05-10"
    rb_gca = freesurfer_home / "average" / f"RB_all_{rb_date}.gca"

    in_atlas_path = tmp / "labels.nii"

    assert call([
        "mri_convert",
        rb_gca,
        "-nth",
        "1",
        in_atlas_path
    ]) == 0

    in_atlas_img = nib.load(in_atlas_path)
    in_atlas = np.asanyarray(in_atlas_img.dataobj, dtype=np.int32)

    in_labels_df = pd.read_table(
        freesurfer_home / "FreeSurferColorLUT.txt",
        sep=r"\s+",
        comment="#",
        index_col=0,
        names=["name", "r", "g", "b", "a"]
    )

    assert isinstance(in_labels_df, pd.DataFrame)

    in_labels = in_labels_df.name[np.unique(in_atlas)]

    def f(x):
        x = str(x).lower()
        if "wm" in x or "chiasm" in x:
            return False
        if "cerebral" in x:
            return False
        if "cerebellum" in x:
            return False
        if "csf" in x or "ventricle" in x or "lat-vent" in x:
            return Falseopen
        if "plexus" in x or "vessel" in x:
            return False
        return True

    keep = in_labels.map(f)
    in_labels = in_labels.loc[keep]

    keep = np.in1d(in_atlas, in_labels.index).reshape(in_atlas.shape)

    filt_atlas = np.zeros_like(in_atlas)
    filt_atlas[keep] = in_atlas[keep]

    filt_atlas_path = tmp / "freesurfer-subcortical.nii"

    filt_atlas_img = new_img_like(in_atlas_img, in_atlas, copy_header=True)
    nib.save(filt_atlas_img, filt_atlas_path)

    merge.from_file(
        "FreeSurfer",
        filt_atlas_path,
        in_labels,
        space="MNI152NLin6Asym",
    )


def build():
    from .merge import AtlasMerge

    merge = AtlasMerge()

    from_freesurfer(merge)

    merge.write(f"tpl-{merge.template}_atlas-FreeSurfer_dseg")
