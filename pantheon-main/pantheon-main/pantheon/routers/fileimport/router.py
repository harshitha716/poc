from fastapi import APIRouter, Depends
from pantheon.routers.fileimport.schemas.fileimport import (
    ColumnAttributesRequest,
    ColumnAttributesResponse,
    GenerateConfigResponse,
    GenerateConfigRequest,
)
from pantheon.controllers.fileimport.fileimport_controller import FileImportController

router = APIRouter(prefix="/file-import")


def get_fileimport_controller():
    return FileImportController()


@router.post("/find-mandatory-field")
async def find_mandatory_field(
    request: ColumnAttributesRequest,
    controller: FileImportController = Depends(get_fileimport_controller),
) -> ColumnAttributesResponse:
    # Convert the list of ColumnAttribute objects to a string
    row_values = str(request.attributes)

    result = await controller.find_mandatory_field_controller(row_values)

    if result is None:
        return ColumnAttributesResponse(status="error")

    return ColumnAttributesResponse(
        status="success",
        chosen_field=result.get("chosen_field"),
        data_type=result.get("data_type"),
        explanation=result.get("explanation"),
        column_number=result.get("column_number"),
    )


@router.post("/generate-config")
async def generate_config(
    request: GenerateConfigRequest,
    controller: FileImportController = Depends(get_fileimport_controller),
) -> GenerateConfigResponse:
    result = await controller.generate_config(
        request.csv_data, request.start_row, request.template_config
    )

    if result is None:
        return GenerateConfigResponse(status="error")

    return GenerateConfigResponse(
        status="success",
        transformation_config=result["transformation_config"],
        unmapped_columns=result["unmapped_columns"],
        errors=result["errors"],
        opening_balance=result["opening_balance"],
    )
