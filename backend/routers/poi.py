from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

VALID_CATEGORIES = {"bike_sharing", "car_sharing", "stazioni", "taxi", "parcheggi", "patti", "luoghi_interesse"}


@router.get("/poi/{category}")
def get_poi(category: str, request: Request):
    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=404,
            detail=f"Categoria non valida. Valori ammessi: {sorted(VALID_CATEGORIES)}",
        )
    datasets = request.app.state.datasets
    return {"category": category, "items": datasets.get(category, [])}


@router.get("/poi")
def list_categories(request: Request):
    datasets = request.app.state.datasets
    return {
        "categories": {k: len(v) for k, v in datasets.items()}
    }
