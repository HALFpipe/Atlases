# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from multiprocessing import cpu_count
from pathlib import Path
from shutil import copyfile

import nibabel as nib
from halfpipe.interfaces.image_maths.resample import Resample
from nilearn.image import new_img_like
import numpy as np
from templateflow.api import get as get_template

from . import __version__


def build():
    from .merge import AtlasMerge

    merge = AtlasMerge()

    for dim in [256, 1024]:
        query = dict(
            atlas="DiFuMo",
            desc=f"{dim}dimensions",
            suffix="probseg",
        )
        atlas_path = get_template(
            merge.template,
            **query,
            resolution=merge.resolution,
            extension=".nii.gz",
        )
        labels_path = get_template(
            merge.template,
            **query,
            extension=".tsv",
        )
        if not isinstance(labels_path, Path):
            raise FileNotFoundError("Could not find labels")

        interface = Resample(
            input_image=str(atlas_path),
            input_space=merge.template,
            reference_space=merge.template,
            reference_res=merge.resolution,
            float=False,
            interpolation="LanczosWindowedSinc",
            num_threads=cpu_count(),
        )
        result = interface.run()

        atlas_img = nib.load(result.outputs.output_image)
        atlas = atlas_img.get_fdata()

        out_atlas_img = new_img_like(merge.fixed_img, atlas, copy_header=True)
        out_atlas_img.header[
            "descrip"
        ] = f"Generated by HALFpipe/Atlases version {__version__}"
        out_atlas_img.header.set_data_dtype(np.float64)

        out_prefix = f"tpl-{merge.template}_atlas-DiFuMo_dim-{dim}_probseg"
        nib.save(out_atlas_img, f"{out_prefix}.nii.gz")

        copyfile(labels_path, f"{out_prefix}.tsv")

        # Clean up temporary file.
        Path(result.outputs.output_image).unlink()
