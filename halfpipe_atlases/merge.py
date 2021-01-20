# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from pathlib import Path
from warnings import warn

import nibabel as nib
import numpy as np
import pandas as pd

from scipy.ndimage.measurements import center_of_mass
from scipy.spatial.distance import cdist

from nilearn.image import new_img_like

from templateflow import api

from halfpipe.io.metadata.niftimetadata import NiftiheaderMetadataLoader
from halfpipe.interface import Resample
from halfpipe.model import File
from halfpipe.utils import first

metadata_loader = NiftiheaderMetadataLoader(None)


class AtlasMerge:
    def __init__(self, template="MNI152NLin2009cAsym", resolution=2):
        self.template = template
        self.resolution = resolution

        fixed_path = api.get(
            template, resolution=resolution, suffix="T1w", desc="brain"
        )
        self.fixed_img = nib.load(fixed_path)

        self.masks = pd.Series([], dtype=object)

        self.labels = pd.Series([], dtype=object)

    def write(self, out_prefix):
        ties = np.sum(self.masks.to_list(), axis=0, dtype=np.uint16) > 1

        if np.any(ties):
            warn(
                f"Atlases to be merged have {np.sum(ties):d} ties. "
                "Resolving by closest center of mass"
            )

            centers_of_mass = np.vstack([*map(center_of_mass, self.masks)])

            for coordinate in zip(*np.nonzero(ties)):
                candidates = [*map(lambda m: m[coordinate], self.masks)]
                distance = cdist(
                    np.asarray(coordinate, dtype=np.float64)[np.newaxis, :],
                    centers_of_mass[candidates, :]
                )
                indices = self.masks.index[candidates]
                winner_index = indices[np.argmin(distance)]
                warn(
                    f"Assigning coordinate {coordinate} to "
                    f"{self.labels.loc[winner_index]:s}"
                )
                for index in indices:
                    if index == winner_index:
                        continue
                    self.masks.loc[index][coordinate] = False

        assert np.all(
            np.sum(self.masks.to_list(), axis=0, dtype=np.uint16) <= 1
        )  # double check ties

        atlas = np.sum(
            [*map(lambda t: t[0] * t[1], self.masks.items())],
            axis=0,
            dtype=np.uint16
        )

        out_atlas_img = new_img_like(self.fixed_img, atlas)
        nib.save(out_atlas_img, f"{out_prefix}.nii.gz")

        self.labels.to_csv(f"{out_prefix}.txt", sep="\t", header=False)

    def accumulate(self, in_prefix, in_labels, in_atlas):
        in_atlas = in_atlas.reshape(self.fixed_img.shape)

        for value, name in in_labels.items():
            if value == 0:
                continue  # zero is assumed to be background

            new_value = np.max(self.masks.index) + 1
            if np.isnan(new_value):  # first iteration
                new_value = 1

            self.labels.loc[new_value] = f"{in_prefix}_{name}"

            mask = np.zeros(self.fixed_img.shape, dtype=np.bool)
            mask[in_atlas == value] = True

            self.masks.loc[new_value] = mask

    def from_templateflow(self, in_prefix, **kwargs):
        in_atlas_path = api.get(
            self.template, resolution=self.resolution, **kwargs
        )
        in_atlas_img = nib.load(in_atlas_path)
        in_atlas = np.asanyarray(in_atlas_img.dataobj, dtype=np.uint16)

        in_labels_path = str(first(
            filter(
                lambda f: f.suffix == ".tsv",
                api.get(self.template, **kwargs)
            )
        ))
        in_labels_df = pd.read_table(in_labels_path, sep=r"\s+", index_col=0)

        assert isinstance(in_labels_df, pd.DataFrame)

        in_labels = in_labels_df["name"]

        self.accumulate(in_prefix, in_labels, in_atlas)

    def from_file(self, in_prefix, in_atlas_path, in_labels, space=None):
        in_atlas_path = Path(in_atlas_path)

        if space is None:
            in_atlas_file = File(
                datatype="anat",
                path=in_atlas_path,
                metadata=dict()
            )
            assert metadata_loader.fill(in_atlas_file, "space")
            space = in_atlas_file.metadata["space"]

        reference_space = self.template
        reference_res = self.resolution

        interface = Resample(
            input_image=str(in_atlas_path),
            input_space=space,
            reference_space=reference_space,
            reference_res=reference_res,
            float=True,
            interpolation="MultiLabel"
        )
        result = interface.run()

        in_atlas_img = nib.load(result.outputs.output_image)
        in_atlas = np.asanyarray(in_atlas_img.dataobj, dtype=np.uint16)

        self.accumulate(in_prefix, in_labels, in_atlas)

        Path(result.outputs.output_image).unlink()
