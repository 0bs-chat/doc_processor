from pathlib import Path
from docling.utils.model_downloader import download_models

download_models(
  output_dir=Path("./models"),
  force = False,
  progress = True,
  with_layout = True,
  with_tableformer = True,
  with_code_formula = True,
  with_picture_classifier = True,
  with_smolvlm = True,
  with_smoldocling = True,
  with_smoldocling_mlx = True,
  with_granite_vision = True,
  with_easyocr = True,
)