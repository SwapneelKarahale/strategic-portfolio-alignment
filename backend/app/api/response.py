from flask import jsonify


def api_response(data=None, error=None, status=200, meta=None):
    body = {"success": error is None, "data": data, "error": error}
    if meta is not None:
        body["meta"] = meta
    return jsonify(body), status


def paginated_response(query, schema_fn, page: int, per_page: int):
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    data = [schema_fn(item) for item in pagination.items]
    meta = {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    }
    return api_response(data=data, meta=meta)
