# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd

from tempfile import mkdtemp
from shutil import rmtree

from scipy.spatial.distance import cdist
from nilearn.image import new_img_like

from templateflow import api

from halfpipe import resource as hr

"""

Power et al. (2011) write "The combination of these methods yielded 264
putative areas spanning the cerebral cortex, subcortical structures, and
the cerebellum (see Methods, Figure S1, Table S1 for analysis details and
Table S2 for coordinates). Regions of interest (ROIs) were modeled as 10 mm
diameter spheres. Graphs were formed using ROIs as nodes (N=264) and ties
terminating within 20 mm of a source node center were set to zero to avoid
possible shared signal between nearby nodes. This procedure yielded graphs of
putative functional areas in which each node represented, to the best of our
capabilities, an element of brain organization."

"""

power2011_table = "NIHMS326477-supplement-02.xls"
power2011_table_url = (
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3222858/bin/"
    + power2011_table
)

EXTRA_RESOURCES = dict()
EXTRA_RESOURCES[power2011_table] = power2011_table_url

hr.ONLINE_RESOURCES.update(EXTRA_RESOURCES)


def from_power2011(merge):
    temp = Path(mkdtemp())

    # read coordinates

    atlas_table_file = str(hr.get(power2011_table))
    atlas_df = pd.read_excel(
        atlas_table_file,
        skiprows=1,
        index_col=0
    )
    coordinates_mni = atlas_df[["X", "Y", "Z"]].to_numpy()

    r0 = 10 / 2  # mm
    r1 = 20 / 2  # mm

    template = "MNI152NLin6Asym"

    fixed_path = api.get(
        template, resolution=1, suffix="mask", desc="brain"
    )
    fixed_img = nib.load(fixed_path)
    fixed_mask = fixed_img.get_fdata() > 0

    meshgrid_fixed = tuple(map(
        np.atleast_2d,
        map(np.ravel, np.where(fixed_mask)),
    ))
    coordinates_fixed = (
        fixed_img.affine  # transform voxel coordinates to mni
        @ np.concatenate(  # each row is one axis
            [
                *meshgrid_fixed,
                np.ones([1, meshgrid_fixed[0].shape[-1]]),
            ],
            axis=0,
        )
    )[:-1, :].T

    distance = cdist(coordinates_mni, coordinates_fixed, metric="euclidean")

    spheres = distance < r0

    ties = np.sum(distance < r1, axis=0) > 1
    spheres[:, ties] = 0

    atlas_masked = np.max(
        spheres * np.arange(1, spheres.shape[0] + 1)[:, np.newaxis], axis=0
    )
    atlas = np.zeros(fixed_img.shape, dtype=np.uint16)
    atlas[meshgrid_fixed] = atlas_masked

    atlas_img = new_img_like(fixed_img, atlas)

    atlas_path = temp / f"tpl-{template}_atlas-Power2011_dseg.nii.gz"
    nib.save(atlas_img, atlas_path)

    labels = pd.Series([], dtype=object)
    for i in atlas_df.index:
        labels.loc[i] = f"{i:03d}"

    merge.from_file(
        "Power2011",
        atlas_path,
        labels,
        space="MNI152NLin6Asym"
    )

    rmtree(temp, ignore_errors=True)


def build():
    from .merge import AtlasMerge

    merge = AtlasMerge()

    from_power2011(merge)

    merge.write(f"tpl-{merge.template}_atlas-Power2011_dseg")
