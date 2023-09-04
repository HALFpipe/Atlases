# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import pandas as pd
from halfpipe import resource as hr

from .buckner2011 import from_buckner2011
from .freesurfer import from_freesurfer

name_changes_csv = "component_name_changes.csv"
name_changes_csv_url = (
    "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/master"
    "/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations"
    "/Updates/Update_20190916_component_name_changes.csv"
)

extra_resources = dict()
extra_resources[name_changes_csv] = name_changes_csv_url

hr.online_resources.update(extra_resources)


def build():
    from .merge import AtlasMerge

    merge = AtlasMerge()

    atlas_name = "Schaefer2018"
    merge.from_templateflow(atlas_name, atlas=atlas_name, desc="400Parcels17Networks")

    name_changes_frame = pd.read_csv(hr.get(name_changes_csv))
    is_resolution = name_changes_frame["Resolution"] == "400Parcels_17Networks"
    name_changes_frame = name_changes_frame.loc[is_resolution, :]
    name_mapping = {
        f"{atlas_name}_{old_name}": f"{atlas_name}_{new_name}"
        for old_name, new_name in zip(
            name_changes_frame["Old parcel name"], name_changes_frame["New parcel name"]
        )
    }
    merge.labels.replace(to_replace=name_mapping, inplace=True)

    from_freesurfer(merge)

    from_buckner2011(merge)

    merge.write("atlas-Schaefer2018Combined_dseg")
