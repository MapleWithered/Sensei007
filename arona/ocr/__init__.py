from . import ocr_cnocr, ocr_paddleocr_json, ocr_rapidocr_json
from .. import config

match config.get_config("arona.yaml/ocr"):
    case "cnocr":
        OCR = ocr_cnocr.OCR
    case "paddleocr_json":
        OCR = ocr_paddleocr_json.OCR
    case "rapidocr_json":
        OCR = ocr_rapidocr_json.OCR
    case _:
        OCR = ocr_cnocr.OCR
