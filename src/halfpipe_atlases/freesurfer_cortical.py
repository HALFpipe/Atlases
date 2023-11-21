# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import gzip
import pkgutil
from pathlib import Path
from tempfile import mkdtemp

import nibabel as nib

from .freesurfer import make_freesurfer_labels
from .merge import AtlasMerge

tmp = Path(mkdtemp())

"""
The surface-based FreeSurfer atlases are not available in MNI space, so we
convert them to MNI space using the method proposed by Wu et al. (2018).
The method needs MATLAB installed, so we have applied it in advance using
the script `data/fsaverage/make-annot.sh` and saved the results in the
`data/fsaverage` directory.

See also
https://github.com/ThomasYeoLab/CBIG/tree/master/stable_projects/registration/Wu2017_RegistrationFusion
"""


def from_desikan_killiany(merge: AtlasMerge) -> None:
    atlas_bytes = pkgutil.get_data("halfpipe_atlases", "data/fsaverage/aparc.nii.gz")
    atlas_bytes = gzip.decompress(atlas_bytes)
    atlas_image, labels = make_freesurfer_labels(atlas_bytes)

    atlas_path = tmp / "desikan-killiany.nii"
    nib.save(atlas_image, atlas_path)

    merge.from_file(
        None,
        atlas_path,
        labels,
        space="MNI152NLin6Asym",
    )


def from_destrieux(merge: AtlasMerge) -> None:
    atlas_bytes = pkgutil.get_data(
        "halfpipe_atlases", "data/fsaverage/aparc.a2009s.nii.gz"
    )
    atlas_bytes = gzip.decompress(atlas_bytes)
    atlas_image, labels = make_freesurfer_labels(atlas_bytes)

    atlas_path = tmp / "destrieux.nii"
    nib.save(atlas_image, atlas_path)

    merge.from_file(
        None,
        atlas_path,
        labels,
        space="MNI152NLin6Asym",
    )


def build() -> None:
    merge = AtlasMerge()
    from_desikan_killiany(merge)
    merge.write("atlas-DesikanKilliany_dseg")

    merge = AtlasMerge()
    from_destrieux(merge)
    merge.write("atlas-Destrieux_dseg")
