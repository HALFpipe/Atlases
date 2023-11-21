# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from pathlib import Path
from subprocess import check_call
from tempfile import mkdtemp

import nibabel as nib

from .freesurfer import freesurfer_home, make_freesurfer_labels
from .merge import AtlasMerge

tmp = Path(mkdtemp())


def from_freesurfer_subcortical(
    merge: AtlasMerge, prefix: str | None = "FreeSurfer"
) -> None:
    rb_date = "2016-05-10"
    rb_gca = freesurfer_home / "average" / f"RB_all_{rb_date}.vc700.gca"

    atlas_path = tmp / "labels.nii"
    check_call(["mri_convert", rb_gca, "-nth", "1", atlas_path])

    def f(x):
        x = str(x).lower()
        if "wm" in x or "chiasm" in x:
            return False
        if "cerebral" in x:
            return False
        if "cerebellum" in x:
            return False
        if "csf" in x or "ventricle" in x or "lat-vent" in x:
            return False
        if "plexus" in x or "vessel" in x:
            return False
        return True

    with open(atlas_path, "rb") as file_handle:
        atlas_bytes = file_handle.read()
    atlas_image, labels = make_freesurfer_labels(atlas_bytes, filter_function=f)

    atlas_path = tmp / "freesurfer-subcortical.nii"
    nib.save(atlas_image, atlas_path)

    merge.from_file(
        prefix,
        atlas_path,
        labels,
        space="MNI152NLin6Asym",
    )


def build() -> None:
    merge = AtlasMerge()
    from_freesurfer_subcortical(merge, prefix=None)
    merge.write("atlas-FreeSurferSubcortical_dseg")
