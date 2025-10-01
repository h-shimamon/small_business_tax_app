from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from app.services.corporate_number_service import CorporateNumberService


def create_blueprint(service: CorporateNumberService) -> Blueprint:
    """
    /api/corp
      - GET /resolve?number=XXXX
      - GET /search?name=XXXX[&pref=YY]
    """
    bp = Blueprint("corp_api", __name__, url_prefix="/api/corp")

    @bp.get("/resolve")
    def resolve() -> Any:
        number = request.args.get("number", "", type=str)
        rec = service.resolve_by_number(number)
        return jsonify({"data": rec}), (200 if rec else 404)

    @bp.get("/search")
    def search() -> Any:
        name = request.args.get("name", "", type=str)
        pref = request.args.get("pref", default=None, type=str)
        items = service.suggest_by_name(name, prefecture=pref)
        return jsonify({"items": items})

    return bp
