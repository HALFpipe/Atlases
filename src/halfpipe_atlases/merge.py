# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from multiprocessing import cpu_count
from pathlib import Path
from warnings import warn

import nibabel as nib
import numpy as np
import pandas as pd
from halfpipe.ingest.metadata.direction import canonicalize_direction_code
from halfpipe.ingest.metadata.niftimetadata import NiftiheaderMetadataLoader
from halfpipe.interfaces.image_maths.resample import Resample
from halfpipe.model.file.base import File
from nilearn.image import new_img_like
from numpy import typing as npt
from scipy import ndimage
from scipy.ndimage.measurements import center_of_mass
from scipy.spatial.distance import cdist
from templateflow.api import get as get_template

from . import __version__

metadata_loader = NiftiheaderMetadataLoader(None)


def mask_to_atlas(item: tuple[int, npt.NDArray[np.bool_]]) -> npt.NDArray[np.uint16]:
    index, mask = item
    return (index * mask).astype(np.uint16)


class AtlasMerge:
    def __init__(self, template: str = "MNI152NLin2009cAsym", resolution: int = 2):
        self.template = template
        self.resolution = resolution

        self.fixed_img_path: Path = get_template(
            template, resolution=resolution, suffix="T1w", desc="brain"
        )
        self.fixed_img = nib.nifti1.load(self.fixed_img_path)

        self.masks = pd.Series([], dtype=object)
        self.labels = pd.Series([], dtype=object)

    def merge_masks_without_overlap(self) -> npt.NDArray[np.uint16]:
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
                    centers_of_mass[candidates, :],
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
            list(map(mask_to_atlas, self.masks.items())),
            axis=0,
            dtype=np.uint16,
        )
        return atlas

    def merge_masks_with_overlap(self) -> npt.NDArray[np.uint16]:
        atlas = np.stack(
            list(map(mask_to_atlas, self.masks.items())),
            axis=-1,
            dtype=np.uint16,
        )
        return atlas

    def write(self, out_prefix: str, allow_overlaps: bool = False) -> None:
        atlas = {
            True: self.merge_masks_with_overlap,
            False: self.merge_masks_without_overlap,
        }[allow_overlaps]()
        out_atlas_img = new_img_like(self.fixed_img, atlas, copy_header=True)
        out_atlas_img.header[
            "descrip"
        ] = f"Generated by HALFpipe/Atlases version {__version__}"
        nib.save(out_atlas_img, f"{out_prefix}.nii.gz")

        self.labels.to_csv(f"{out_prefix}.tsv", sep="\t", header=False)

    def lateralize(self) -> None:
        lat_masks = pd.Series([], dtype=object)
        lat_labels = pd.Series([], dtype=object)

        left_to_right_code = canonicalize_direction_code("lr", self.fixed_img_path)
        assert left_to_right_code == "i", "fixed_img needs to be in RAS orientation"

        ac_point = np.linalg.inv(self.fixed_img.affine) @ np.array([0, 0, 0, 1])
        center = int(ac_point[0])

        def accumulate(mask, label):
            new_value = np.max(lat_masks.index) + 1
            if np.isnan(new_value):  # first iteration
                new_value = 1

            lat_labels.loc[new_value] = label
            lat_masks.loc[new_value] = mask

        for value in self.masks.index:
            mask = self.masks.loc[value]
            label = self.labels.loc[value]

            components, n_components = ndimage.label(mask, structure=np.ones((3, 3, 3)))

            if n_components == 1:
                accumulate(mask, label)
                continue

            left_components = components[:center, :, :]
            right_components = components[center:, :, :]

            left_component_indices = set(np.unique(left_components))
            left_component_indices.discard(0)

            right_component_indices = set(np.unique(right_components))
            right_component_indices.discard(0)

            if (
                len(left_component_indices) == 0
                or len(right_component_indices) == 0
                or not left_component_indices.isdisjoint(right_component_indices)
            ):
                accumulate(mask, label)
                continue

            accumulate(np.isin(components, list(left_component_indices)), f"{label}_L")
            accumulate(np.isin(components, list(right_component_indices)), f"{label}_R")

        self.masks = lat_masks
        self.labels = lat_labels

    def accumulate(
        self,
        in_prefix: str | None,
        in_labels: pd.Series,
        in_atlas: npt.NDArray[np.uint16],
    ) -> None:
        in_atlas = in_atlas.reshape(self.fixed_img.shape)

        for value, name in in_labels.items():
            if value == 0:
                continue  # zero is assumed to be background

            new_value = np.max(self.masks.index) + 1
            if np.isnan(new_value):  # first iteration
                new_value = 1

            label = name
            if in_prefix is not None and len(in_prefix) > 0:
                label = f"{in_prefix}_{name}"
            self.labels.loc[new_value] = label

            mask = np.zeros(self.fixed_img.shape, dtype=bool)
            mask[in_atlas == value] = True

            self.masks.loc[new_value] = mask

    def from_templateflow(self, in_prefix: str, **kwargs: str):
        in_atlas_path = get_template(
            self.template, resolution=self.resolution, **kwargs
        )
        in_atlas_img = nib.load(in_atlas_path)
        in_atlas = np.asanyarray(in_atlas_img.dataobj, dtype=np.uint16)

        in_labels_path = str(
            next(
                iter(
                    filter(
                        lambda f: f.suffix == ".tsv",
                        get_template(self.template, **kwargs),
                    )
                )
            )
        )
        in_labels_df = pd.read_table(in_labels_path, sep=r"\s+", index_col=0)

        assert isinstance(in_labels_df, pd.DataFrame)

        in_labels = in_labels_df["name"]

        self.accumulate(in_prefix, in_labels, in_atlas)

    def from_file(
        self,
        in_prefix: str | None,
        in_atlas_path: Path | str,
        in_labels: pd.Series,
        space: str | None = None,
    ) -> None:
        in_atlas_path = Path(in_atlas_path)

        if space is None:
            in_atlas_file = File(datatype="anat", path=in_atlas_path, metadata=dict())
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
            interpolation="MultiLabel",
            num_threads=cpu_count(),
        )
        result = interface.run()

        in_atlas_img = nib.load(result.outputs.output_image)
        in_atlas = np.asanyarray(in_atlas_img.dataobj, dtype=np.uint16)

        self.accumulate(in_prefix, in_labels, in_atlas)

        Path(result.outputs.output_image).unlink()
