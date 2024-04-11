# Export maps from puzzlemaker and also maybe something else lol, Enderek
from colorama import Fore, Style
from shutil import copy2 as CopyFile
from os import getcwd
from pathlib import Path
import json as js
import subprocess
from sys import argv
from sys import exit as exit_final

# Globals
config_path = None
moddir = None
config = None
path_dict = {} # Stores all of the path <var>s
compile_blocks = []
ASK = False

def Settings():
    global config_path

    # CONFIG
    if "-c" in argv:
        ind = argv.index("-c")
    elif "--config" in argv:
        ind = argv.index("--config")
    else:
        ind = -1
    
    if ind == -1:
        config_path = Path("./s_cfg/compilersettings.json")
    else: #We did actually find something
        try:
            config_path = argv[ind + 1]
        except IndexError:
            print_error("Config parameter was passed but no path was specified!")
        
        config_path = Path(config_path).resolve()

    global ASK
    if "-a" in argv or "--ask" in argv:
        ASK = True
    # END

def exit():
    """Pause the program and then exit"""
    input("Press any key to exit the program.")
    exit_final()

def print_info(message):
    print(Style.RESET_ALL + Fore.LIGHTBLACK_EX + f"[INFO] {message}" + Style.RESET_ALL)

def print_error(message):
    print(Style.RESET_ALL + Fore.RED + f"[ERROR] {message}" + Style.RESET_ALL)

def print_warning(message):
    print(Style.RESET_ALL + Fore.LIGHTYELLOW_EX + f"[WARNING] {message}" + Style.RESET_ALL)

def print_success(message):
    print(Style.RESET_ALL + Fore.GREEN + f"[SUCCESS] {message}" + Style.RESET_ALL)

def LoadConfig():
    global config
    if not config_path.is_file():
        return False

    with open(config_path, "r") as c_file:
        config = js.loads(c_file.read())
    return True

def GetModdir():
    try:
        modname = config["Moddir"]
    except:
        print_error("Moddir was not specified in the config file.")
        exit()
    
    global moddir, path_dict

    cwd = Path(getcwd())
    for parent in cwd.parents:
        if str(parent.stem) == modname:
            moddir = parent
            path_dict["moddir"] = parent
            return
    
    print_error("Moddir could not be located.")
    exit()
    
def ResolvePathVar(arg: str, as_path = True, custom_vars = {}):
    finished = False
    #print(f"Resolving path: {arg}")
    while(not finished):
        arg, finished = ResolvePathVar_internal(arg, custom_vars)
    #print(f"Resolved path: {arg}")
    if as_path:
        return Path(arg)
    else:
        return arg

def ResolvePathVar_internal(arg: str, custom_vars = {}):
    head = ""
    variable = ""
    cur_flag = ""
    flags = []
    processing_var = 0
    end_ind = 0


    for letter in arg:
        if letter == "<": # Variable start

            if processing_var != 0:
                print_error("< detected in a variable name or a flag name!")
                exit()

            processing_var = 1

        elif letter == ">":
            if processing_var == 1:
                processing_var = 2 # A step above, finished variable reading, now 
            else:
                print_error("> detected but no variable defined!")
                exit()

        elif letter == "{":
            if processing_var == 1 or processing_var == 0:
                print_error("{ is not allowed in a path nor a variable name!")
                exit()

            elif processing_var == 2:
                processing_var = 3
            
            elif processing_var == 3: # We are already processing a variable, wtf?
                print_error("{ is not allowed in a flag!")
                exit()

        elif letter == "}":
            if processing_var in [0, 1, 2]:
                print_error("} detected but not in a correct place, check your config!")
                exit()

            elif processing_var == 3: # stop reading current flag
                processing_var = 2 # Go step back so we can read other flags
                flags.append(cur_flag)
                cur_flag = ""

        elif processing_var == 1:
            variable += letter
        
        elif processing_var == 3:
            cur_flag += letter
        
        elif processing_var == 2: # At this moment it means we stopped processing either flags or the variable, stop 
            break
        
        else:
            head += letter
        
        end_ind += 1
    # End of loop
    if not variable:
        return arg, True
    
    try:
        var = path_dict[variable] # Read the variable
        var_is_string = type(var) == str
        var = str(var)
    except KeyError:
        try:
            var = custom_vars[variable]
            var_is_string = type(var) == str
            var = str(var)
        except KeyError:
            print_error(f"Variable {variable} does not exist!")
            exit()
    
    if not var_is_string and head: # This is a situation like "C:/something/<portal2>/somethingelse", which is forbidden
        print_error("Cannot use a path inside another path!")
        exit()

    if "posix" in flags:
        var = var.replace("\\", "/")
        var = var.replace("//", "/") #Remove duplicates if there are any

    tail = arg[end_ind:]
    final_str = head + var + tail
    return final_str, False



def RequestInstallDir(AppID:int, provider: Path):
    process = subprocess.Popen([str(provider), str(AppID)], stdout=subprocess.PIPE, universal_newlines=True)
    path_ = process.stdout.readline()
    code = process.wait()
    if code != 0:
        print_error(f"There was an error while requesting path for AppID: {AppID} | RC: {code}")
        exit()
    return Path(path_).resolve()
    

def MakePathsVDF(paths: dict):
    try:
        example_path = config["ExamplePathsVDF"]
    except:
        print_error("ExamplePathsVDF is not specified, but generating PathsVDF was requested!")
        exit()
    
    try:
        write_path = config["PathsVDFWrite"]
    except:
        print_error("PathsVDFWrite was not specified!")
        exit()
    
    write_path = ResolvePathVar(write_path)
    example_path = ResolvePathVar(example_path)
    if not example_path.is_file():
        print_error("ExamplePathsVDF is not a valid path!")
        exit()
    
    print_info(f"Writing \"{str(write_path)}\"")
    example = ""
    with open(example_path, "r") as examplef:
        example = examplef.read()
    
    cut = example.find("}")
    s_cut = example[:cut]
    
    lines = []
    for key in paths.keys():
        line = f"\"{key}\" \"{paths[key]}\"\n"
        lines.append(line)
    
    s_cut += lines.pop(0) # There will be at least one element
    for line in lines:
        s_cut += "    " + line
    
    s_cut += "    }"
    with open(write_path, "w+") as writefile:
        writefile.write(s_cut)
    
        


def SearchForPaths():
    try:
        block = config["SearchForPaths"]
    except:
        return
    
    try:
        provider = config["PathProvider"]
    except:
        print_error("SearchForPaths requested but no PathProvider is specified!")
        exit()
    
    provider = ResolvePathVar(provider)
    if not provider.is_file():
        print_error("PathProvider field is not a valid path!")
        exit()
    
    
    vdf_d = {} # Stuff to add to paths vdf later
    vdf_export = False
    global path_dict

    for mount in block:
        reference = ""
        appid = 0
        vdf = ""
        try:
            reference = mount["Reference"]
            vdf = mount["InPathsVDF"]
        except:
            pass

        try: # AppID is always required
            appid = mount["AppID"]
        except:
            print_error(f"No AppID was defined for {reference} in SearchForPaths!")
            exit()

        install_path = RequestInstallDir(appid, provider)
        if reference:
            path_dict[reference] = install_path
        if vdf:
            vdf_export = True
            vdf_d[vdf] = str(install_path)
        
    if vdf_export:
        MakePathsVDF(vdf_d)
        

        
def PromptMap():
    global path_dict
    pmap_block = {}
    map_path: Path = None
    try:
        pmap_block = config["PromptMap"]
    except: # user has not requested to prompt for a map
        map_path = AskForMap()
    
    if pmap_block:
        try:
            map_path = pmap_block["SearchIn"]
        except:
            print_error("PromptMap specified but SearchIn does not exist!")
            exit()
        
        try:
            ext = pmap_block["Filetype"]
        except:
            ext = "" #There can be files with no extension
        
        map_path = ResolvePathVar(map_path)
        print_warning(f"Searching in: {str(map_path)}")
        mapname = input("[Prompt]: Please input the map file name: ")

        if not "." in ext:
            mapname += "." + ext
        else:
            mapname += ext
        
        map_path = map_path.joinpath(mapname)

    if map_path.is_file():
        print_success("Map file found!")
        path_dict["map"] = map_path.with_suffix("") # Remove the filetype
        path_dict["mapfilename"] = map_path.stem



    
def AskForMap():
    map_ = input("[Prompt] Please specify the path for the map with file extension (you can also use the Path <vars>, such as <moddir> here): ")
    map_ = ResolvePathVar(map_)

class CompilerBlock:
    invokePath: Path = None
    name: str = ""
    workingdir: Path = None
    arguments: list = []
    ignoreReturnCode = False
    ignorelog = False

    copyfile_src: Path = None
    copyfile_dst: Path = None

    future_map_path: Path = None

    def __init__(self, block: dict):
        try:
            self.name = block["Name"]
        except:
            print_error("No name specififed in one of the compiler blocks!")
            exit()
        
        try:
            call: str = block["Call"]
            if not call.lower() == "copyfile":
                self.invokePath = call # If not, it remains as None, then the behaviour bases on that, also don't process the variables here until we actually call
        except:
            print_error(f"In compile block {self.name} no Call command has been specified!")
            exit()
        
        try:
            self.workingdir = block["CWD"]
        except:
            if self.invokePath:
                print_error(f"No CWD was specified for compile block {self.name}")
                exit()

        if self.invokePath:
            try:
                self.arguments = block["Arguments"]
            except:
                pass # Literally do nothing, arguments are not required
        else:
            try:
                self.copyfile_src = block["Source"]
                self.copyfile_dst = block["Destination"]
            except:
                print_error(f"Source or Destination parameter missing in compile block {self.name}")
                exit()

        try:
            self.future_map_path = block["ChangeMapPath"]
        except:
            pass

        try:
            self.ignoreReturnCode = block["IgnoreReturnCode"]
        except:
            pass
        
        try:
            self.ignorelog = block["IgnoreLog"]
        except:
            pass

    
    def print_process(self, message, end_ = ""):
        print(f"[{self.name}] " + message, end=end_) # No coloring
    
    def CallProcess(self):
        print_info(f"Calling: {str(self.invokePath)}")
        print_info(f"With arguments: {str(self.arguments)}")
        arglist = []
        arglist.append(str(self.invokePath))
        arglist.extend(self.arguments)
        process = subprocess.Popen(
            arglist,
            stdout=subprocess.PIPE,
            cwd=self.workingdir,
            shell=True,
            universal_newlines=True
        )
        for line in process.stdout: # We still have to iterate, because it acts like wait()
            if not self.ignorelog:
                self.print_process(line)
        
        #Automatically goes here when the process stops
        #if not self.ignoreReturnCode:
        #    if not process.returncode == 0:
        #        print_error(f"Process returned error code {process.returncode}!")
        #        exit()
        # Ignore all return codes, because every program seems to return None either way

    def CopyBehaviour(self):
        print(self.copyfile_src)
        if not self.copyfile_src.is_file():
            print_error(f"In compile block {self.name}: File \"{str(self.copyfile_src)}\" does not exist!")
            exit()
        
        print_info(f"Calling [CopyFile]")
        self.print_process(f"Source     : {str(self.copyfile_src)}", end_="\n")
        self.print_process(f"Destination: {str(self.copyfile_dst)}", end_="\n")
        self.copyfile_dst.parent.mkdir(parents=True, exist_ok=True)
        CopyFile(self.copyfile_src, self.copyfile_dst)
        print_success("Done.")
        
    def ResolveInternalPaths(self):
        c_param = {}
        if self.workingdir:
            self.workingdir = ResolvePathVar(self.workingdir) # At first resolve the workingdir
            c_param["cwd"] = self.workingdir

        if self.invokePath:
            self.invokePath = ResolvePathVar(self.invokePath, as_path=True, custom_vars=c_param)
        
        if self.arguments:
            arg_temp = []
            for argument in self.arguments:
                arg_temp.append(ResolvePathVar(argument, as_path=False, custom_vars=c_param))
            self.arguments = arg_temp

        if self.copyfile_dst:
            self.copyfile_dst = ResolvePathVar(self.copyfile_dst, custom_vars=c_param)
        
        if self.copyfile_src:
            self.copyfile_src = ResolvePathVar(self.copyfile_src, custom_vars=c_param)
        
        if self.future_map_path:
            self.future_map_path = ResolvePathVar(self.future_map_path, custom_vars=c_param)

    
    def Execute(self):
        print_warning(f"Process [{self.name}]")
        self.ResolveInternalPaths()
        if self.invokePath:
            self.CallProcess()
        else:
            self.CopyBehaviour()
        
        global path_dict
        if self.future_map_path:
            path_dict["map"] = self.future_map_path
        # We won't be checking for the path, programs should do that themselves
        

def LoadCompileBlocks():
    try:
        to_process = config["Compile"]
    except:
        print_error("No compile blocks were specified!")
        exit()
    
    global compile_blocks
    for block in to_process:
        b = CompilerBlock(block)
        compile_blocks.append(b)


def main():
    Settings()
    print_info("Welcome to MapExport program.")
    print_info(f"Config path is \"{str(config_path)}\"")
    print_info("Loading config file...")
    if not LoadConfig():
        print_error("(Specififed) config file does not exist!")
        return
    
    GetModdir()
    SearchForPaths()
    print_info("Available path <vars>:")
    for key in path_dict.keys():
        print(f"<{key}> {str(path_dict[key])}")
    
    print_info("Loading compile configs...")
    LoadCompileBlocks()
    print_info("Compile order:")
    for block in compile_blocks:
        print_info("[===] " + block.name)

    PromptMap()
    print_info(f"Starting to compile: {path_dict['map']}.<extension>")

    for process in compile_blocks:
        process.Execute()
        if ASK:
            input("Press anything to continue...")
    
    print_success("Done!")

    



main()