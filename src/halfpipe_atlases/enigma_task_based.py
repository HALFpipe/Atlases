# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import pkgutil


def build() -> None:
    # Just copy files from package_data to current directory
    atlas_name = "ENIGMATaskBasedFMRIRegionsOfInterest"
    for extension in {".nii.gz", ".tsv"}:
        file_name = f"atlas-{atlas_name}_dseg{extension}"
        with open(file_name, "wb") as file_handle:
            file_handle.write(pkgutil.get_data("halfpipe_atlases", f"data/{file_name}"))
