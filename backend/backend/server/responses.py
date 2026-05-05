from fastapi.responses import JSONResponse

def make_response(success=True, message="", data=None, status_code=200, error=None):
    res = {
        "success": success,
        "message": message,
        "status_code": status_code
    }
    if success and data is not None:
        res["data"] = data
    if not success and error:
        res["error"] = error
    return res

def success(message="Success", code=200, data=None):
    return make_response(True, message, data, code)

def fail(message="Error", code=400, error=None, data=None):
    return make_response(False, message, data, code, error)

def _service_response(result: dict):
    """Normalize service responses into JSONResponse with proper status code."""
    status_code = result.get("status_code", 200)
    # Ensure consistent envelope: if service already returns {"message":..., "data":...}, pass it through
    return JSONResponse(content=result, status_code=status_code)
