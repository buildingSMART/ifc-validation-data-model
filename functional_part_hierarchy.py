from enum import Enum

""""
Example Usage : 

-> Getting all the sub parts of a functional part including their description
# FunctionalPartHierarchy.get_hierarchy(FunctionalPartEnum.POS)['sub_parts']
# {'code': 'LOP', 'name': 'Local placement', 'sub_parts': []}
# {'code': 'LIP', 'name': 'Linear placement', 'sub_parts': []}
# {'code': 'GDP', 'name': 'Grid placement', 'sub_parts': []}
# {'code': 'GRD', 'name': 'Grid', 'sub_parts': []}
# {'code': 'ALB', 'name': 'Alignment', 'sub_parts': []}
# {'code': 'RFT', 'name': 'Referent', 'sub_parts': []}

-> Getting the parent of a sub part
# FunctionalPartHierarchy.get_parent(FunctionalPartEnum.ALS)
# {'code': 'GEM', 'name': 'Geometry representation'}
"""

class FunctionalPartEnum(Enum):
    PJS = "Project definition"
    GRF = "Georeferencing"
    BLT = "Built elements"
    ASM = "Assemblies"
    SPA = "Spaces"
    VRT = "Virtual elements"
    OJT = "Objects typing"
    STR = "Structural items and actions"
    CTR = "Constraints"
    GRP = "Groups"
    SPS = "Spatial breakdown"
    MAT = "Materials"
    PSE = "Properties for object"
    QTY = "Quantities for objects"
    CLS = "Classification reference"
    ANN = "Annotations"
    LIB = "Library reference"
    DOC = "Documentation reference"
    LAY = "Presentation layer"
    CTX = "Presentation Colours and Textures"
    POR = "Ports connectivity & nesting"
    OJP = "Object placement"
    POS = "Positioning elements"
    GEM = "Geometry representation"
    VER = "Versioning / revision control"
    CST = "Costing"
    SDL = "Scheduling of activities"
    LOP = "Local placement"
    GRD = "Grid"
    AXG = "Axis geometry"
    TAS = "Tessellated (i.e., meshes)"
    SWE = "Sweeps (i.e., extrusions, lofts, blends)"
    MPD = "Mapped geometry"
    LIP = "Linear placement"
    ALB = "Alignment"
    ALS = "Alignment geometry"
    BRP = "Boundary Representation (BREP)"
    TFM = "Transformations"
    RCO = "Relational constructs"
    GDP = "Grid placement"
    RFT = "Referent"
    PBG = "Point-based geometry"
    CSG = "Constructive Solid Geometry (CSG)"
    BBX = "Bounding box"
    CPD = "Clipped representations"


class FunctionalPartHierarchy:
    HIERARCHY = {
        FunctionalPartEnum.POS: [FunctionalPartEnum.LOP, FunctionalPartEnum.LIP, FunctionalPartEnum.GDP, FunctionalPartEnum.GRD, FunctionalPartEnum.ALB, FunctionalPartEnum.RFT],
        FunctionalPartEnum.GEM: [FunctionalPartEnum.TAS, FunctionalPartEnum.SWE, FunctionalPartEnum.MPD, FunctionalPartEnum.BRP, FunctionalPartEnum.TFM, FunctionalPartEnum.BBX, FunctionalPartEnum.RCO, FunctionalPartEnum.CPD, FunctionalPartEnum.ALS],
        FunctionalPartEnum.OJP: [FunctionalPartEnum.LOP, FunctionalPartEnum.LIP, FunctionalPartEnum.GDP]
    }

    @classmethod
    def get_hierarchy(cls, code):
        """
        Retrieves the entire hierarchy starting from the given functional part code.
        """
        if code not in FunctionalPartEnum:
            raise ValueError(f"Functional part code '{code}' does not exist.")

        def build_hierarchy(part_code):
            sub_parts = cls.HIERARCHY.get(part_code, [])
            return {
                "code": part_code.name,
                "name": part_code.value,
                "sub_parts": [build_hierarchy(child_code) for child_code in sub_parts]
            }

        return build_hierarchy(code)

    @classmethod
    def get_parent(cls, child_code):
        """
        Retrieves the parent code of the given child functional part code.
        """
        for parent_code, sub_parts in cls.HIERARCHY.items():
            if child_code in sub_parts:
                return {
                    "code": parent_code.name,
                    "name": parent_code.value
                }
        return None 