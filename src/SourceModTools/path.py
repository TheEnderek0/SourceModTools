from pathlib import Path
from srctools.steam import find_app, AppInfo
from .logger import getLogger

LOGGER = getLogger("Path")

def parse_path(raw_path: str, available_vars: dict[str, str|Path] = {}):

    p_path = raw_path

    if p_path.startswith("<"): # We're looking for an appid
        try:
            appid_end_idx = p_path.index(">")
        except ValueError:
            LOGGER.error(f"Path {raw_path} is invalid! Missing AppID closing bracket '>'!")
            raise RuntimeError

        appid, p_path = p_path[1:appid_end_idx], p_path[appid_end_idx+1:]
        
        try:
            appid = int(appid)
        except ValueError:
            LOGGER.error(f"Path {raw_path} has non-numerical AppID!")
            raise RuntimeError
        
        try:
            app = find_app(appid)
        except KeyError:
            LOGGER.error(f"Cannot find AppID {appid}!")
            raise RuntimeError
        
        p_path = str(app.path) + p_path

    while p_path.find("{") != -1:
        var_start = p_path.index("{")
        try:
            var_end = p_path.index("}")
        except ValueError:
            LOGGER.error(f"Path {raw_path}" + " has unclosed }!")
            raise RuntimeError
        

        var_name = p_path[var_start+1:var_end]


        if not var_name.casefold() in available_vars.keys():
            LOGGER.error(f"Unknown path variable '{var_name}' in path {raw_path}!")
            raise RuntimeError
        
        var_value = available_vars[var_name.casefold()]

        p_path = p_path.replace("{" + var_name + "}", var_value)

    p_path = Path(p_path)

    if not p_path.is_absolute():
        p_path = available_vars["wd"] / p_path

    return p_path

