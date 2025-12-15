# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from pathlib import Path
from shutil import rmtree
import tarfile
from tempfile import mkdtemp

import pandas as pd
from halfpipe import resource as hr

from .merge import AtlasMerge

aal_tar = "AAL3v2_for_SPM12.tar.gz"
aal_tar_url = f"https://www.gin.cnrs.fr/wp-content/uploads/{aal_tar}"

extra_resources = dict()
extra_resources[aal_tar] = aal_tar_url

hr.online_resources.update(extra_resources)  # type: ignore[arg-type]


def from_aal(merge: AtlasMerge, prefix: str | None = "Brainnetome") -> None:
    temporary_path = Path(mkdtemp())

    aal_tar_file = str(hr.get(aal_tar))

    with tarfile.open(aal_tar_file, "r:gz") as tar_file:
        tar_file.extractall(path=temporary_path)

    labels_data_frame = pd.read_table(
        temporary_path / "AAL3" / "AAL3v1_1mm.nii.txt",
        sep=r"\s+",
        index_col=0,
        names=["name", "number"],
        dtype=dict(name=str, number=str),
    )

    merge.from_file(
        prefix,
        temporary_path / "AAL3" / "AAL3v1_1mm.nii.gz",
        labels_data_frame["name"],
        space="MNI152NLin6Asym",
    )

    rmtree(temporary_path, ignore_errors=True)


def build() -> None:
    merge = AtlasMerge()

    from_aal(merge, prefix=None)

    merge.write("atlas-AAL_dseg")


if __name__ == "__main__":
    build()
