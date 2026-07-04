from typing import Any, Dict


def api_response(success: bool, message: str, data: Any = None) -> Dict[str, Any]:
    """Create a consistent API response envelope.

    Input:
        success: bool
        message: str
        data: any serializable payload
    Output:
        dict with keys: success, message, data
    """

    return {"success": success, "message": message, "data": data}

