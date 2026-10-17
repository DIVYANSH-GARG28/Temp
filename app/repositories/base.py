from typing import Any, Dict, Optional
from bson import ObjectId

def doc_to_dict(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if doc is None:
        return None
    res = dict(doc)
    if "_id" in res:
        res["id"] = str(res.pop("_id"))
    return res
